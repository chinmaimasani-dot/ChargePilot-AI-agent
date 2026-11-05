from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AddressCreate(BaseModel):
    hno: str | None = Field(default=None, max_length=50)

    street: str = Field(min_length=1, max_length=255)
    city: str = Field(min_length=1, max_length=100)
    state: str = Field(min_length=1, max_length=100)
    postal_code: str = Field(min_length=1, max_length=20)
    country: str = Field(min_length=1, max_length=100)

    lat: float | None = Field(default=None, ge=-90, le=90)
    long: float | None = Field(default=None, ge=-180, le=180)


class AddressUpdate(BaseModel):
    hno: str | None = Field(default=None, max_length=50)

    street: str | None = Field(default=None, min_length=1, max_length=255)
    city: str | None = Field(default=None, min_length=1, max_length=100)
    state: str | None = Field(default=None, min_length=1, max_length=100)
    postal_code: str | None = Field(default=None, min_length=1, max_length=20)
    country: str | None = Field(default=None, min_length=1, max_length=100)

    lat: float | None = Field(default=None, ge=-90, le=90)
    long: float | None = Field(default=None, ge=-180, le=180)


class AddressResponse(BaseModel):
    id: int
    hno: str | None

    street: str
    city: str
    state: str
    postal_code: str
    country: str

    lat: float | None
    long: float | None

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
    