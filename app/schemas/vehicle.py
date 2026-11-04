from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class VehicleCreate(BaseModel):
    # Temporary until Member 1's authentication is connected.
    owner_id: str = Field(min_length=1, max_length=100)

    make: str = Field(min_length=1, max_length=80)
    model: str = Field(min_length=1, max_length=100)
    model_year: int = Field(ge=1886, le=2100)

    battery_capacity_kwh: float = Field(gt=0)
    connector_type: str = Field(min_length=1, max_length=50)
    max_charging_power_kw: float = Field(gt=0)


class VehicleUpdate(BaseModel):
    make: str | None = Field(default=None, min_length=1, max_length=80)
    model: str | None = Field(default=None, min_length=1, max_length=100)
    model_year: int | None = Field(default=None, ge=1886, le=2100)

    battery_capacity_kwh: float | None = Field(default=None, gt=0)
    connector_type: str | None = Field(default=None, min_length=1, max_length=50)
    max_charging_power_kw: float | None = Field(default=None, gt=0)


class VehicleRead(BaseModel):
    id: int
    owner_id: str
    make: str
    model: str
    model_year: int
    battery_capacity_kwh: float
    connector_type: str
    max_charging_power_kw: float
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)