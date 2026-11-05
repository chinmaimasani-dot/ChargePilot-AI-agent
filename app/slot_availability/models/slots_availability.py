from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Integer,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SlotAvailability(Base):
    __tablename__ = "slots_availability"

    __table_args__ = (
        UniqueConstraint(
            "station_id",
            name="uq_slots_availability_station_id",
        ),
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

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    station_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("charging_stations.id", ondelete="CASCADE"),
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