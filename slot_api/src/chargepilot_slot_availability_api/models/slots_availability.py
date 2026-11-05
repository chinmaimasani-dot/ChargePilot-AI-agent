from sqlalchemy import CheckConstraint, ForeignKey, Integer, text
from sqlalchemy.orm import Mapped, mapped_column

from chargepilot_slot_availability_api.database import Base


class ChargingStationReference(Base):
    """Reference the existing charging_stations table in Neon."""

    __tablename__ = "charging_stations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)


class SlotAvailability(Base):
    __tablename__ = "slots_availability"

    __table_args__ = (
        CheckConstraint(
            "two_wheeler_slots_count >= 0",
            name="ck_slots_availability_two_wheeler_nonnegative",
        ),
        CheckConstraint(
            "three_wheeler_slots_count >= 0",
            name="ck_slots_availability_three_wheeler_nonnegative",
        ),
        CheckConstraint(
            "four_wheeler_slots_count >= 0",
            name="ck_slots_availability_four_wheeler_nonnegative",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # One current availability record per charging station.
    station_id: Mapped[int] = mapped_column(
        ForeignKey("charging_stations.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    two_wheeler_slots_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    three_wheeler_slots_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    four_wheeler_slots_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )