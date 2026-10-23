from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm import selectinload

from bc_ferry_data_platform.models.route import Route
from bc_ferry_data_platform.models.sailing import Sailing

def get_by_code(session: Session, route_code: str) -> Route | None:
    normalized_route_code = route_code.replace("-", "").strip().upper()
    statement = (
        select(Route)
        .options(selectinload(Route.ferries))
        .where(Route.routeCode == normalized_route_code)
    )
    return session.scalar(statement)

def get_or_add_route(session: Session, route: Route) -> Route:
    route.routeCode = route.routeCode.replace("-", "").strip().upper()
    statement = select(Route).where(Route.routeCode == route.routeCode)
    stored_route = session.scalar(statement)
    if stored_route is None:
        session.add(route)
        return route
    return stored_route


def add_sailing_history(
    session: Session,
    route_code: str,
    sailings: list[Sailing],
) -> None:
    for sailing in sailings:
        sailing.routeCode = route_code
    session.add_all(sailings)

