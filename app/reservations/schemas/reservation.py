
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


ReservationStatus = Literal["confirmed", "cancelled", "completed"]


class ReservationCreate(BaseModel):
    user_id: int = Field(gt=0)
    vehicle_id: int = Field(gt=0)
    station_id: int = Field(gt=0)
    start_time: datetime
    end_time: datetime

    @model_validator(mode="after")
    def validate_time_range(self):
        if self.end_time <= self.start_time:
            raise ValueError("End time must be later than start time")
        return self


class ReservationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    vehicle_id: int
    station_id: int
    start_time: datetime
    end_time: datetime
    status: ReservationStatus
    created_at: datetime
    updated_at: datetime
