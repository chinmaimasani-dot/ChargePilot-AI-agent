from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

UserType = Literal["staff", "customer", "admin"]


class UserCreate(BaseModel):
    user_type: UserType
    name: str = Field(min_length=4, max_length=255)
    mobile: str = Field(pattern=r"^\d{10}$")
    dob: date = Field(serialization_format="%Y-%m-%d")
    email: EmailStr = Field(min_length=4, max_length=255)


class UserUpdate(BaseModel):
    user_type: UserType | None = None
    name: str | None = Field(default=None, min_length=4, max_length=255)
    mobile: str | None = Field(default=None, pattern=r"^\d{10}$")
    dob: date | None = Field(default=None, serialization_format="%Y-%m-%d")
    email: EmailStr | None = Field(default=None, min_length=4, max_length=255)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_type: UserType
    name: str
    mobile: str
    dob: date
    email: EmailStr
    created_at: datetime
    updated_at: datetime
