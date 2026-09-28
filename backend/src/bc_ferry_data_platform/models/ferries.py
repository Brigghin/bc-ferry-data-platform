"""Define response models for ferry routes and sailing times."""

from pydantic import BaseModel


class FerryRoute(BaseModel):
    """Represents a ferry route with its scheduled departures."""
    source: str
    destination: str
    ferries: list[FerriesTiming]


class FerriesTiming(BaseModel):
    """Represents the timing information for a ferry departure."""
    departed: bool
    departure_time: str
    arrival_time: str
