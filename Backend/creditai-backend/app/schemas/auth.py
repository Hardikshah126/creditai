from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator
import re


class SignupRequest(BaseModel):
    name: str
    phone: str
    country: str
    email: Optional[EmailStr] = None
    password: str

    @field_validator("password")
    @classmethod
    def password_length(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v


class LoginRequest(BaseModel):
    # accepts either phone or email
    identifier: str   # phone number or email
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class UserOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    phone: str
    country: str
    email: Optional[str]
    role: str
    organization: Optional[str]
