"""Expose API routes for ferry schedule data."""

import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from ..config.settings import settings
from ..database.dependencies import get_session
from ..schemas.ferries import Route as RouteSchema
from ..services.ferries import fetch_storage_ferries, upload_ferries

router = APIRouter(prefix="/ferries")


@router.get("/", response_model=list[RouteSchema])
def list_ferries(
    session: Annotated[Session, Depends(get_session)],
    route_code: str | None = None,
) -> list[RouteSchema]:
    """Return ferry routes and their scheduled sailings."""
    return fetch_storage_ferries(session, route_code)


@router.post("/refresh")
def refresh_ferries(
    session: Annotated[Session, Depends(get_session)],
    x_refresh_token: Annotated[str, Header()] = "",
) -> int:
    """Upload ferry routes and their scheduled sailings."""
    if not settings.refresh_token or not secrets.compare_digest(
        x_refresh_token, settings.refresh_token
    ):
        raise HTTPException(status_code=401, detail="Invalid refresh token.")
    return upload_ferries(session)
