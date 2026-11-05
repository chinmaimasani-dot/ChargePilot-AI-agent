from sqlalchemy import DateTime, Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class AddressDetails(Base):
    __tablename__ = "address_details"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    hno: Mapped[str | None] = mapped_column(String(50), nullable=True)
    street_village: Mapped[str] = mapped_column(String(150), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    pincode: Mapped[str] = mapped_column(String(10), nullable=False)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    long: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
