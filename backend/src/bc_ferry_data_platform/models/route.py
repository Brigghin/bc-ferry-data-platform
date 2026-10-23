"""Defines models for ferry routes in PostgreSQL."""

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from bc_ferry_data_platform.models.base import Base

if TYPE_CHECKING:
    from bc_ferry_data_platform.models.sailing import Sailing

class Route(Base):
    """Route model for FerryRoute"""
    __tablename__ = "routes"

    id: Mapped[int] = mapped_column(primary_key=True)
    routeCode: Mapped[str] = mapped_column("route_code", String(6), unique=True)
    source: Mapped[str] = mapped_column(String(3))
    destination: Mapped[str] = mapped_column(String(3))
    duration: Mapped[str] = mapped_column(String)
    ferries: Mapped[list["Sailing"]] = relationship(
        back_populates="route",
        cascade="all, delete-orphan",
    )
