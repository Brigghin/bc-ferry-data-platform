"""Defines models for ferry sailings in PostgreSQL."""

from typing import TYPE_CHECKING
from datetime import datetime
from datetime import date

from sqlalchemy import String
from sqlalchemy import Integer
from sqlalchemy import Date
from sqlalchemy import DateTime
from sqlalchemy import text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

from bc_ferry_data_platform.models.base import Base

if TYPE_CHECKING:
    from bc_ferry_data_platform.models.route import Route

class Sailing(Base):
    """Route model for FerryInfo"""
    __tablename__ = "sailings"

    id: Mapped[int] = mapped_column(primary_key=True)
    routeCode: Mapped[str] = mapped_column(
        "route_code", String(6), ForeignKey("routes.route_code")
    )
    departureTime: Mapped[str] = mapped_column("departure_time", String)
    arrivalTime: Mapped[str] = mapped_column("arrival_time", String)
    status: Mapped[str] = mapped_column(String)
    vessel: Mapped[str] = mapped_column(String)
    fill: Mapped[int] = mapped_column(Integer)
    carFill: Mapped[int] = mapped_column("car_fill", Integer)
    oversizeFill: Mapped[int] = mapped_column("oversize_fill", Integer)
    sailingDate: Mapped[date] = mapped_column("sailing_date", Date, nullable=False)
    capturedAt: Mapped[datetime] = mapped_column(
        "captured_at",
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )

    route: Mapped["Route"] = relationship(back_populates="ferries")
