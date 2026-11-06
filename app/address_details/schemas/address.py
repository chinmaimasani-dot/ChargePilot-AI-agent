from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class AddressCreate(BaseModel):
    hno: str | None = Field(default=None, max_length=50)
    street_village: str = Field(min_length=1, max_length=150)
    city: str = Field(min_length=1, max_length=100)
    state: str = Field(min_length=1, max_length=100)
    pincode: str = Field(min_length=1, max_length=10)
    lat: float | None = Field(default=None, ge=-90, le=90)
    long: float | None = Field(default=None, ge=-180, le=180)


class AddressUpdate(BaseModel):
    hno: str | None = Field(default=None, max_length=50)
    street_village: str | None = Field(default=None, min_length=1, max_length=150)
    city: str | None = Field(default=None, min_length=1, max_length=100)
    state: str | None = Field(default=None, min_length=1, max_length=100)
    pincode: str | None = Field(default=None, min_length=1, max_length=10)
    lat: float | None = Field(default=None, ge=-90, le=90)
    long: float | None = Field(default=None, ge=-180, le=180)


class AddressResponse(BaseModel):
    id: int
    hno: str | None
    street_village: str
    city: str
    state: str
    pincode: str
    lat: float | None
    long: float | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
