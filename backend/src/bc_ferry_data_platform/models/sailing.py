"""Defines models for ferry sailings in PostgreSQL."""

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy import Integer
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
    route_code: Mapped[str] = mapped_column(String(6), ForeignKey("routes.route_code"))
    departure_time: Mapped[str] = mapped_column(String)
    arrival_time: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)
    vessel: Mapped[str] = mapped_column(String)
    fill: Mapped[int] = mapped_column(Integer)
    car_fill: Mapped[int] = mapped_column(Integer)
    oversize_fill: Mapped[int] = mapped_column(Integer)

    route: Mapped["Route"] = relationship(back_populates="sailings")
