"""Fetch and transform BC Ferries sailing data for the API."""

from datetime import datetime, time
import re
import httpx


from ..schemas.ferries import FerryRoute, FerryInfo

BASE_URL = "https://www.bcferriesapi.ca/v2/"

def ferry_info_status_helper(departure_time: time, arrival_time: time, current_time: time) -> str:
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

def ferry_info_time_helper(sailing: dict[str, str]) -> tuple[str, str, str]:
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

    now = datetime.now()
    current_time = time(hour=now.hour, minute=now.minute).strftime("%H:%M")
    status = ferry_info_status_helper(departure_time, arrival_time, current_time)

    if departure_time:
        departure_time = departure_time[1:] if departure_time[0] == "0" else departure_time

    if arrival_time:
        arrival_time = arrival_time[1:] if arrival_time[0] == "0" else arrival_time

    return departure_time, arrival_time, status

def ferry_info_parse(sailing_list: list[dict[str, str]]) -> list[FerryInfo]:
    """Convert upstream sailing-time records to response models."""
    ferry_info_list = []
    for ferry_info in sailing_list:
        departure_time, arrival_time, status = ferry_info_time_helper(ferry_info)

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
            oversizeFill = oversize_fill
        )

        ferry_info_list.append(info_object)

    return ferry_info_list

async def fetch_ferries(route_code: str | None) -> list[FerryRoute]:
    """Fetch ferry routes and map their sailings to response models."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}")
        response.raise_for_status()
        data = response.json()

        results: list[FerryRoute] = []
        for route in data["capacityRoutes"]:
            parsed_route = FerryRoute(
                routeCode=route["routeCode"].upper(),
                source=route["fromTerminalCode"].upper(),
                destination=route["toTerminalCode"].upper(),
                duration=route["sailingDuration"],
                ferries=ferry_info_parse(route["sailings"])
            )
            if parsed_route.routeCode == route_code or route_code is None:
                results.append(parsed_route)
    return results
