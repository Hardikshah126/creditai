from __future__ import annotations
import enum
from datetime import datetime, timezone
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import String, DateTime, ForeignKey, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.document import Document
    from app.models.conversation import ConversationMessage
    from app.models.report import CreditReport


class SubmissionStatus(str, enum.Enum):
    PENDING = "pending"                        # just created
    DOCUMENTS_UPLOADED = "documents_uploaded"  # at least one file saved
    ANALYZING = "analyzing"                    # LLM extraction running
    AWAITING_CHAT = "awaiting_chat"            # needs gap-fill conversation
    SCORING = "scoring"                        # ML model running
    COMPLETED = "completed"                    # report ready
    FAILED = "failed"


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    status: Mapped[SubmissionStatus] = mapped_column(
        SAEnum(SubmissionStatus), default=SubmissionStatus.PENDING
    )
    # Extracted ML features stored as JSON string
    extracted_features: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user: Mapped["User"] = relationship(back_populates="submissions")
    documents: Mapped[List["Document"]] = relationship(
        back_populates="submission", cascade="all, delete-orphan"
    )
    messages: Mapped[List["ConversationMessage"]] = relationship(
        back_populates="submission",
        cascade="all, delete-orphan",
        order_by="ConversationMessage.created_at",
    )
    report: Mapped[Optional["CreditReport"]] = relationship(
        back_populates="submission", uselist=False
    )
