"""Fetch and transform BC Ferries sailing data for the API."""

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from datetime import datetime, time
from datetime import date, timedelta
import re
import httpx
from zoneinfo import ZoneInfo
from ..models.route import Route
from ..models.sailing import Sailing
from ..repositories.route import add_sailing_history
from ..repositories.route import get_or_add_route


from ..schemas.ferries import FerryRoute, FerryInfo



BASE_URL = "https://www.bcferriesapi.ca/v2/"
BC_TIMEZONE = ZoneInfo("America/Vancouver")


def normalize_route_code(route_code: str | None) -> str | None:
    if route_code is None:
        return None
    return route_code.replace("-", "").strip().upper()


def ferry_info_status_helper(departure_time: str, arrival_time: str, current_time: str) -> str:
    """Find the status info for the ferry_info object."""
    status = "unknown"
    #Compare the time objects to set sailing status
    if not arrival_time and departure_time:
        status = "future"
    elif not arrival_time and not departure_time:
        status = "unknown"
    elif arrival_time and not departure_time:
        status = "unknown"
    elif arrival_time >= current_time:
        status = "current"
    elif arrival_time < current_time:
        status = "past"


    return status

def ferry_info_time_helper(
    sailing: dict[str, str],
    observed_at: datetime | None = None,
) -> tuple[str, str, str]:
    """Parse the time info for the ferry_info object."""
    departure_time = ""
    arrival_time = ""
    #Create regex for matching the time format from the API
    time_pattern = re.compile(r"^(\d{1,2}):(\d{2})\s*(am|pm)$", re.IGNORECASE)
    for time_field in ("time", "arrivalTime"):
        time_text = sailing.get(time_field, "")
        match = time_pattern.match(time_text)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2))
            period = match.group(3).lower()

            #Convert to 24 hr time
            if period == "pm":
                hour = hour % 12 + 12
            elif hour == 12:
                hour = 0

            sailing_time = time(hour=hour, minute=minute).strftime("%H:%M")

            if time_field == "time":
                departure_time = sailing_time
            else:
                arrival_time = sailing_time

    now = observed_at or datetime.now(BC_TIMEZONE)
    if now.tzinfo is None:
        now = now.replace(tzinfo=BC_TIMEZONE)
    else:
        now = now.astimezone(BC_TIMEZONE)
    current_time = now.strftime("%H:%M")
    status = ferry_info_status_helper(departure_time, arrival_time, current_time)

    if departure_time:
        departure_time = departure_time[1:] if departure_time[0] == "0" else departure_time

    if arrival_time:
        arrival_time = arrival_time[1:] if arrival_time[0] == "0" else arrival_time

    return departure_time, arrival_time, status


def infer_sailing_date(
    departure_time: str,
    status: str,
    observed_at: datetime,
) -> date:
    """Infer the sailing day for feeds that provide a time but no date."""
    if observed_at.tzinfo is None:
        observed_at = observed_at.replace(tzinfo=BC_TIMEZONE)
    else:
        observed_at = observed_at.astimezone(BC_TIMEZONE)

    sailing_date = observed_at.date()
    if departure_time and status == "future":
        hour, minute = (int(part) for part in departure_time.split(":"))
        departure_clock = time(hour=hour, minute=minute)
        if departure_clock <= observed_at.time().replace(tzinfo=None):
            sailing_date += timedelta(days=1)
    return sailing_date


def ferry_info_parse(
    sailing_list: list[dict[str, str]],
    observed_at: datetime | None = None,
) -> list[FerryInfo]:
    """Convert upstream sailing-time records to response models."""
    observed_at = observed_at or datetime.now(BC_TIMEZONE)
    ferry_info_list = []
    for ferry_info in sailing_list:
        departure_time, arrival_time, status = ferry_info_time_helper(
            ferry_info,
            observed_at,
        )
        sailing_date = infer_sailing_date(departure_time, status, observed_at)

        vessel = ferry_info["vesselName"]
        fill = ferry_info.get("fill", 0)
        car_fill = ferry_info.get("carFill", 0)
        oversize_fill =  ferry_info.get("oversizeFill", 0)

        info_object = FerryInfo(
            departureTime = departure_time,
            arrivalTime = arrival_time,
            status = status,
            vessel = vessel,
            fill =  fill,
            carFill = car_fill,
            oversizeFill = oversize_fill,
            sailingDate=sailing_date,
        )

        ferry_info_list.append(info_object)

    return ferry_info_list

async def fetch_api_ferries(route_code: str | None) -> list[FerryRoute]:
    """Fetch ferry routes and map their sailings to response models."""
    requested_route_code = normalize_route_code(route_code)
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}")
        response.raise_for_status()
        data = response.json()

        results: list[FerryRoute] = []
        for route in data["capacityRoutes"]:
            normalized_route_code = normalize_route_code(route["routeCode"])
            parsed_route = FerryRoute(
                routeCode=normalized_route_code,
                source=route["fromTerminalCode"].upper(),
                destination=route["toTerminalCode"].upper(),
                duration=route["sailingDuration"],
                ferries=ferry_info_parse(route["sailings"])
            )
            if parsed_route.routeCode == requested_route_code or requested_route_code is None:
                results.append(parsed_route)
    return results

async def upload_ferries(session: Session, route_code: str | None = None) -> int:
    """Upload ferries to the database"""
    api_routes = await fetch_api_ferries(route_code)

    for api_route in api_routes:
        route = Route(
            routeCode=api_route.routeCode,
            source=api_route.source,
            destination=api_route.destination,
            duration=api_route.duration,
        )
        stored_route = get_or_add_route(session, route)
        sailing_snapshot = [
            Sailing(
                departureTime=ferry.departureTime,
                arrivalTime=ferry.arrivalTime,
                status=ferry.status,
                vessel=ferry.vessel,
                fill=ferry.fill,
                carFill=ferry.carFill,
                oversizeFill=ferry.oversizeFill,
                sailingDate=ferry.sailingDate,
            )
            for ferry in api_route.ferries
        ]
        add_sailing_history(session, stored_route.routeCode, sailing_snapshot)

    try:
        session.commit()
    except Exception:
        session.rollback()
        raise
    return len(api_routes)

def fetch_storage_ferries(session: Session, route_code: str | None) -> list[FerryRoute]:
    """Fetch ferry routes + sailings from the database"""
    statement = select(Route).options(selectinload(Route.ferries))
    if route_code is not None:
        statement = statement.where(
            Route.routeCode == normalize_route_code(route_code)
        )

    routes = session.scalars(statement).all()
    return [FerryRoute.model_validate(route) for route in routes]