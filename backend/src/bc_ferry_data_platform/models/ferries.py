"""Define response models for ferry routes and sailing times."""

from pydantic import BaseModel


class FerryRoute(BaseModel):
    """Represents a ferry route with its scheduled departures."""
    routeCode: str
    source: str
    destination: str
    duration: str
    ferries: list[FerryInfo]


class FerryInfo(BaseModel):
    """Represents the information for a specific ferry departure."""
    departureTime: str
    arrivalTime: str
    status: str
    vessel: str
    fill: int
    carFill: int
    oversizeFill: int
