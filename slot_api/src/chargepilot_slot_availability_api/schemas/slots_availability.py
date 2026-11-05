from pydantic import BaseModel, ConfigDict, Field


class SlotAvailabilityCreate(BaseModel):
    station_id: int = Field(gt=0)
    two_wheeler_slots_count: int = Field(default=0, ge=0)
    three_wheeler_slots_count: int = Field(default=0, ge=0)
    four_wheeler_slots_count: int = Field(default=0, ge=0)


class SlotAvailabilityUpdate(BaseModel):
    two_wheeler_slots_count: int = Field(default=None, ge=0)
    three_wheeler_slots_count: int = Field(default=None, ge=0)
    four_wheeler_slots_count: int = Field(default=None, ge=0)


class SlotAvailabilityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    station_id: int
    two_wheeler_slots_count: int
    three_wheeler_slots_count: int
    four_wheeler_slots_count: int
