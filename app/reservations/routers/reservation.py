
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.reservations.schemas.reservation import (
    ReservationCreate,
    ReservationRead,
)
from app.reservations.crud.reservation import (
    create_reservation,
    get_reservations,
    get_reservation_by_id,
    cancel_reservation,
    complete_reservation,
)

router = APIRouter(
    prefix="/api/v1/reservations",
    tags=["Reservations"],
)


@router.post("/", response_model=ReservationRead, status_code=201)
def create_reservation_api(
    reservation_data: ReservationCreate,
    db: Session = Depends(get_db),
):
    return create_reservation(db, reservation_data)


@router.get("/", response_model=list[ReservationRead])
def get_reservations_api(
    user_id: int | None = Query(default=None, gt=0),
    station_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
):
    return get_reservations(
        db,
        user_id=user_id,
        station_id=station_id,
    )


@router.get("/{reservation_id}", response_model=ReservationRead)
def get_reservation_api(
    reservation_id: int,
    db: Session = Depends(get_db),
):
    return get_reservation_by_id(db, reservation_id)


@router.patch("/{reservation_id}/cancel", response_model=ReservationRead)
def cancel_reservation_api(
    reservation_id: int,
    db: Session = Depends(get_db),
):
    return cancel_reservation(db, reservation_id)


@router.patch("/{reservation_id}/complete", response_model=ReservationRead)
def complete_reservation_api(
    reservation_id: int,
    db: Session = Depends(get_db),
):
    return complete_reservation(db, reservation_id)
