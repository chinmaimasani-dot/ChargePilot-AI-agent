from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


VehicleType = Literal["2 wheeler", "3 wheeler", "4 wheeler"]
VehicleModel = Literal["SUV", "Sedan"]
ChargingType = Literal["DC", "AC"]


class VehicleCreate(BaseModel):
    owner_id: str = Field(min_length=1, max_length=100)
    vehicle_number: str = Field(min_length=1, max_length=30)
    vehicle_type: VehicleType
    company_name: str = Field(min_length=1, max_length=100)
    charging_capacity: float = Field(gt=0, description="Capacity in kWh")
    vehicle_model: VehicleModel
    charging_type: ChargingType
    year_of_manufacturing: int = Field(ge=1886, le=datetime.now().year)


class VehicleUpdate(BaseModel):
    vehicle_number: str | None = Field(default=None, min_length=1, max_length=30)
    vehicle_type: VehicleType | None = None
    company_name: str | None = Field(default=None, min_length=1, max_length=100)
    charging_capacity: float | None = Field(
        default=None, gt=0, description="Capacity in kWh"
    )
    vehicle_model: VehicleModel | None = None
    charging_type: ChargingType | None = None
    year_of_manufacturing: int | None = Field(
        default=None, ge=1886, le=datetime.now().year
    )


class VehicleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: str
    vehicle_number: str
    vehicle_type: VehicleType
    company_name: str
    charging_capacity: float
    vehicle_model: VehicleModel
    charging_type: ChargingType
    year_of_manufacturing: int
    created_at: datetime
    updated_at: datetime