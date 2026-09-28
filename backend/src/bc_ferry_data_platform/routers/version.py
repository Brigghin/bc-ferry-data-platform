"""Expose the backend package version through the API."""

from importlib.metadata import version

from fastapi import APIRouter

router = APIRouter(prefix="/version")

@router.get("/")
def get_version() -> dict[str, str]:
    """Return the current backend version maintained by Release Please."""
    return {"version": version("bc-ferry-data-platform")}
