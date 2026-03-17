import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship

from app.db.session import Base


class AgentConversation(Base):
    __tablename__ = "agent_conversations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    submission_id = Column(String, ForeignKey("submissions.id"), nullable=False)
    role = Column(Enum("ai", "user", name="conversation_role"), nullable=False)
    message = Column(Text, nullable=False)
    # JSON array of quick-reply chip options (optional, for AI turns)
    chips = Column(Text, nullable=True)
    turn_index = Column(String, nullable=False, default="0")  # ordering
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    submission = relationship("Submission", back_populates="conversations")

    def __repr__(self):
        return f"<AgentConversation id={self.id} role={self.role}>"
