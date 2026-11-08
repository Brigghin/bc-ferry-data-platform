from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from bc_ferry_data_platform.models.base import Base
from bc_ferry_data_platform.models.route import Route
from bc_ferry_data_platform.models.sailing import Sailing
from bc_ferry_data_platform.repositories.route import (add_sailing_history,
                                                       get_by_code,
                                                       get_or_add_route)


@pytest.fixture
def session():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    with Session(engine) as database_session:
        yield database_session

    Base.metadata.drop_all(engine)
    engine.dispose()


def test_add_and_get_route_with_sailings(session: Session) -> None:
    route = Route(
        routeCode="TSASWB",
        source="TSA",
        destination="SWB",
        duration="1h 35m",
        ferries=[
            Sailing(
                routeCode="TSASWB",
                departureTime="08:00",
                arrivalTime="09:35",
                status="future",
                vessel="Test vessel",
                fill=25,
                carFill=30,
                oversizeFill=10,
                sailingDate=date(2026, 11, 2),
            )
        ],
    )

    get_or_add_route(session, route)
    session.commit()
    session.expunge_all()

    stored_route = get_by_code(session, "TSASWB")

    assert stored_route is not None
    assert stored_route.routeCode == "TSASWB"
    assert len(stored_route.ferries) == 1
    assert stored_route.ferries[0].departureTime == "08:00"
    assert stored_route.ferries[0].vessel == "Test vessel"


def test_get_by_code_returns_none_when_route_is_missing(session: Session) -> None:
    assert get_by_code(session, "MISSING") is None


def test_two_refreshes_keep_sailing_history(session: Session) -> None:
    route = Route(
        routeCode="TSASWB",
        source="TSA",
        destination="SWB",
        duration="1h 35m",
    )
    stored_route = get_or_add_route(session, route)
    add_sailing_history(
        session,
        stored_route.routeCode,
        [
            Sailing(
                departureTime="08:00",
                arrivalTime="09:35",
                status="future",
                vessel="Test vessel",
                fill=25,
                carFill=30,
                oversizeFill=10,
                sailingDate=date(2026, 11, 2),
            ),
        ],
    )
    session.commit()

    existing_route = get_or_add_route(
        session,
        Route(
            routeCode="TSA-SWB",
            source="TSA",
            destination="SWB",
            duration="1h 35m",
        ),
    )
    assert existing_route.id == stored_route.id
    add_sailing_history(
        session,
        existing_route.routeCode,
        [
            Sailing(
                departureTime="08:30",
                arrivalTime="10:05",
                status="future",
                vessel="Test vessel",
                fill=20,
                carFill=25,
                oversizeFill=5,
                sailingDate=date(2026, 11, 3),
            ),
        ],
    )
    session.commit()
    session.expunge_all()

    stored_route = get_by_code(session, "TSA-SWB")

    assert stored_route is not None
    assert len(stored_route.ferries) == 2
    assert {sailing.departureTime for sailing in stored_route.ferries} == {
        "08:00",
        "08:30",
    }
    assert all(sailing.capturedAt is not None for sailing in stored_route.ferries)
