from datetime import time, datetime

import httpx
from fastapi import APIRouter, HTTPException

from ..models.ferries import ferries_timing, ferry_route

BASE_URL = "https://www.bcferriesapi.ca/v2"

'''
This function helps to make the ferries_timing model for the 
ferry_route model

:param sailing_list: Sailing_list is the dictionary of ferry sailing time
from the BCferriesapo

:return: This function returns a list of ferries_timing objects
'''
def ferries_time_helper(sailing_list: dict) -> list[ferries_timing]:
    ferries_timing_list = []
    for timing in sailing_list:
        #Find the time for both arrival and departure
        for i in range(2):
            if i == 0:
                arrival_departure = "time"
            else:
                arrival_departure = "arrivalTime"

            #Convert the time into 24hr
            if timing[arrival_departure][-2:] == "am":
                hour = int(timing[arrival_departure].split(":")[0])
            else:
                hour = int(timing[arrival_departure].split(":")[0])%12 + 12
            minute = int(timing[arrival_departure].split(":")[1][:2])

            #Create a time object and convert it to a string
            t = time(hour=hour, minute=minute)
            time_str = t.strftime("%H:%M")
            if i == 0:
               departure_time = time_str
            else:
                arrival_time = time_str

        #Get the current time and compare it to the departure time to update the status of the ferry
        now = datetime.now()
        current_time = time(hour=int(now.hour), minute=int(now.minute))
        current_time = current_time.strftime("%H:%M")
        if current_time > departure_time:
            departed = True
        else:
            departed = False

        #Remove the leading zero if the time hour is somthing like "05"
        departure_time = departure_time[1:] if departure_time[0] == "0" else departure_time 
        arrival_time = arrival_time[1:] if arrival_time[0] == "0" else arrival_time

        timing_object = ferries_timing(
            departed = departed,
            departure_time = departure_time,
            arrival_time = arrival_time
        )

        ferries_timing_list.append(timing_object)

    return ferries_timing_list

'''
Parse and fetch the list of ferries using from the BCFerries API keeping only needed data

:return: A list of ferry_route models that define all routes and their accompanying sailings
'''
async def fetch_ferries() -> list[ferry_route]:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/noncapacity/")
        response.raise_for_status()
        data = response.json()

        results = []
        for route in data["routes"]:
            parsed_route = ferry_route(
                source = route["fromTerminalCode"],
                destination= route["toTerminalCode"],
                ferries= ferries_time_helper(route["sailings"])
            )
            results.append(parsed_route)
    return results