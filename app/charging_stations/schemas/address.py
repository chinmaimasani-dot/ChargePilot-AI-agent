
from pydantic import BaseModel, ConfigDict, Field


class AddressCreate(BaseModel):
    street: str = Field(min_length=1, max_length=255)
    city: str = Field(min_length=1, max_length=100)
    state: str = Field(min_length=1, max_length=100)
    postal_code: str = Field(min_length=1, max_length=20)
    country: str = Field(min_length=1, max_length=100)


class AddressResponse(BaseModel):
    id: int
    street: str
    city: str
    state: str
    postal_code: str
    country: str

    model_config = ConfigDict(from_attributes=True)
