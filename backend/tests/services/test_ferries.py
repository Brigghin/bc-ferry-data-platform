'''Test files for the services/ferries file'''

from datetime import date, datetime
from zoneinfo import ZoneInfo

import httpx
import pytest
import respx

from bc_ferry_data_platform.services.ferries import (ferry_info_parse,
                                                     ferry_info_status_helper,
                                                     ferry_info_time_helper,
                                                     fetch_api_ferries,
                                                     infer_sailing_date)

BASE_URL = "https://www.bcferriesapi.ca/v2/"
BC_TIMEZONE = ZoneInfo("America/Vancouver")


def test_infer_sailing_date_rolls_future_departure_to_tomorrow():
    observed_at = datetime(2026, 11, 2, 23, 45, tzinfo=BC_TIMEZONE)

    result = infer_sailing_date("0:30", "future", observed_at)

    assert result == date(2026, 11, 3)


def test_infer_sailing_date_keeps_upcoming_departure_today():
    observed_at = datetime(2026, 11, 3, 0, 10, tzinfo=BC_TIMEZONE)

    result = infer_sailing_date("0:30", "future", observed_at)

    assert result == date(2026, 11, 3)


def test_infer_sailing_date_does_not_roll_past_departure_forward():
    observed_at = datetime(2026, 11, 3, 10, 0, tzinfo=BC_TIMEZONE)

    result = infer_sailing_date("9:00", "past", observed_at)

    assert result == date(2026, 11, 3)


def test_time_helper():
    '''Tests the ferry_info_time_helper function in services/ferries'''
    test_inputs = [{
        "time": "10:40 pm", #both Pm
        "arrivalTime": "11:30 pm"
    }, {
        "time": "10:40 am", #both am
        "arrivalTime": "11:30 am"
    },  {
        "time": "1:40 pm", #pm then am
        "arrivalTime": "1:30 am"
    },  {
        "time": "10:40 am", #am then pm
        "arrivalTime": "11:30 pm"
    }, {
        "time": "12:00 am", #noon edge cases
        "arrivalTime": "12:00 pm"
    },  {
        "time": "", #empty time
        "arrivalTime": "11:30 pm"
    }, {
        "time": "10:40 pm", #empty arrivaltime
        "arrivalTime": ""
    }, {
        "time": "", #both empty
        "arrivalTime": ""
    }, {
        "time": "test", #non valid formatting
        "arrivalTime": "11:30 pm"
    }, {
        "time": "10:40 pm", #arrivaltime non valid formatting
        "arrivalTime": "test"
    }, {
        "time": "test", #both non valid formatting
        "arrivalTime": "test"
    }, {
        "time": "am", #partial match
        "arrivalTime": "pm"
    }, {
        "time": "2 am", #partial match v2
        "arrivalTime": "1 pm"
    }]

    test_outputs = [
        ("22:40", "23:30"),
        ("10:40", "11:30"),
        ("13:40", "1:30"),
        ("10:40", "23:30"),
        ("0:00", "12:00"), 
        ("", "23:30"),
        ("22:40", ""), 
        ("", ""), 
        ("", "23:30"),
        ("22:40", ""),
        ("", ""),
        ("", ""),
        ("", ""),
    ]

    for test_input, expected_output in zip(test_inputs, test_outputs):
        departure_time, arrival_time, _ = ferry_info_time_helper(test_input)
        assert (departure_time, arrival_time) == expected_output

def test_status_helper():
    '''Tests the ferry_info_status_helper function in services/ferries'''
    test_inputs = [
    ("22:40", "23:30", "12:00"), 
    ("22:40", "11:30", "12:00"), 
    ("22:40", "",      "12:00"),
    ("",      "22:40", "12:00"),
    ("",      "",      "12:00"),
    ("10:40", "10:40", "10:40"),
    ("10:40", "10:41", "10:40"),
    ("10:40", "10:39", "10:40"),
    ]

    test_outputs = [
    "current",  # arrival > current_time
    "past",     # arrival < current_time
    "future",   # departure exists, arrival missing
    "unknown",  # departure missing, arrival exists
    "unknown",  # both missing
    "current",  # arrival == current_time
    "current",  # arrival > current_time
    "past",     # arrival < current_time
    ]

    for test_input, expected_output in zip(test_inputs, test_outputs):
        status = ferry_info_status_helper(
            test_input[0],
            test_input[1],
            test_input[2]
        )
        assert status == expected_output

def test_ferry_info_parse():
    """Tests the ferry_info_parse function in services/ferries."""

    test_inputs = [
        [
            {
                "time": "10:40 pm", #normal test pm time
                "arrivalTime": "11:30 pm",
                "vesselName": "Coastal Renaissance",
                "fill": 50,
                "carFill": 60,
                "oversizeFill": 70
            }
        ],
        [
            {
                "time": "10:40 am", #normal test am time
                "arrivalTime": "11:30 am",
                "vesselName": "Spirit of Vancouver Island",
                "fill": 25,
                "carFill": 30,
                "oversizeFill": 35
            }
        ],
        [
            {
                "time": "12:00 am", #noon edge cases
                "arrivalTime": "12:00 pm",
                "vesselName": "Coastal Celebration",
                "fill": 100,
                "carFill": 80,
                "oversizeFill": 20
            }
        ],
        [
            {
                "time": "", #only vesselname
                "arrivalTime": "",
                "vesselName": "Northern Adventure"
            }
        ],
        [
            {
                "time": "10:40 pm", #missing arrival time
                "arrivalTime": "",
                "vesselName": "Queen of Oak Bay"
            }
        ],
        [
            {
                "time": "", #missing time
                "arrivalTime": "11:30 pm",
                "vesselName": "Spirit of British Columbia"
            }
        ]
    ]

    test_outputs = [
        {
            "departureTime": "22:40",
            "arrivalTime": "23:30",
            "vessel": "Coastal Renaissance",
            "fill": 50,
            "carFill": 60,
            "oversizeFill": 70
        },
        {
            "departureTime": "10:40",
            "arrivalTime": "11:30",
            "vessel": "Spirit of Vancouver Island",
            "fill": 25,
            "carFill": 30,
            "oversizeFill": 35
        },
        {
            "departureTime": "0:00",
            "arrivalTime": "12:00",
            "vessel": "Coastal Celebration",
            "fill": 100,
            "carFill": 80,
            "oversizeFill": 20
        },
        {
            "departureTime": "",
            "arrivalTime": "",
            "vessel": "Northern Adventure",
            "fill": 0,
            "carFill": 0,
            "oversizeFill": 0
        },
        {
            "departureTime": "22:40",
            "arrivalTime": "",
            "vessel": "Queen of Oak Bay",
            "fill": 0,
            "carFill": 0,
            "oversizeFill": 0
        },
        {
            "departureTime": "",
            "arrivalTime": "23:30",
            "vessel": "Spirit of British Columbia",
            "fill": 0,
            "carFill": 0,
            "oversizeFill": 0
        }
    ]

    for input_num, sailing_list in enumerate(test_inputs):
        result = ferry_info_parse(sailing_list)

        assert len(result) == 1

        ferry = result[0]

        assert ferry.departureTime == test_outputs[input_num]["departureTime"]
        assert ferry.arrivalTime == test_outputs[input_num]["arrivalTime"]
        assert ferry.vessel == test_outputs[input_num]["vessel"]
        assert ferry.fill == test_outputs[input_num]["fill"]
        assert ferry.carFill == test_outputs[input_num]["carFill"]
        assert ferry.oversizeFill == test_outputs[input_num]["oversizeFill"]

def test_ferry_info_parse_multiple_records():
    '''Testing multiple ferry inputs for ferry_info_parse'''
    test_input = [
        {
            "time": "10:40 pm",
            "arrivalTime": "11:30 pm",
            "vesselName": "Vessel One"
        },
        {
            "time": "10:40 am",
            "arrivalTime": "11:30 am",
            "vesselName": "Vessel Two"
        }
    ]

    result = ferry_info_parse(test_input)

    assert len(result) == 2

    assert result[0].vessel == "Vessel One"
    assert result[1].vessel == "Vessel Two"

def test_ferry_info_parse_empty_list():
    '''Tests empty lists for ferry_info_parse'''
    result = ferry_info_parse([])

    assert not result

@pytest.mark.anyio
@respx.mock
async def test_fetch_ferries():
    '''Test fetch_ferries function'''
    api_response = {
        "capacityRoutes": [
            {
                "routeCode": "TSA-SWB", #normal test
                "fromTerminalCode": "TSA",
                "toTerminalCode": "SWB",
                "sailingDuration": "1h 35m",
                "sailings": []
            },
            {
                "routeCode": "HSB-NAN", #normal test
                "fromTerminalCode": "HSB",
                "toTerminalCode": "NAN",
                "sailingDuration": "1h 40m",
                "sailings": []
            },
            {
                "routeCode": "tsa-swb", #lowercase codes
                "fromTerminalCode": "tsa",
                "toTerminalCode": "swb",
                "sailingDuration": "1h 35m",
                "sailings": []
            },
            {
                "routeCode": "HSB-NAN", #missing duration
                "fromTerminalCode": "HSB",
                "toTerminalCode": "NAN",
                "sailingDuration": "",
                "sailings": []
            }
        ]
    }
    respx.get(BASE_URL).mock(
        return_value=httpx.Response(
            200,
            json=api_response
        )
    )

    result = await fetch_api_ferries()

    assert len(result) == 4

    assert result[0].routeCode == "TSASWB"
    assert result[0].source == "TSA"
    assert result[0].destination == "SWB"
    assert result[0].duration == "1h 35m"

    assert result[1].routeCode == "HSBNAN"
    assert result[1].source == "HSB"
    assert result[1].destination == "NAN"
    assert result[1].duration == "1h 40m"

    assert result[2].routeCode == "TSASWB"
    assert result[2].source == "TSA"
    assert result[2].destination == "SWB"
    assert result[2].duration == "1h 35m"

    assert result[3].routeCode == "HSBNAN"
    assert result[3].source == "HSB"
    assert result[3].destination == "NAN"
    assert result[3].duration == ""
