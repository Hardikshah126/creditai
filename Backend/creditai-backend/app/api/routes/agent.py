from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.base import get_db
from app.models.user import User
from app.models.submission import Submission, SubmissionStatus
from app.models.document import Document
from app.models.conversation import ConversationMessage
from app.schemas.agent import ChatMessageIn, ChatMessageOut, ConversationOut
from app.core.security import get_current_user
from app.services import agent_service

router = APIRouter(prefix="/agent", tags=["agent"])


async def _get_submission(submission_id: int, user: User, db: AsyncSession) -> Submission:
    result = await db.execute(
        select(Submission)
        .options(selectinload(Submission.messages))
        .where(
            Submission.id == submission_id,
            Submission.user_id == user.id,
        )
    )
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Submission not found")
    return sub


@router.post("/{submission_id}/message", response_model=ChatMessageOut)
async def send_message(
    submission_id: int,
    body: ChatMessageIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sub = await _get_submission(submission_id, current_user, db)
    first_name = current_user.name.split()[0]

    # ── Step 1: First message — extract docs then start conversation ──────────
    if sub.status == SubmissionStatus.DOCUMENTS_UPLOADED and not sub.messages:
        docs_result = await db.execute(
            select(Document).where(Document.submission_id == submission_id)
        )
        docs = docs_result.scalars().all()
        doc_texts = [
            {"doc_type": d.doc_type, "text": d.extracted_text or d.original_filename}
            for d in docs
        ]

        sub.status = SubmissionStatus.ANALYZING
        await db.flush()

        # Extract features from documents
        features = await agent_service.extract_features_from_documents(doc_texts)
        sub.extracted_features = json.dumps(features)
        sub.status = SubmissionStatus.AWAITING_CHAT

        # Determine first question to ask
        next_feature = agent_service.get_next_missing_feature(features)
        doc_context = agent_service._build_doc_context(features)

        # Generate natural greeting + first question via Gemini
        message = await agent_service.generate_natural_response(
            previous_feature=None,
            previous_answer=None,
            next_feature=next_feature,
            user_first_name=first_name,
            doc_context=doc_context,
            is_first_message=True,
        )

        ai_msg = ConversationMessage(
            submission_id=submission_id,
            role="ai",
            content=message,
            target_feature=next_feature,
        )
        db.add(ai_msg)

        if next_feature is None:
            sub.status = SubmissionStatus.SCORING

        await db.commit()
        chips = agent_service.get_chips_for_feature(next_feature)
        return _to_out(ai_msg, chips=chips)

    # ── Step 2: Ongoing conversation ──────────────────────────────────────────
    if sub.status == SubmissionStatus.AWAITING_CHAT:
        features = json.loads(sub.extracted_features or "{}")

        # Find which feature the last AI message was asking about
        msgs_result = await db.execute(
            select(ConversationMessage)
            .where(ConversationMessage.submission_id == submission_id)
            .order_by(ConversationMessage.created_at.desc())
            .limit(10)
        )
        recent_msgs = msgs_result.scalars().all()
        last_ai_with_feature = next(
            (m for m in recent_msgs if m.role == "ai" and m.target_feature), None
        )

        # Save user message
        user_msg = ConversationMessage(
            submission_id=submission_id,
            role="user",
            content=body.content,
        )
        db.add(user_msg)

        # Parse and store the answer using Python (reliable)
        answered_feature = None
        if last_ai_with_feature and last_ai_with_feature.target_feature:
            answered_feature = last_ai_with_feature.target_feature
            parsed = agent_service.parse_user_answer(answered_feature, body.content)
            if parsed is not None:
                features[answered_feature] = parsed
                sub.extracted_features = json.dumps(features)

        # Find next unanswered feature
        next_feature = agent_service.get_next_missing_feature(features)
        doc_context = agent_service._build_doc_context(features)

        # Generate natural response via Gemini
        message = await agent_service.generate_natural_response(
            previous_feature=answered_feature,
            previous_answer=body.content,
            next_feature=next_feature,
            user_first_name=first_name,
            doc_context=doc_context,
            is_first_message=False,
        )

        ai_msg = ConversationMessage(
            submission_id=submission_id,
            role="ai",
            content=message,
            target_feature=next_feature,
        )
        db.add(ai_msg)

        if next_feature is None:
            sub.status = SubmissionStatus.SCORING

        await db.commit()
        chips = agent_service.get_chips_for_feature(next_feature)
        return _to_out(ai_msg, chips=chips)

    # ── Already completed ─────────────────────────────────────────────────────
    fallback = ConversationMessage(
        submission_id=submission_id,
        role="ai",
        content="Your score is already being generated. Check the Report tab shortly.",
    )
    db.add(fallback)
    await db.commit()
    return _to_out(fallback)


@router.get("/{submission_id}/conversation", response_model=ConversationOut)
async def get_conversation(
    submission_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sub = await _get_submission(submission_id, current_user, db)

    msgs_result = await db.execute(
        select(ConversationMessage)
        .where(ConversationMessage.submission_id == submission_id)
        .order_by(ConversationMessage.created_at)
    )
    msgs = msgs_result.scalars().all()

    is_complete = sub.status in (SubmissionStatus.SCORING, SubmissionStatus.COMPLETED)

    return ConversationOut(
        submission_id=submission_id,
        messages=[_to_out(m) for m in msgs],
        is_complete=is_complete,
    )


def _to_out(msg: ConversationMessage, chips: list | None = None) -> ChatMessageOut:
    return ChatMessageOut(
        id=msg.id,
        role=msg.role,
        content=msg.content,
        chips=chips,
        created_at=msg.created_at,
    )