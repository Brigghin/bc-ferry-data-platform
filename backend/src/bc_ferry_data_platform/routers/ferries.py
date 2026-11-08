"""Expose API routes for ferry schedule data."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database.dependencies import get_session
from ..schemas.ferries import FerryRoute
from ..services.ferries import fetch_storage_ferries, upload_ferries

router = APIRouter(prefix="/ferries")


@router.get("/", response_model=list[FerryRoute])
def list_ferries(
    session: Annotated[Session, Depends(get_session)],
    route_code: str | None = None,
) -> list[FerryRoute]:
    """Return ferry routes and their scheduled sailings."""
    return fetch_storage_ferries(session, route_code)


@router.post("/refresh")
async def refresh_ferries(
    session: Annotated[Session, Depends(get_session)],
) -> int:
    """Upload ferry routes and their scheduled sailings."""
    return await upload_ferries(session)
