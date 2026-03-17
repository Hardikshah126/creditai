from __future__ import annotations
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class ChatMessageIn(BaseModel):
    content: str


class ChatMessageOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    role: str           # "ai" | "user"
    content: str
    chips: Optional[List[str]] = None   # quick-reply options (synthesised, not stored)
    created_at: datetime


class ConversationOut(BaseModel):
    submission_id: int
    messages: List[ChatMessageOut]
    is_complete: bool   # True once all gap-fill questions answered
