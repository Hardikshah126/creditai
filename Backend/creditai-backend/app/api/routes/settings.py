from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr

from app.db.base import get_db
from app.models.user import User
from app.schemas.auth import UserOut
from app.core.security import get_current_user

router = APIRouter(prefix="/settings", tags=["settings"])


class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    country: Optional[str] = None
    email: Optional[EmailStr] = None


@router.patch("/profile", response_model=UserOut)
async def update_profile(
    body: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.name:
        current_user.name = body.name
    if body.phone:
        current_user.phone = body.phone
    if body.country:
        current_user.country = body.country
    if body.email is not None:
        current_user.email = body.email
    await db.flush()
    return UserOut.model_validate(current_user)
