"""Define response models for ferry routes and sailing times."""

from datetime import date
from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict


class FerryRoute(BaseModel):
    """Represents a ferry route with its scheduled departures."""
    model_config = ConfigDict(from_attributes=True)

    routeCode: str
    source: str
    destination: str
    duration: str
    ferries: list[FerryInfo]


class FerryInfo(BaseModel):
    """Represents the information for a specific ferry departure."""
    model_config = ConfigDict(from_attributes=True)

    departureTime: str
    arrivalTime: str
    status: str
    vessel: str
    fill: int
    carFill: int
    oversizeFill: int
    sailingDate: date
    capturedAt: datetime | None = None
