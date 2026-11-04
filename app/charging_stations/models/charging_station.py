from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    Numeric,
    text,
)
from sqlalchemy.orm import relationship

from app.database import Base


class ChargingStation(Base):
    __tablename__ = "charging_stations"

    id = Column(Integer, primary_key=True, index=True)

    address_id = Column(
        Integer,
        ForeignKey("addresses.id"),
        nullable=False
    )

    two_wheeler_slots_count = Column(
        Integer,
        nullable=False,
        default=100,
        server_default=text("100")
    )

    three_wheeler_slots_count = Column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0")
    )

    four_wheeler_slots_count = Column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0")
    )

    two_wheeler_cost = Column(
        Numeric(10, 2),
        nullable=False
    )

    three_wheeler_cost = Column(
        Numeric(10, 2),
        nullable=False
    )

    four_wheeler_cost = Column(
        Numeric(10, 2),
        nullable=False
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true")
    )

    address = relationship(
        "Address",
        back_populates="charging_stations"
    )