"""Repository functions for managing ferry routes and sailings in the database."""
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from bc_ferry_data_platform.models.route import Route
from bc_ferry_data_platform.models.sailing import Sailing


def normalize_route_code(route_code: str) -> str:
    """Turn route codes like 'tsa-swb ' into the stored form 'TSASWB'."""
    return route_code.replace("-", "").strip().upper()


def _as_utc(value: datetime | None) -> datetime | None:
    """Compare times in UTC; SQLite drops the offset, so naive values are stored UTC."""
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def get_or_add_route(session: Session, route: Route) -> Route:
    """Retrieve a ferry route by its code, or add it to the database if it doesn't exist."""
    route.routeCode = normalize_route_code(route.routeCode)
    statement = select(Route).where(Route.routeCode == route.routeCode)
    stored_route = session.scalar(statement)
    if stored_route is None:
        session.add(route)
        session.flush()
        return route
    stored_route.fromTerminalCode = route.fromTerminalCode
    stored_route.toTerminalCode = route.toTerminalCode
    if route.sailingDuration:  # the feed sometimes blanks it; keep the last known value
        stored_route.sailingDuration = route.sailingDuration
    return stored_route


def add_sailing_history(
    session: Session,
    route_code: str,
    sailings: list[Sailing],
) -> None:
    """Add or update sailing history for a specific ferry route."""
    # One query per route: load stored sailings for the dates in this snapshot.
    statement = (
        select(Sailing)
        .where(Sailing.routeCode == route_code)
        .where(Sailing.serviceDate.in_({sailing.serviceDate for sailing in sailings}))
    )
    stored = {
        (row.serviceDate, _as_utc(row.scheduledTime)): row
        for row in session.scalars(statement)
    }
    for sailing in sailings:
        if sailing.scheduledTime is None:
            raise ValueError(
                f"Sailing for route {route_code} on {sailing.serviceDate} "
                "has no scheduled time"
            )
        sailing.scheduledTime = _as_utc(sailing.scheduledTime)
        key = (sailing.serviceDate, sailing.scheduledTime)
        stored_sailing = stored.get(key)

        if stored_sailing is None:
            session.add(sailing)
            stored[key] = sailing
            continue

        if sailing.actualDepartureTime is not None:
            stored_sailing.actualDepartureTime = sailing.actualDepartureTime
        if sailing.actualArrivalTime is not None:
            stored_sailing.actualArrivalTime = sailing.actualArrivalTime
        stored_sailing.capacityKnown = sailing.capacityKnown
        stored_sailing.carCapacityKnown = sailing.carCapacityKnown
        stored_sailing.oversizeCapacityKnown = sailing.oversizeCapacityKnown
        if sailing.capacityKnown:
            stored_sailing.fill = sailing.fill
        if sailing.carCapacityKnown:
            stored_sailing.carFill = sailing.carFill
        if sailing.oversizeCapacityKnown:
            stored_sailing.oversizeFill = sailing.oversizeFill
        stored_sailing.vesselName = sailing.vesselName
        stored_sailing.status = sailing.status
        stored_sailing.observedAt = sailing.observedAt
        stored_sailing.APICapturedAt = sailing.APICapturedAt
