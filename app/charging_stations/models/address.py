from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base


class Address(Base):
    __tablename__ = "addresses"

    id = Column(Integer, primary_key=True, index=True)

    # Existing fields
    street = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    postal_code = Column(String(20), nullable=False)
    country = Column(String(100), nullable=False)

    # New fields from teammate's Address API
    hno = Column(String(50), nullable=True)
    lat = Column(Float, nullable=True)
    long = Column(Float, nullable=True)

    # Timestamp fields
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Existing relationship
    charging_stations = relationship(
        "ChargingStation",
        back_populates="address",
    )