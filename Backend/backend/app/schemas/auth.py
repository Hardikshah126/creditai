from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime


class SignupRequest(BaseModel):
    name: str
    phone: str
    country: str
    password: str
    email: Optional[EmailStr] = None
    role: str = "applicant"  # "applicant" | "lender"

    @field_validator("phone")
    @classmethod
    def phone_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Phone number is required")
        return v.strip()

    @field_validator("password")
    @classmethod
    def password_length(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class LoginRequest(BaseModel):
    phone: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    name: str
    role: str


class UserResponse(BaseModel):
    id: str
    name: str
    phone: str
    email: Optional[str]
    country: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True
