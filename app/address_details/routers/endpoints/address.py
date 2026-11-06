from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select
from app.address_details.api.deps import DbSession
from app.address_details.models.address import AddressDetails
from app.address_details.schemas.address import AddressCreate, AddressUpdate, AddressResponse

router = APIRouter(prefix="/addresses", tags=["Address Details"])


@router.post("/", response_model=AddressResponse, status_code=status.HTTP_201_CREATED)
def create_address(payload: AddressCreate, db: DbSession):
    address = AddressDetails(**payload.model_dump())
    db.add(address)
    db.commit()
    db.refresh(address)
    return address


@router.get("/", response_model=list[AddressResponse])
def get_all_addresses(
    db: DbSession,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
):
    statement = select(AddressDetails).order_by(AddressDetails.id).offset(skip).limit(limit)
    return db.scalars(statement).all()


@router.get("/{address_id}", response_model=AddressResponse)
def get_address_by_id(address_id: int, db: DbSession):
    address = db.get(AddressDetails, address_id)
    if address is None:
        raise HTTPException(status_code=404, detail="Address not found")
    return address


@router.put("/{address_id}", response_model=AddressResponse)
def update_address(address_id: int, payload: AddressUpdate, db: DbSession):
    address = db.get(AddressDetails, address_id)
    if address is None:
        raise HTTPException(status_code=404, detail="Address not found")

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        if value is None and field not in {"hno", "lat", "long"}:
            raise HTTPException(status_code=422, detail=f"{field} cannot be null")
        setattr(address, field, value)

    db.commit()
    db.refresh(address)
    return address


@router.delete("/{address_id}", status_code=status.HTTP_200_OK)
def delete_address(address_id: int, db: DbSession):
    address = db.get(AddressDetails, address_id)
    if address is None:
        raise HTTPException(status_code=404, detail="Address not found")
    db.delete(address)
    db.commit()
    return {"message": "Address deleted successfully", "address_id": address_id}
