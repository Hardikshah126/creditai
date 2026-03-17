from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class SubmissionCreate(BaseModel):
    pass  # created server-side from auth context


class DocumentResponse(BaseModel):
    id: str
    doc_type: str
    file_name: str
    file_size_bytes: Optional[float]
    processing_status: str
    confidence_score: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


class SubmissionResponse(BaseModel):
    id: str
    status: str
    created_at: datetime
    updated_at: datetime
    documents: List[DocumentResponse] = []

    class Config:
        from_attributes = True


class AnalyzeRequest(BaseModel):
    submission_id: str
