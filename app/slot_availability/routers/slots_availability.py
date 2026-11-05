from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.slot_availability import crud
from app.slot_availability.schemas import (
    SlotAvailabilityCreate,
    SlotAvailabilityUpdate,
    SlotAvailabilityResponse,
)


router = APIRouter(
    prefix="/api/v1/slots-availability",
    tags=["Slot Availability"],
)


@router.post(
    "",
    response_model=SlotAvailabilityResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_slots_availability(
    payload: SlotAvailabilityCreate,
    db: Session = Depends(get_db),
):
    record = crud.create_slots_availability(db, payload)

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="Charging station not found.",
        )

    if record is False:
        raise HTTPException(
            status_code=409,
            detail="Slot availability already exists for this station.",
        )

    if record == "capacity_exceeded":
        raise HTTPException(
            status_code=422,
            detail="Available slots cannot exceed total station capacity.",
        )

    return record


@router.get(
    "",
    response_model=list[SlotAvailabilityResponse],
)
def get_all_slots_availability(
    db: Session = Depends(get_db),
):
    return crud.get_all_slots_availability(db)


@router.get(
    "/station/{station_id}",
    response_model=SlotAvailabilityResponse,
)
def get_slots_by_station(
    station_id: int,
    db: Session = Depends(get_db),
):
    record = crud.get_slots_availability_by_station(db, station_id)

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="Slot availability not found for this station.",
        )

    return record


@router.get(
    "/{availability_id}",
    response_model=SlotAvailabilityResponse,
)
def get_slots_by_id(
    availability_id: int,
    db: Session = Depends(get_db),
):
    record = crud.get_slots_availability_by_id(db, availability_id)

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="Slot availability record not found.",
        )

    return record


@router.patch(
    "/{availability_id}",
    response_model=SlotAvailabilityResponse,
)
def update_slots_availability(
    availability_id: int,
    payload: SlotAvailabilityUpdate,
    db: Session = Depends(get_db),
):
    record = crud.update_slots_availability(
        db,
        availability_id,
        payload,
    )

    if record is None:
        raise HTTPException(status_code=404, detail="Record not found.")

    if record == "empty":
        raise HTTPException(
            status_code=422,
            detail="Provide at least one slot count to update.",
        )

    if record == "capacity_exceeded":
        raise HTTPException(
            status_code=422,
            detail="Available slots cannot exceed total station capacity.",
        )

    return record


@router.delete(
    "/{availability_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_slots_availability(
    availability_id: int,
    db: Session = Depends(get_db),
):
    record = crud.delete_slots_availability(db, availability_id)

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="Slot availability record not found.",
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)