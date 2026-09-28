"""Fetch and transform BC Ferries sailing data for the API."""

from datetime import datetime, time

import httpx

from ..models.ferries import FerryRoute, FerriesTiming

BASE_URL = "https://www.bcferriesapi.ca/v2"

def ferries_time_helper(sailing_list: list[dict[str, str]]) -> list[FerriesTiming]:
    """Convert upstream sailing-time records to response models."""
    ferries_timing_list = []
    for timing in sailing_list:
        # Find the time for both arrival and departure.
        for time_field in ("time", "arrivalTime"):
            time_text = timing[time_field]

            # Convert the time into 24-hour format.
            if time_text[-2:] == "am":
                hour = int(time_text.split(":")[0])
            else:
                hour = int(time_text.split(":")[0]) % 12 + 12
            minute = int(time_text.split(":")[1][:2])

            # Create a time object and convert it to a string.
            sailing_time = time(hour=hour, minute=minute).strftime("%H:%M")
            if time_field == "time":
                departure_time = sailing_time
            else:
                arrival_time = sailing_time

        # Compare the departure time with the server's current time.
        now = datetime.now()
        current_time = time(hour=now.hour, minute=now.minute).strftime("%H:%M")
        departed = current_time > departure_time

        # Remove the leading zero from single-digit hours.
        departure_time = departure_time[1:] if departure_time[0] == "0" else departure_time
        arrival_time = arrival_time[1:] if arrival_time[0] == "0" else arrival_time

        timing_object = FerriesTiming(
            departed=departed,
            departure_time=departure_time,
            arrival_time=arrival_time,
        )

        ferries_timing_list.append(timing_object)

    return ferries_timing_list

async def fetch_ferries() -> list[FerryRoute]:
    """Fetch ferry routes and map their sailings to response models."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/noncapacity/")
        response.raise_for_status()
        data = response.json()

        results: list[FerryRoute] = []
        for route in data["routes"]:
            parsed_route = FerryRoute(
                source=route["fromTerminalCode"],
                destination=route["toTerminalCode"],
                ferries=ferries_time_helper(route["sailings"]),
            )
            results.append(parsed_route)
    return results
