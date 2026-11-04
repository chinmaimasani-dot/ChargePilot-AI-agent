from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    owner_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    vehicle_number: Mapped[str] = mapped_column(
        String(30), nullable=False, unique=True, index=True
    )
    vehicle_type: Mapped[str] = mapped_column(String(20), nullable=False)
    company_name: Mapped[str] = mapped_column(String(100), nullable=False)
    charging_capacity: Mapped[float] = mapped_column(Float, nullable=False)
    vehicle_model: Mapped[str] = mapped_column(String(50), nullable=False)
    charging_type: Mapped[str] = mapped_column(String(2), nullable=False)
    year_of_manufacturing: Mapped[int] = mapped_column(Integer, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    legacy_model: Mapped[str | None] = mapped_column(
        "model", String(100), nullable=True
    )
    legacy_connector_type: Mapped[str | None] = mapped_column(
        "connector_type", String(50), nullable=True
    )
    legacy_max_charging_power_kw: Mapped[float | None] = mapped_column(
        "max_charging_power_kw", Float, nullable=True
    )