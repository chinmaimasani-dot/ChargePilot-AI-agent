
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.charging_stations.schemas.address import AddressResponse


class ChargingStationCreate(BaseModel):
    address_id: int

    two_wheeler_slots_count: int = Field(default=100, ge=0)
    three_wheeler_slots_count: int = Field(default=0, ge=0)
    four_wheeler_slots_count: int = Field(default=0, ge=0)

    two_wheeler_cost: Decimal = Field(ge=0)
    three_wheeler_cost: Decimal = Field(ge=0)
    four_wheeler_cost: Decimal = Field(ge=0)

    is_active: bool = True


class ChargingStationUpdate(BaseModel):
    address_id: int | None = None

    two_wheeler_slots_count: int | None = Field(default=None, ge=0)
    three_wheeler_slots_count: int | None = Field(default=None, ge=0)
    four_wheeler_slots_count: int | None = Field(default=None, ge=0)

    two_wheeler_cost: Decimal | None = Field(default=None, ge=0)
    three_wheeler_cost: Decimal | None = Field(default=None, ge=0)
    four_wheeler_cost: Decimal | None = Field(default=None, ge=0)

    is_active: bool | None = None


class ChargingStationResponse(BaseModel):
    id: int
    address_id: int

    two_wheeler_slots_count: int
    three_wheeler_slots_count: int
    four_wheeler_slots_count: int

    two_wheeler_cost: Decimal
    three_wheeler_cost: Decimal
    four_wheeler_cost: Decimal

    is_active: bool
    address: AddressResponse

    model_config = ConfigDict(from_attributes=True)
