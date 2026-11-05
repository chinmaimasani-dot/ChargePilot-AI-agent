from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from chargepilot_slot_availability_api.database import get_db
from chargepilot_slot_availability_api.models.slots_availability import (
    ChargingStationReference,
    SlotAvailability,
)
from chargepilot_slot_availability_api.schemas.slots_availability import (
    SlotAvailabilityCreate,
    SlotAvailabilityResponse,
    SlotAvailabilityUpdate,
)


router = APIRouter(prefix="/api/v1/slots-availability", tags=["Slot availability"])


@router.post(
    "",
    response_model=SlotAvailabilityResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create slot availability for a station",
)
def create_slots_availability(
    payload: SlotAvailabilityCreate,
    db: Session = Depends(get_db),
):
    station_exists = db.scalar(
        select(ChargingStationReference.id).where(
            ChargingStationReference.id == payload.station_id
        )
    )
    if station_exists is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Charging station {payload.station_id} was not found.",
        )

    existing = db.scalar(
        select(SlotAvailability.id).where(
            SlotAvailability.station_id == payload.station_id
        )
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Slot availability already exists for this station.",
        )

    record = SlotAvailability(**payload.model_dump())
    db.add(record)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Could not create availability; the station may already have a record.",
        ) from None
    db.refresh(record)
    return record


@router.get(
    "",
    response_model=list[SlotAvailabilityResponse],
    summary="List slot availability records",
)
def list_slots_availability(db: Session = Depends(get_db)):
    return db.scalars(select(SlotAvailability).order_by(SlotAvailability.id)).all()


@router.get(
    "/station/{station_id}",
    response_model=SlotAvailabilityResponse,
    summary="Get availability for a station",
)
def get_station_slots_availability(
    station_id: int,
    db: Session = Depends(get_db),
):
    record = db.scalar(
        select(SlotAvailability).where(SlotAvailability.station_id == station_id)
    )
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Slot availability was not found for this station.",
        )
    return record


@router.get(
    "/{availability_id}",
    response_model=SlotAvailabilityResponse,
    summary="Get a slot availability record by ID",
)
def get_slots_availability(
    availability_id: int,
    db: Session = Depends(get_db),
):
    record = db.get(SlotAvailability, availability_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Slot availability record was not found.",
        )
    return record


@router.patch(
    "/{availability_id}",
    response_model=SlotAvailabilityResponse,
    summary="Update slot counts",
)
def update_slots_availability(
    availability_id: int,
    payload: SlotAvailabilityUpdate,
    db: Session = Depends(get_db),
):
    record = db.get(SlotAvailability, availability_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Slot availability record was not found.",
        )

    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Provide at least one slot count to update.",
        )

    for field, value in updates.items():
        setattr(record, field, value)
    db.commit()
    db.refresh(record)
    return record


@router.delete(
    "/{availability_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a slot availability record",
)
def delete_slots_availability(
    availability_id: int,
    db: Session = Depends(get_db),
):
    record = db.get(SlotAvailability, availability_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Slot availability record was not found.",
        )
    db.delete(record)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
