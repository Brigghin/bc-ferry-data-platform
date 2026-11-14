"""Fetch and transform BC Ferries sailing data for the API."""

import re
from datetime import date, datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..models.route import Route as RouteModel
from ..models.sailing import Sailing as SailingModel
from ..repositories.route import add_sailing_history, get_or_add_route
from ..schemas.ferries import Route as RouteSchema
from ..schemas.ferries import Sailing as SailingSchema

BASE_URL = "https://www.bcferriesapi.ca/v2/"
BC_TIMEZONE = ZoneInfo("America/Vancouver")

def parse_utc(value: str | None) -> datetime | None:
    """Parse an RFC 3339 timestamp (with nanoseconds and 'Z') into an aware UTC datetime."""
    if not value:
        return None
    # Trim fractional seconds to 6 digits and turn 'Z' into '+00:00'
    value = re.sub(r"(\.\d{6})\d+", r"\1", value).replace("Z", "+00:00")
    return datetime.fromisoformat(value).astimezone(timezone.utc)

def parse_bc_time(service_date: str | date, value: str | None) -> datetime | None:
    """Combine a service date and a BC local time like '5:45 pm' into an aware datetime."""
    if not value:
        return None
    if isinstance(service_date, str):
        service_date = date.fromisoformat(service_date)
    t = datetime.strptime(value.strip().upper(), "%I:%M %p").time()
    return datetime.combine(service_date, t, tzinfo=BC_TIMEZONE)

def sailing_parse(
    sailing_list: list[dict[str, Any]],  # List of sailing-time records from the API
    captured_at: datetime | None = None,
) -> list[SailingSchema]:
    """Convert upstream sailing-time records to response models."""
    captured_at = captured_at or datetime.now(timezone.utc)  # one value for the whole fetch
    parsed: list[SailingSchema] = []
    for sailing in sailing_list:
        service_date = sailing["serviceDate"]
        scheduled_time = parse_bc_time(service_date, sailing.get("scheduledTime"))
        if scheduled_time is None:
            raise ValueError(f"Sailing on {service_date} has no scheduled time")
        arrival_date = sailing.get("arrivalDate") or service_date
        parsed.append(
            SailingSchema(
                serviceDate=date.fromisoformat(service_date),
                scheduledTime=scheduled_time,
                actualDepartureTime=parse_bc_time(service_date, sailing.get("actualDepartureTime")),
                actualArrivalTime=parse_bc_time(arrival_date, sailing.get("actualArrivalTime")),
                capacityKnown=bool(sailing["capacityKnown"]),
                carCapacityKnown=bool(sailing["carCapacityKnown"]),
                oversizeCapacityKnown=bool(sailing["oversizeCapacityKnown"]),
                fill=int(sailing.get("fill", 0)),
                carFill=int(sailing.get("carFill", 0)),
                oversizeFill=int(sailing.get("oversizeFill", 0)),
                vesselName=sailing.get("vesselName", ""),
                status=sailing.get("status", "unknown"),
                observedAt=parse_utc(sailing.get("observedAt")),
                APICapturedAt=captured_at,
            )
        )
    return parsed

async def fetch_api_ferries() -> list[RouteSchema]:
    """Fetch ferry routes and map their sailings to response models."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}")
        response.raise_for_status()
        data = response.json()

        # List of FerryRoute Objects each with their own list of FerryInfo Objects
        results: list[RouteSchema] = []
        captured_at = datetime.now(timezone.utc)
        for ferry_route in data["capacityRoutes"]: #Iterating through the routes + sailings from API
            parsed_route = RouteSchema(
                routeCode=ferry_route["routeCode"].replace("-", "").strip().upper(),
                fromTerminalCode=ferry_route["fromTerminalCode"].upper(),
                toTerminalCode=ferry_route["toTerminalCode"].upper(),
                sailingDuration=ferry_route["sailingDuration"],
                sailings=sailing_parse(
                    ferry_route["sailings"], captured_at
                ) #Formatted list of sailings for each route
            )
            results.append(parsed_route) #Adding complete route + sailings to the list of results
    return results

async def upload_ferries(session: Session) -> int:
    """Upload ferries to the database"""
    api_routes = await fetch_api_ferries()

    try:
        for api_route in api_routes:
            route = RouteModel(
                routeCode=api_route.routeCode,
                fromTerminalCode=api_route.fromTerminalCode,
                toTerminalCode=api_route.toTerminalCode,
                sailingDuration=api_route.sailingDuration,
            )
            stored_route = get_or_add_route(session, route)
            sailing_snapshot = []
            for sailing in api_route.sailings:
                sailing_snapshot.append(
                    SailingModel(
                        routeCode=stored_route.routeCode,
                        serviceDate=sailing.serviceDate,
                        scheduledTime=sailing.scheduledTime,
                        actualDepartureTime=sailing.actualDepartureTime,
                        actualArrivalTime=sailing.actualArrivalTime,
                        capacityKnown=sailing.capacityKnown,
                        carCapacityKnown=sailing.carCapacityKnown,
                        oversizeCapacityKnown=sailing.oversizeCapacityKnown,
                        fill=sailing.fill,
                        carFill=sailing.carFill,
                        oversizeFill=sailing.oversizeFill,
                        vesselName=sailing.vesselName,
                        status=sailing.status,
                        observedAt=sailing.observedAt,
                        APICapturedAt=sailing.APICapturedAt,
                    )
                )
            add_sailing_history(session, stored_route.routeCode, sailing_snapshot)
        session.commit()
    except Exception:
        session.rollback()
        raise
    return len(api_routes)

def fetch_storage_ferries(
    session: Session, route_code: str | None = None
) -> list[RouteSchema]:
    """Fetch ferry routes and upcoming sailings from the database."""
    today = datetime.now(BC_TIMEZONE).date()
    statement = select(RouteModel).options(
        selectinload(
            RouteModel.sailings.and_(SailingModel.serviceDate >= today)
        )
    )
    if route_code is not None:
        normalized_route_code = route_code.replace("-", "").strip().upper()
        statement = statement.where(RouteModel.routeCode == normalized_route_code)

    routes = session.scalars(statement).all()
    return [RouteSchema.model_validate(route) for route in routes]
