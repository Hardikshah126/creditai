import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.models.submission import Submission
from app.models.agent_conversation import AgentConversation
from app.core.security import get_current_user
from app.schemas.conversation import ChatReplyRequest, ChatReplyResponse, ConversationHistoryResponse, ChatMessage
from app.services.agent_service import (
    get_missing_features,
    get_next_question,
    extract_features_from_conversation,
    REQUIRED_FEATURES,
)

router = APIRouter(prefix="/chat", tags=["chat"])


def _get_aggregated_features(submission: Submission) -> dict:
    """Merge all extracted features from documents into one dict."""
    features = {}
    for doc in submission.documents:
        if doc.extracted_features:
            try:
                doc_features = json.loads(doc.extracted_features)
                features.update(doc_features)
            except json.JSONDecodeError:
                pass
    return features


def _get_next_turn_index(submission_id: str, db: Session) -> int:
    count = db.query(AgentConversation).filter(
        AgentConversation.submission_id == submission_id
    ).count()
    return count


@router.post("/start", response_model=ChatReplyResponse)
def start_conversation(
    submission_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Start the AI conversation for a submission.
    Call after /analyze — the agent will ask questions for any missing features.
    """
    submission = db.query(Submission).filter(
        Submission.id == submission_id,
        Submission.user_id == current_user.id,
    ).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    doc_features = _get_aggregated_features(submission)
    missing = get_missing_features(doc_features)

    ai_message, chips, is_complete = get_next_question(missing, [], current_user.name)

    # Save AI's opening message
    turn_idx = _get_next_turn_index(submission_id, db)
    msg = AgentConversation(
        submission_id=submission_id,
        role="ai",
        message=ai_message,
        chips=json.dumps(chips) if chips else None,
        turn_index=str(turn_idx),
    )
    db.add(msg)
    db.commit()

    return ChatReplyResponse(
        submission_id=submission_id,
        ai_message=ai_message,
        chips=chips,
        is_complete=is_complete,
        turn_index=turn_idx,
    )


@router.post("/reply", response_model=ChatReplyResponse)
def reply(
    body: ChatReplyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Send a user reply and get the next AI question.
    When is_complete=True, call POST /reports/{submission_id} to generate the score.
    """
    submission = db.query(Submission).filter(
        Submission.id == body.submission_id,
        Submission.user_id == current_user.id,
    ).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    # Save user message
    turn_idx = _get_next_turn_index(body.submission_id, db)
    user_msg = AgentConversation(
        submission_id=body.submission_id,
        role="user",
        message=body.message,
        turn_index=str(turn_idx),
    )
    db.add(user_msg)
    db.commit()

    # Determine what's still missing
    doc_features = _get_aggregated_features(submission)

    # Get all user answers so far to figure out which features are covered
    user_turns = (
        db.query(AgentConversation)
        .filter(
            AgentConversation.submission_id == body.submission_id,
            AgentConversation.role == "user",
        )
        .order_by(AgentConversation.turn_index)
        .all()
    )

    # Mark features as answered by conversation
    answered_count = len(user_turns)
    still_missing = [f for f in REQUIRED_FEATURES if doc_features.get(f) is None]
    remaining_missing = still_missing[answered_count:]

    history = (
        db.query(AgentConversation)
        .filter(AgentConversation.submission_id == body.submission_id)
        .order_by(AgentConversation.turn_index)
        .all()
    )
    history_dicts = [{"role": m.role, "message": m.message} for m in history]

    ai_message, chips, is_complete = get_next_question(
        remaining_missing, history_dicts, current_user.name
    )

    # Save AI response
    turn_idx2 = _get_next_turn_index(body.submission_id, db)
    ai_msg = AgentConversation(
        submission_id=body.submission_id,
        role="ai",
        message=ai_message,
        chips=json.dumps(chips) if chips else None,
        turn_index=str(turn_idx2),
    )
    db.add(ai_msg)
    db.commit()

    return ChatReplyResponse(
        submission_id=body.submission_id,
        ai_message=ai_message,
        chips=chips,
        is_complete=is_complete,
        turn_index=turn_idx2,
    )


@router.get("/{submission_id}/history", response_model=ConversationHistoryResponse)
def get_conversation_history(
    submission_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    submission = db.query(Submission).filter(
        Submission.id == submission_id,
        Submission.user_id == current_user.id,
    ).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    messages = (
        db.query(AgentConversation)
        .filter(AgentConversation.submission_id == submission_id)
        .order_by(AgentConversation.turn_index)
        .all()
    )

    return ConversationHistoryResponse(
        submission_id=submission_id,
        messages=[
            ChatMessage(
                role=m.role,
                message=m.message,
                chips=json.loads(m.chips) if m.chips else None,
                turn_index=int(m.turn_index),
                created_at=m.created_at,
            )
            for m in messages
        ],
    )
