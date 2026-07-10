import re
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator

# Regular expression for password: 8+ chars, upper, lower, digit, and special char
PASSWORD_REGEX = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
)


class UserBase(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=100)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not PASSWORD_REGEX.match(v):
            raise ValueError(
                "Password must be at least 8 characters long, contain at least one uppercase letter, "
                "one lowercase letter, one number, and one special character."
            )
        return v


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    current_password: Optional[str] = None
    new_password: Optional[str] = None

    @field_validator("new_password")
    @classmethod
    def validate_new_password_strength(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not PASSWORD_REGEX.match(v):
            raise ValueError(
                "New password must be at least 8 characters long, contain at least one uppercase letter, "
                "one lowercase letter, one number, and one special character."
            )
        return v


class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserSimpleResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    name: str

    class Config:
        from_attributes = True
