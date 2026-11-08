"""Defines models for ferry sailings in PostgreSQL."""

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

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
