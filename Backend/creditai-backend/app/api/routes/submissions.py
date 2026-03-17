from __future__ import annotations

import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.base import get_db
from app.core.security import get_current_user
from app.core.config import settings
from app.models.user import User
from app.models.submission import Submission, SubmissionStatus
from app.models.document import Document
from app.schemas.submission import SubmissionOut, DocumentOut, DashboardStats

router = APIRouter(prefix="/submissions", tags=["submissions"])

ALLOWED_MIME_TYPES = {
    "application/pdf", "image/jpeg", "image/jpg",
    "image/png", "text/csv", "application/csv",
}

DOC_TYPE_MAP = {
    "Utility Bill": "utility_bill", "Rent Receipt": "rent_receipt",
    "Mobile Recharge History": "mobile_recharge", "Transaction Statement": "transaction_statement",
    "utility": "utility_bill", "rent": "rent_receipt",
    "mobile": "mobile_recharge", "transaction": "transaction_statement",
}


@router.post("/", response_model=SubmissionOut, status_code=status.HTTP_201_CREATED)
async def create_submission(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sub = Submission(user_id=current_user.id, status=SubmissionStatus.PENDING)
    db.add(sub)
    await db.commit()
    await db.refresh(sub)
    result = await db.execute(
        select(Submission)
        .options(selectinload(Submission.documents))
        .where(Submission.id == sub.id)
    )
    return result.scalar_one()


@router.post("/{submission_id}/documents", response_model=DocumentOut)
async def upload_document(
    submission_id: int,
    file: UploadFile = File(...),
    doc_type: str = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Submission).where(
            Submission.id == submission_id,
            Submission.user_id == current_user.id,
        )
    )
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")

    mime = file.content_type or ""
    if mime not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {mime}")

    content = await file.read()
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(status_code=400, detail=f"File too large. Max {settings.MAX_UPLOAD_MB}MB")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    ext = os.path.splitext(file.filename or "file")[1] or ".bin"
    file_path = os.path.join(settings.UPLOAD_DIR, f"{uuid.uuid4()}{ext}")
    with open(file_path, "wb") as f:
        f.write(content)

    doc = Document(
        submission_id=submission_id,
        original_filename=file.filename or "upload",
        file_path=file_path,
        file_size_bytes=len(content),
        mime_type=mime,
        doc_type=DOC_TYPE_MAP.get(doc_type, "utility_bill"),
    )
    db.add(doc)
    sub.status = SubmissionStatus.DOCUMENTS_UPLOADED
    await db.commit()
    await db.refresh(doc)
    return doc


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Submission)
        .options(selectinload(Submission.documents), selectinload(Submission.report))
        .where(Submission.user_id == current_user.id)
        .order_by(Submission.created_at.desc())
        .limit(1)
    )
    latest = result.scalar_one_or_none()

    documents_uploaded = len(latest.documents) if latest else 0
    report_generated = False
    score = None
    risk_tier = None

    if latest and latest.report:
        report_generated = True
        score = latest.report.score
        risk_tier = latest.report.risk_tier

    pct = 20
    if documents_uploaded >= 1: pct += 30
    if documents_uploaded >= 2: pct += 20
    if report_generated: pct += 30

    activity = []
    if latest:
        activity.append({"action": "Created submission", "time": _time_ago(latest.created_at)})
        for doc in sorted(latest.documents, key=lambda d: d.created_at, reverse=True)[:3]:
            activity.append({"action": f"Uploaded {doc.doc_type.replace('_', ' ')}", "time": _time_ago(doc.created_at)})
    activity.append({"action": "Created account", "time": _time_ago(current_user.created_at)})

    return DashboardStats(
        name=current_user.name,
        country=current_user.country,
        profile_complete_pct=pct,
        documents_uploaded=documents_uploaded,
        report_generated=report_generated,
        score=score,
        risk_tier=risk_tier,
        latest_submission_id=latest.id if latest else None,
        recent_activity=activity[:5],
    )


@router.get("/{submission_id}", response_model=SubmissionOut)
async def get_submission(
    submission_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Submission)
        .options(selectinload(Submission.documents))
        .where(Submission.id == submission_id, Submission.user_id == current_user.id)
    )
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")
    return sub


def _time_ago(dt) -> str:
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    diff = now - dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else now - dt
    s = int(diff.total_seconds())
    if s < 60: return "just now"
    if s < 3600: return f"{s // 60} minutes ago"
    if s < 86400: return f"{s // 3600} hours ago"
    return f"{s // 86400} days ago"
