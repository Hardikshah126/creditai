import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship

from app.db.session import Base


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    status = Column(
        Enum("pending", "processing", "scored", "failed", name="submission_status"),
        default="pending",
        nullable=False,
    )
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="submissions")
    documents = relationship("AlternativeData", back_populates="submission", cascade="all, delete-orphan")
    conversations = relationship("AgentConversation", back_populates="submission", cascade="all, delete-orphan")
    report = relationship("CreditReport", back_populates="submission", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Submission id={self.id} status={self.status}>"
