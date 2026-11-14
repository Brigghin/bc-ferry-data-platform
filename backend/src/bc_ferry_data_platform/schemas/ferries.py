"""Define response models for ferry routes and sailing times."""

from datetime import datetime, date

from pydantic import BaseModel, ConfigDict


class Sailing(BaseModel):
    """Represents the information for a specific ferry departure."""
    model_config = ConfigDict(from_attributes=True)

    serviceDate: date
    scheduledTime: datetime | None = None #BC time zone
    actualDepartureTime: datetime | None = None #BC time zone
    actualArrivalTime: datetime | None = None #BC time zone
    capacityKnown: bool
    carCapacityKnown: bool
    oversizeCapacityKnown: bool
    fill: int
    carFill: int
    oversizeFill: int
    vesselName: str
    status: str
    observedAt: datetime | None = None
    APICapturedAt: datetime | None = None


class Route(BaseModel):
    """Represents a ferry route with its scheduled departures."""
    model_config = ConfigDict(from_attributes=True)

    routeCode: str
    fromTerminalCode: str
    toTerminalCode: str
    sailingDuration: str
    sailings: list[Sailing]
