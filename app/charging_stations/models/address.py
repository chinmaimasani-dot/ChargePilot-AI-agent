
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base

class Address(Base):
    __tablename__ = "addresses"

    id = Column(Integer, primary_key=True, index=True)

    street = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    postal_code = Column(String(20), nullable=False)
    country = Column(String(100), nullable=False)

    charging_stations = relationship(
        "ChargingStation",
        back_populates="address"
    )