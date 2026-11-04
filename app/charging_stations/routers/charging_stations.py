from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.charging_stations.database import (
    get_charging_stations_db as get_db,
)
from app.charging_stations import crud
from app.charging_stations.schemas import (
    AddressCreate,
    AddressResponse,
    ChargingStationCreate,
    ChargingStationUpdate,
    ChargingStationResponse,
)


router = APIRouter(
    prefix="/api/v1",
    tags=["Charging Stations"],
)


# --------------------------------
# CREATE ADDRESS
# --------------------------------

@router.post(
    "/addresses",
    response_model=AddressResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_address(
    address_data: AddressCreate,
    db: Session = Depends(get_db),
):
    return crud.create_address(db, address_data)


# --------------------------------
# CREATE CHARGING STATION
# --------------------------------

@router.post(
    "/stations",
    response_model=ChargingStationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_station(
    station_data: ChargingStationCreate,
    db: Session = Depends(get_db),
):
    station = crud.create_station(db, station_data)

    if station is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found",
        )

    return station


# --------------------------------
# GET ALL CHARGING STATIONS
# --------------------------------

@router.get(
    "/stations",
    response_model=list[ChargingStationResponse],
)
def get_all_stations(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return crud.get_all_stations(db, skip, limit)


# --------------------------------
# GET ONE CHARGING STATION
# --------------------------------

@router.get(
    "/stations/{station_id}",
    response_model=ChargingStationResponse,
)
def get_station(
    station_id: int,
    db: Session = Depends(get_db),
):
    station = crud.get_station(db, station_id)

    if station is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Charging station not found",
        )

    return station


# --------------------------------
# UPDATE CHARGING STATION
# --------------------------------

@router.put(
    "/stations/{station_id}",
    response_model=ChargingStationResponse,
)
def update_station(
    station_id: int,
    station_data: ChargingStationUpdate,
    db: Session = Depends(get_db),
):
    station = crud.update_station(
        db,
        station_id,
        station_data,
    )

    if station is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Charging station or address not found",
        )

    return station


# --------------------------------
# DELETE CHARGING STATION
# --------------------------------

@router.delete(
    "/stations/{station_id}",
)
def delete_station(
    station_id: int,
    db: Session = Depends(get_db),
):
    station = crud.delete_station(db, station_id)

    if station is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Charging station not found",
        )

    return {
        "message": "Charging station deleted successfully",
        "station_id": station_id,
    }


# --------------------------------
# UPDATE STATION STATUS
# --------------------------------

@router.patch(
    "/stations/{station_id}/status",
    response_model=ChargingStationResponse,
)
def update_station_status(
    station_id: int,
    is_active: bool,
    db: Session = Depends(get_db),
):
    station = crud.update_station_status(
        db,
        station_id,
        is_active,
    )

    if station is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Charging station not found",
        )

    return station
