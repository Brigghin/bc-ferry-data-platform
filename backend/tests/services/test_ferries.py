"""Tests for capacity-feed parsing, fetch, and storage."""

from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import httpx
import pytest
import respx
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from bc_ferry_data_platform.models.base import Base
from bc_ferry_data_platform.models.route import Route as RouteModel
from bc_ferry_data_platform.models.sailing import Sailing as SailingModel
from bc_ferry_data_platform.services.ferries import (
    BASE_URL,
    fetch_api_ferries,
    fetch_storage_ferries,
    parse_bc_time,
    parse_utc,
    sailing_parse,
    upload_ferries,
)
from bc_ferry_data_platform.schemas.ferries import Route as RouteSchema
from bc_ferry_data_platform.schemas.ferries import Sailing as SailingSchema

BC_TIMEZONE = ZoneInfo("America/Vancouver")


def test_parse_bc_time_combines_service_date_and_local_time() -> None:
    """Interpret a clock time in the BC timezone on its service date."""
    result = parse_bc_time("2026-11-10", "8:30 am")

    assert result == datetime(2026, 11, 10, 8, 30, tzinfo=BC_TIMEZONE)


def test_parse_bc_time_returns_none_for_missing_time() -> None:
    """Preserve missing upstream clock times as null."""
    assert parse_bc_time(date(2026, 11, 10), None) is None


def test_parse_utc_trims_nanoseconds_and_parses_zulu_timestamp() -> None:
    """Parse upstream UTC timestamps with more precision than Python supports."""
    result = parse_utc("2026-11-10T16:30:45.123456789Z")

    assert result == datetime(
        2026, 11, 10, 16, 30, 45, 123456, tzinfo=timezone.utc
    )


def test_sailing_parse_uses_arrival_date_and_shared_capture_time() -> None:
    """Use arrival date for post-midnight arrivals and retain capture metadata."""
    captured_at = datetime(2026, 11, 10, 16, tzinfo=timezone.utc)
    parsed = sailing_parse(
        [
            {
                "serviceDate": "2026-11-10",
                "arrivalDate": "2026-11-11",
                "scheduledTime": "11:30 pm",
                "actualDepartureTime": "11:40 pm",
                "actualArrivalTime": "1:00 am",
                "capacityKnown": True,
                "carCapacityKnown": True,
                "oversizeCapacityKnown": False,
                "fill": 50,
                "carFill": 60,
                "oversizeFill": 0,
                "vesselName": "Test vessel",
                "status": "departed",
                "observedAt": "2026-11-10T23:45:00.123456789Z",
            }
        ],
        captured_at,
    )

    assert len(parsed) == 1
    assert parsed[0].scheduledTime == datetime(
        2026, 11, 10, 23, 30, tzinfo=BC_TIMEZONE
    )
    assert parsed[0].actualArrivalTime == datetime(
        2026, 11, 11, 1, 0, tzinfo=BC_TIMEZONE
    )
    assert parsed[0].observedAt == datetime(
        2026, 11, 10, 23, 45, 0, 123456, tzinfo=timezone.utc
    )
    assert parsed[0].APICapturedAt == captured_at


@pytest.mark.parametrize("scheduled_time", [None, "", "   "])
def test_sailing_parse_rejects_missing_scheduled_time(scheduled_time) -> None:
    """Reject records which do not have a usable unique key."""
    with pytest.raises(ValueError):
        sailing_parse([{
            "serviceDate": "2026-11-10",
            "scheduledTime": scheduled_time,
        }])


@pytest.mark.anyio
@respx.mock
async def test_fetch_api_ferries_maps_capacity_feed() -> None:
    """Map the upstream capacity feed into normalized route schemas."""
    respx.get(BASE_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "capacityRoutes": [
                    {
                        "routeCode": "TSA-SWB",
                        "fromTerminalCode": "tsa",
                        "toTerminalCode": "swb",
                        "sailingDuration": "1h 35m",
                        "sailings": [
                            {
                                "serviceDate": "2026-11-10",
                                "scheduledTime": "8:30 am",
                                "capacityKnown": True,
                                "carCapacityKnown": True,
                                "oversizeCapacityKnown": True,
                                "fill": 50,
                                "carFill": 60,
                                "oversizeFill": 70,
                                "vesselName": "Test vessel",
                                "status": "scheduled",
                            }
                        ],
                    }
                ]
            },
        )
    )

    routes = await fetch_api_ferries()

    assert len(routes) == 1
    assert routes[0].routeCode == "TSASWB"
    assert routes[0].fromTerminalCode == "TSA"
    assert routes[0].toTerminalCode == "SWB"
    assert routes[0].sailings[0].fill == 50


@pytest.mark.anyio
async def test_upload_and_fetch_round_trip(monkeypatch) -> None:
    """Store fetched route and sailing data and return it through the read path."""
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    service_date = datetime.now(BC_TIMEZONE).date() + timedelta(days=1)
    captured_at = datetime.now(timezone.utc)
    sailing = SailingSchema(
        serviceDate=service_date,
        scheduledTime=datetime.combine(
            service_date, datetime.min.time(), tzinfo=BC_TIMEZONE
        ),
        capacityKnown=True,
        carCapacityKnown=True,
        oversizeCapacityKnown=False,
        fill=45,
        carFill=50,
        oversizeFill=0,
        vesselName="Test vessel",
        status="scheduled",
        APICapturedAt=captured_at,
    )
    route = RouteSchema(
        routeCode="TSASWB",
        fromTerminalCode="TSA",
        toTerminalCode="SWB",
        sailingDuration="1h 35m",
        sailings=[sailing],
    )

    async def fetch_routes():
        return [route]

    monkeypatch.setattr(
        "bc_ferry_data_platform.services.ferries.fetch_api_ferries",
        fetch_routes,
    )

    try:
        with Session(engine) as session:
            assert await upload_ferries(session) == 1
            sailing.actualDepartureTime = sailing.scheduledTime
            sailing.fill = 65
            assert sailing.scheduledTime is not None
            extra_sailing = sailing.model_copy(
                update={"scheduledTime": sailing.scheduledTime + timedelta(hours=1)}
            )
            route.sailings.append(extra_sailing)
            assert await upload_ferries(session) == 1
            session.expire_all()
            stored_routes = fetch_storage_ferries(session, "TSA-SWB")

            assert len(stored_routes) == 1
            assert stored_routes[0].sailings[0].vesselName == "Test vessel"
            assert stored_routes[0].sailings[0].fill == 65
            assert stored_routes[0].sailings[0].actualDepartureTime is not None
            assert session.query(RouteModel).count() == 1
            assert session.query(SailingModel).count() == 2
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.mark.anyio
async def test_upload_rolls_back_if_sailing_key_is_missing(monkeypatch) -> None:
    """Do not leave partial route data after a persistence error."""
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    route = RouteSchema(
        routeCode="TSASWB",
        fromTerminalCode="TSA",
        toTerminalCode="SWB",
        sailingDuration="1h 35m",
        sailings=[
            SailingSchema(
                serviceDate=date(2026, 11, 10),
                scheduledTime=None,
                capacityKnown=False,
                carCapacityKnown=False,
                oversizeCapacityKnown=False,
                fill=0,
                carFill=0,
                oversizeFill=0,
                vesselName="Test vessel",
                status="scheduled",
            )
        ],
    )

    async def fetch_routes():
        return [route]

    monkeypatch.setattr(
        "bc_ferry_data_platform.services.ferries.fetch_api_ferries", fetch_routes
    )

    try:
        with Session(engine) as session:
            with pytest.raises(ValueError, match="has no scheduled time"):
                await upload_ferries(session)
            assert session.query(RouteModel).count() == 0
            assert session.query(SailingModel).count() == 0
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()
