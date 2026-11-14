"""Defines models for ferry routes in PostgreSQL."""

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bc_ferry_data_platform.models.base import Base

if TYPE_CHECKING:
    from bc_ferry_data_platform.models.sailing import Sailing

class Route(Base):
    """Route model for FerryRoute"""

    __tablename__ = "routes"

    id: Mapped[int] = mapped_column(primary_key=True)
    routeCode: Mapped[str] = mapped_column("route_code", String(6), unique=True)
    fromTerminalCode: Mapped[str] = mapped_column("from_terminal_code", String(3))
    toTerminalCode: Mapped[str] = mapped_column("to_terminal_code", String(3))
    sailingDuration: Mapped[str] = mapped_column("sailing_duration", String, default="")
    sailings: Mapped[list["Sailing"]] = relationship(
        back_populates="route",
        cascade="all, delete-orphan",
        order_by="Sailing.scheduledTime",
    )
