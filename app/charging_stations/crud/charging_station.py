
from sqlalchemy.orm import Session

from app.charging_stations.models import Address, ChargingStation
from app.charging_stations.schemas import (
    AddressCreate,
    ChargingStationCreate,
    ChargingStationUpdate,
)

# --------------------------------
# ADDRESS CRUD OPERATIONS
# --------------------------------

def create_address(db: Session, address_data: AddressCreate):
    new_address = Address(**address_data.model_dump())

    db.add(new_address)
    db.commit()
    db.refresh(new_address)

    return new_address


def get_address(db: Session, address_id: int):
    return db.query(Address).filter(
        Address.id == address_id
    ).first()


# --------------------------------
# CHARGING STATION CRUD OPERATIONS
# --------------------------------

def create_station(
    db: Session,
    station_data: ChargingStationCreate
):
    # Check whether the address exists
    address = get_address(db, station_data.address_id)

    if not address:
        return None

    new_station = ChargingStation(
        **station_data.model_dump()
    )

    db.add(new_station)
    db.commit()
    db.refresh(new_station)

    return new_station


def get_all_stations(
    db: Session,
    skip: int = 0,
    limit: int = 10
):
    return (
        db.query(ChargingStation)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_station(db: Session, station_id: int):
    return (
        db.query(ChargingStation)
        .filter(ChargingStation.id == station_id)
        .first()
    )


def update_station(
    db: Session,
    station_id: int,
    station_data: ChargingStationUpdate
):
    station = get_station(db, station_id)

    if not station:
        return None

    update_data = station_data.model_dump(
        exclude_unset=True,
        exclude_none=True
    )

    # If the address is changed, verify that it exists
    if "address_id" in update_data:
        address = get_address(db, update_data["address_id"])

        if not address:
            return None

    for field, value in update_data.items():
        setattr(station, field, value)

    db.commit()
    db.refresh(station)

    return station


def delete_station(db: Session, station_id: int):
    station = get_station(db, station_id)

    if not station:
        return None

    db.delete(station)
    db.commit()

    return station


def update_station_status(
    db: Session,
    station_id: int,
    is_active: bool
):
    station = get_station(db, station_id)

    if not station:
        return None

    station.is_active = is_active

    db.commit()
    db.refresh(station)

    return station
