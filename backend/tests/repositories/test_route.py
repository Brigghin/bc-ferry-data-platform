"""Tests for ferry route and sailing persistence."""

# Pytest fixtures are injected by parameter name.
# pylint: disable=redefined-outer-name

from datetime import date, datetime, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from bc_ferry_data_platform.models.base import Base
from bc_ferry_data_platform.models.route import Route
from bc_ferry_data_platform.models.sailing import Sailing
from bc_ferry_data_platform.repositories.route import (
    add_sailing_history,
    get_by_code,
    get_or_add_route,
)


@pytest.fixture
def db_session():
    """Provide an isolated in-memory database session."""
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    with Session(engine) as database_session:
        yield database_session

    Base.metadata.drop_all(engine)
    engine.dispose()


def make_route() -> Route:
    """Build a test route."""
    return Route(
        routeCode="TSA-SWB",
        fromTerminalCode="TSA",
        toTerminalCode="SWB",
        sailingDuration="1h 35m",
    )


def make_sailing(**overrides) -> Sailing:
    """Build a test sailing with overridable fields."""
    values = {
        "serviceDate": date(2026, 11, 10),
        "scheduledTime": datetime(2026, 11, 10, 8, 30, tzinfo=timezone.utc),
        "actualDepartureTime": None,
        "actualArrivalTime": None,
        "capacityKnown": True,
        "carCapacityKnown": True,
        "oversizeCapacityKnown": False,
        "fill": 25,
        "carFill": 30,
        "oversizeFill": 0,
        "vesselName": "Test vessel",
        "status": "scheduled",
        "observedAt": None,
        "APICapturedAt": datetime(2026, 11, 10, 8, tzinfo=timezone.utc),
    }
    values.update(overrides)
    return Sailing(**values)


def test_add_and_get_route_with_sailings(db_session: Session) -> None:
    """Persist a route with its sailing and retrieve the relationship."""
    route = make_route()
    get_or_add_route(db_session, route)
    route_code = route.routeCode
    sailing = make_sailing(routeCode=route_code)
    add_sailing_history(db_session, route_code, [sailing])
    db_session.commit()
    db_session.expunge_all()

    stored_route = get_by_code(db_session, "TSA-SWB")

    assert stored_route is not None
    assert stored_route.routeCode == "TSASWB"
    assert stored_route.fromTerminalCode == "TSA"
    assert len(stored_route.sailings) == 1
    assert stored_route.sailings[0].vesselName == "Test vessel"


def test_get_by_code_returns_none_when_route_is_missing(db_session: Session) -> None:
    """Return no result for a route code not in storage."""
    assert get_by_code(db_session, "MISSING") is None


def test_refresh_updates_existing_sailing_without_adding_duplicate(
    db_session: Session,
) -> None:
    """Update an existing row on refresh instead of duplicating the sailing."""
    route = make_route()
    stored_route = get_or_add_route(db_session, route)
    route_code = stored_route.routeCode
    add_sailing_history(
        db_session, route_code, [make_sailing(routeCode=route_code)]
    )
    db_session.commit()

    updated = make_sailing(
        routeCode=route_code,
        status="departed",
        fill=0,
        carFill=0,
        vesselName="Updated vessel",
        APICapturedAt=datetime(2026, 11, 10, 8, 30, tzinfo=timezone.utc),
    )
    add_sailing_history(db_session, route_code, [updated])
    db_session.commit()

    sailings = db_session.scalars(select(Sailing)).all()
    assert len(sailings) == 1
    assert sailings[0].status == "departed"
    assert sailings[0].fill == 0
    assert sailings[0].carFill == 0
    assert sailings[0].vesselName == "Updated vessel"


def test_refresh_preserves_known_actual_times_and_unknown_fill(
    db_session: Session,
) -> None:
    """Keep known values when an updated feed reports them as unavailable."""
    route_code = get_or_add_route(db_session, make_route()).routeCode
    departure = datetime(2026, 11, 10, 8, 35, tzinfo=timezone.utc)
    arrival = datetime(2026, 11, 10, 10, 10, tzinfo=timezone.utc)
    original = make_sailing(
        routeCode=route_code,
        actualDepartureTime=departure,
        actualArrivalTime=arrival,
        oversizeCapacityKnown=True,
        oversizeFill=40,
    )
    add_sailing_history(db_session, route_code, [original])
    db_session.commit()

    updated = make_sailing(
        routeCode=route_code,
        capacityKnown=False,
        carCapacityKnown=True,
        oversizeCapacityKnown=False,
        fill=0,
        carFill=0,
        oversizeFill=0,
    )
    add_sailing_history(db_session, route_code, [updated])
    db_session.commit()

    stored = db_session.scalar(select(Sailing))
    assert stored is not None
    assert stored.actualDepartureTime is not None
    assert stored.actualArrivalTime is not None
    assert stored.actualDepartureTime.replace(tzinfo=timezone.utc) == departure
    assert stored.actualArrivalTime.replace(tzinfo=timezone.utc) == arrival
    assert stored.fill == 25
    assert stored.carFill == 0
    assert stored.oversizeFill == 40
    assert not stored.capacityKnown
    assert stored.carCapacityKnown
    assert not stored.oversizeCapacityKnown


def test_reject_sailing_without_a_scheduled_time(db_session: Session) -> None:
    """Do not persist a sailing without the full identifying key."""
    route_code = get_or_add_route(db_session, make_route()).routeCode
    with pytest.raises(ValueError, match="has no scheduled time"):
        add_sailing_history(
            db_session, route_code, [make_sailing(scheduledTime=None)]
        )


def test_get_or_add_route_normalizes_code_and_updates_route_details(
    db_session: Session,
) -> None:
    """Normalize route codes and refresh metadata for an existing route."""
    first_route = get_or_add_route(db_session, make_route())
    db_session.commit()

    updated_route = Route(
        routeCode="TSA-SWB",
        fromTerminalCode="TSA",
        toTerminalCode="SWB",
        sailingDuration="1h 40m",
    )
    result = get_or_add_route(db_session, updated_route)

    assert result.id == first_route.id
    assert result.routeCode == "TSASWB"
    assert result.sailingDuration == "1h 40m"
