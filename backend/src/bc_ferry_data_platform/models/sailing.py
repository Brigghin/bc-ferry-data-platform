"""Defines models for ferry sailings in PostgreSQL."""

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bc_ferry_data_platform.models.base import Base

if TYPE_CHECKING:
    from bc_ferry_data_platform.models.route import Route


class Sailing(Base):
    """Sailing model for a specific ferry departure"""

    __tablename__ = "sailings"
    __table_args__ = (
        UniqueConstraint(
            "route_code",
            "service_date",
            "scheduled_time",
            name="uq_sailing_route_service_scheduled",
        ),
        Index("ix_sailing_route_date", "route_code", "service_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    routeCode: Mapped[str] = mapped_column(
        "route_code", String(6), ForeignKey("routes.route_code")
    )

    serviceDate: Mapped[date] = mapped_column("service_date", Date)
    scheduledTime: Mapped[datetime | None] = mapped_column(
        "scheduled_time", DateTime(timezone=True), nullable=True
    )
    actualDepartureTime: Mapped[datetime | None] = mapped_column(
        "actual_departure_time",
        DateTime(timezone=True), default=None
    )
    actualArrivalTime: Mapped[datetime | None] = mapped_column(
        "actual_arrival_time",
        DateTime(timezone=True), default=None
    )

    capacityKnown: Mapped[bool] = mapped_column("capacity_known", Boolean, default=False)
    carCapacityKnown: Mapped[bool] = mapped_column("car_capacity_known", Boolean, default=False)
    oversizeCapacityKnown: Mapped[bool] = mapped_column(
        "oversize_capacity_known", Boolean, default=False
    )
    fill: Mapped[int] = mapped_column(default=0)
    carFill: Mapped[int] = mapped_column("car_fill", default=0)
    oversizeFill: Mapped[int] = mapped_column("oversize_fill", default=0)

    vesselName: Mapped[str] = mapped_column("vessel_name", String, default="")
    status: Mapped[str] = mapped_column(String, default="unknown")

    observedAt: Mapped[datetime | None] = mapped_column(
        "observed_at",
        DateTime(timezone=True), default=None
    )
    APICapturedAt: Mapped[datetime | None] = mapped_column(
        "api_captured_at",
        DateTime(timezone=True), default=None
    )

    route: Mapped["Route"] = relationship(back_populates="sailings")
