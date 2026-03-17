from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.db.base import get_db
from app.models.user import User
from app.models.submission import Submission
from app.models.document import Document
from app.models.conversation import ConversationMessage
from app.models.report import CreditReport
from app.core.security import get_current_user
from app.api.routes.submissions import _time_ago

router = APIRouter(prefix="/history", tags=["history"])


@router.get("/")
async def get_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    events = []

    # Account creation
    events.append({
        "event_type": "account_created",
        "action": "Account created",
        "detail": "Profile set up successfully",
        "created_at": current_user.created_at.isoformat(),
    })

    # All submissions
    subs_result = await db.execute(
        select(Submission)
        .where(Submission.user_id == current_user.id)
        .order_by(Submission.created_at)
    )
    submissions = subs_result.scalars().all()

    for sub in submissions:
        # Documents
        docs_result = await db.execute(
            select(Document)
            .where(Document.submission_id == sub.id)
            .order_by(Document.created_at)
        )
        for doc in docs_result.scalars().all():
            size_str = _fmt_size(doc.file_size_bytes or 0)
            events.append({
                "event_type": "document_uploaded",
                "action": f"{doc.doc_type.replace('_', ' ').title()} uploaded",
                "detail": f"{doc.original_filename} · {size_str}",
                "created_at": doc.created_at.isoformat(),
            })

        # Chat completed
        msgs_result = await db.execute(
            select(ConversationMessage)
            .where(
                ConversationMessage.submission_id == sub.id,
                ConversationMessage.role == "ai",
                ConversationMessage.target_feature == None,  # noqa: E711
            )
            .order_by(desc(ConversationMessage.created_at))
            .limit(1)
        )
        last_msg = msgs_result.scalar_one_or_none()
        if last_msg:
            events.append({
                "event_type": "chat_completed",
                "action": "AI questionnaire completed",
                "detail": "Gap-fill conversation finished",
                "created_at": last_msg.created_at.isoformat(),
            })

        # Report generated
        rep_result = await db.execute(
            select(CreditReport).where(CreditReport.submission_id == sub.id)
        )
        report = rep_result.scalar_one_or_none()
        if report:
            events.append({
                "event_type": "score_generated",
                "action": "Credit score generated",
                "detail": f"Score: {report.score} · {report.risk_tier.value.title()} Risk",
                "created_at": report.created_at.isoformat(),
            })

    # Sort newest first
    events.sort(key=lambda e: e["created_at"], reverse=True)
    return events


def _fmt_size(b: int) -> str:
    if b < 1024:
        return f"{b} B"
    if b < 1_048_576:
        return f"{b / 1024:.1f} KB"
    return f"{b / 1_048_576:.1f} MB"