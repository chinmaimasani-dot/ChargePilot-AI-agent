from sqlalchemy.orm import Session

from app.charging_stations.models import ChargingStation
from app.slot_availability.models import SlotAvailability
from app.slot_availability.schemas import (
    SlotAvailabilityCreate,
    SlotAvailabilityUpdate,
)


def create_slots_availability(
    db: Session,
    payload: SlotAvailabilityCreate,
):
    station = db.get(ChargingStation, payload.station_id)

    if station is None:
        return None

    existing = (
        db.query(SlotAvailability)
        .filter(SlotAvailability.station_id == payload.station_id)
        .first()
    )

    if existing:
        return False

    # Available slots cannot exceed total station capacity.
    capacity_fields = {
        "two_wheeler_slots_count": station.two_wheeler_slots_count,
        "three_wheeler_slots_count": station.three_wheeler_slots_count,
        "four_wheeler_slots_count": station.four_wheeler_slots_count,
    }

    data = payload.model_dump()

    for field, capacity in capacity_fields.items():
        if data[field] > capacity:
            return "capacity_exceeded"

    record = SlotAvailability(**data)

    try:
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    except Exception:
        db.rollback()
        raise


def get_all_slots_availability(db: Session):
    return (
        db.query(SlotAvailability)
        .order_by(SlotAvailability.id)
        .all()
    )


def get_slots_availability_by_station(
    db: Session,
    station_id: int,
):
    return (
        db.query(SlotAvailability)
        .filter(SlotAvailability.station_id == station_id)
        .first()
    )


def get_slots_availability_by_id(
    db: Session,
    availability_id: int,
):
    return db.get(SlotAvailability, availability_id)


def update_slots_availability(
    db: Session,
    availability_id: int,
    payload: SlotAvailabilityUpdate,
):
    record = db.get(SlotAvailability, availability_id)

    if record is None:
        return None

    updates = payload.model_dump(
        exclude_unset=True,
        exclude_none=True,
    )

    if not updates:
        return "empty"

    station = db.get(ChargingStation, record.station_id)

    if station is None:
        return None

    capacities = {
        "two_wheeler_slots_count": station.two_wheeler_slots_count,
        "three_wheeler_slots_count": station.three_wheeler_slots_count,
        "four_wheeler_slots_count": station.four_wheeler_slots_count,
    }

    for field, value in updates.items():
        if value > capacities[field]:
            return "capacity_exceeded"

    try:
        for field, value in updates.items():
            setattr(record, field, value)

        db.commit()
        db.refresh(record)

        return record

    except Exception:
        db.rollback()
        raise


def delete_slots_availability(
    db: Session,
    availability_id: int,
):
    record = db.get(SlotAvailability, availability_id)

    if record is None:
        return None

    db.delete(record)
    db.commit()

    return record