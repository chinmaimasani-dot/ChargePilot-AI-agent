
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.models.vehicle import Vehicle
from app.charging_stations.models import ChargingStation
from app.reservations.models import Reservation
from app.reservations.schemas.reservation import ReservationCreate


def create_reservation(
    db: Session,
    reservation_data: ReservationCreate,
) -> Reservation:

    try:
        # 1. Lock the station row to prevent simultaneous bookings
        station = db.scalar(
            select(ChargingStation)
            .where(ChargingStation.id == reservation_data.station_id)
            .with_for_update()
        )

        if not station:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Charging station not found",
            )

        # 2. Check whether the customer exists
        user = db.get(User, reservation_data.user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # 3. Check whether the vehicle exists
        vehicle = db.get(Vehicle, reservation_data.vehicle_id)

        if not vehicle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vehicle not found",
            )

        # 4. Validate vehicle ownership
        if vehicle.owner_id != str(user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This vehicle does not belong to this user",
            )

        # 5. Check whether the station is active
        if not station.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This charging station is inactive",
            )

        # 6. Find the station capacity for this vehicle type
        capacity_columns = {
            "2 wheeler": "two_wheeler_slots_count",
            "3 wheeler": "three_wheeler_slots_count",
            "4 wheeler": "four_wheeler_slots_count",
        }

        capacity_column = capacity_columns.get(vehicle.vehicle_type)

        if not capacity_column:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported vehicle type",
            )

        station_capacity = getattr(station, capacity_column)

        if station_capacity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This station does not support this vehicle type",
            )

        # 7. Count confirmed reservations that overlap this time period
        overlapping_count = db.scalar(
            select(func.count(Reservation.id))
            .join(Vehicle, Reservation.vehicle_id == Vehicle.id)
            .where(
                Reservation.station_id == reservation_data.station_id,
                Reservation.status == "confirmed",
                Vehicle.vehicle_type == vehicle.vehicle_type,
                Reservation.start_time < reservation_data.end_time,
                Reservation.end_time > reservation_data.start_time,
            )
        ) or 0

        # 8. Check available capacity
        if overlapping_count >= station_capacity:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No charging slots available for this time period",
            )

        # 9. Create the reservation
        reservation = Reservation(
            user_id=user.id,
            vehicle_id=vehicle.id,
            station_id=station.id,
            start_time=reservation_data.start_time,
            end_time=reservation_data.end_time,
            status="confirmed",
        )

        db.add(reservation)
        db.commit()
        db.refresh(reservation)

        return reservation

    except Exception:
        db.rollback()
        raise


def get_reservations(
    db: Session,
    user_id: int | None = None,
    station_id: int | None = None,
):
    query = select(Reservation).order_by(Reservation.start_time.desc())

    if user_id is not None:
        query = query.where(Reservation.user_id == user_id)

    if station_id is not None:
        query = query.where(Reservation.station_id == station_id)

    return db.scalars(query).all()


def get_reservation_by_id(
    db: Session,
    reservation_id: int,
) -> Reservation:

    reservation = db.get(Reservation, reservation_id)

    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found",
        )

    return reservation


def cancel_reservation(
    db: Session,
    reservation_id: int,
) -> Reservation:

    reservation = get_reservation_by_id(db, reservation_id)

    if reservation.status != "confirmed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel a reservation with status '{reservation.status}'",
        )

    reservation.status = "cancelled"

    db.commit()
    db.refresh(reservation)

    return reservation


def complete_reservation(
    db: Session,
    reservation_id: int,
) -> Reservation:

    reservation = get_reservation_by_id(db, reservation_id)

    if reservation.status != "confirmed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot complete a reservation with status '{reservation.status}'",
        )

    reservation.status = "completed"

    db.commit()
    db.refresh(reservation)

    return reservation
