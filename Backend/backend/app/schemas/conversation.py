from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ChatMessage(BaseModel):
    role: str  # "ai" | "user"
    message: str
    chips: Optional[List[str]] = None
    turn_index: int
    created_at: datetime

    class Config:
        from_attributes = True


class ChatReplyRequest(BaseModel):
    submission_id: str
    message: str


class ChatReplyResponse(BaseModel):
    submission_id: str
    ai_message: str
    chips: Optional[List[str]] = None
    is_complete: bool = False   # True when all questions answered → triggers scoring
    turn_index: int


class ConversationHistoryResponse(BaseModel):
    submission_id: str
    messages: List[ChatMessage]
