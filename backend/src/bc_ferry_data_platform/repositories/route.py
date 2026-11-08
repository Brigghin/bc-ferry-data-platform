"""Repository functions for managing ferry routes and sailings in the database."""
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from bc_ferry_data_platform.models.route import Route
from bc_ferry_data_platform.models.sailing import Sailing


def get_by_code(session: Session, route_code: str) -> Route | None:
    """Retrieve a ferry route by its code, including its associated ferries."""
    normalized_route_code = route_code.replace("-", "").strip().upper()
    statement = (
        select(Route)
        .options(selectinload(Route.ferries))
        .where(Route.routeCode == normalized_route_code)
    )
    return session.scalar(statement)

def get_or_add_route(session: Session, route: Route) -> Route:
    """Retrieve a ferry route by its code, or add it to the database if it doesn't exist."""
    route.routeCode = route.routeCode.replace("-", "").strip().upper()
    statement = select(Route).where(Route.routeCode == route.routeCode)
    stored_route = session.scalar(statement)
    if stored_route is None:
        session.add(route)
        session.flush()
        return route
    return stored_route


def add_sailing_history(
    session: Session,
    route_code: str,
    sailings: list[Sailing],
) -> None:
    """Add or update sailing history for a specific ferry route."""
    for sailing in sailings:
        statement = (select(Sailing).where(Sailing.routeCode == route_code)
                     .where(Sailing.departureTime == sailing.departureTime)
                     .where(Sailing.sailingDate == sailing.sailingDate))
        stored_sailing = session.scalar(statement)

        if stored_sailing is None:
            session.add(sailing)
            session.flush()
            continue

        if sailing.arrivalTime:
            stored_sailing.arrivalTime = sailing.arrivalTime

        if sailing.status != "past" or sailing.carFill != 0:
            stored_sailing.carFill = sailing.carFill

        if sailing.fill:
            stored_sailing.fill = sailing.fill

        if sailing.oversizeFill:
            stored_sailing.oversizeFill = sailing.oversizeFill
