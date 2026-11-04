from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy import select

from app.database import SessionLocal
from app.models.vehicle import Vehicle
from app.schemas.vehicle import VehicleCreate, VehicleRead, VehicleUpdate

router = APIRouter(prefix="/api/v1/vehicles", tags=["Vehicles"])


@router.post(
    "",
    response_model=VehicleRead,
    status_code=status.HTTP_201_CREATED,
)
def create_vehicle(vehicle_data: VehicleCreate):
    with SessionLocal() as session:
        vehicle = Vehicle(**vehicle_data.model_dump())
        session.add(vehicle)
        session.commit()
        session.refresh(vehicle)
        return vehicle


@router.get("", response_model=list[VehicleRead])
def list_vehicles(
    owner_id: str = Query(min_length=1, max_length=100),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    with SessionLocal() as session:
        statement = (
            select(Vehicle)
            .where(Vehicle.owner_id == owner_id)
            .order_by(Vehicle.id)
            .limit(limit)
            .offset(offset)
        )
        return session.scalars(statement).all()


@router.get("/{vehicle_id}", response_model=VehicleRead)
def get_vehicle(
    vehicle_id: int,
    owner_id: str = Query(min_length=1, max_length=100),
):
    with SessionLocal() as session:
        statement = select(Vehicle).where(
            Vehicle.id == vehicle_id,
            Vehicle.owner_id == owner_id,
        )
        vehicle = session.scalar(statement)

        if vehicle is None:
            raise HTTPException(status_code=404, detail="Vehicle not found")

        return vehicle


@router.patch("/{vehicle_id}", response_model=VehicleRead)
def update_vehicle(
    vehicle_id: int,
    vehicle_data: VehicleUpdate,
    owner_id: str = Query(min_length=1, max_length=100),
):
    with SessionLocal() as session:
        statement = select(Vehicle).where(
            Vehicle.id == vehicle_id,
            Vehicle.owner_id == owner_id,
        )
        vehicle = session.scalar(statement)

        if vehicle is None:
            raise HTTPException(status_code=404, detail="Vehicle not found")

        changes = vehicle_data.model_dump(exclude_unset=True)
        for field, value in changes.items():
            setattr(vehicle, field, value)

        session.commit()
        session.refresh(vehicle)
        return vehicle


@router.delete(
    "/{vehicle_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_vehicle(
    vehicle_id: int,
    owner_id: str = Query(min_length=1, max_length=100),
):
    with SessionLocal() as session:
        statement = select(Vehicle).where(
            Vehicle.id == vehicle_id,
            Vehicle.owner_id == owner_id,
        )
        vehicle = session.scalar(statement)

        if vehicle is None:
            raise HTTPException(status_code=404, detail="Vehicle not found")

        session.delete(vehicle)
        session.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)