
"""Expose API routes for ferry schedule data."""

from fastapi import APIRouter

from ..models.ferries import FerryRoute
from ..services.ferries import fetch_ferries

BASE_URL = "https://www.bcferriesapi.ca/v2"

router = APIRouter(prefix="/ferries")


@router.get("/", response_model=list[FerryRoute])
async def list_ferries(route_code: str | None = None,) -> list[FerryRoute]:
    """Return ferry routes and their scheduled sailings."""
    return await fetch_ferries(route_code)
