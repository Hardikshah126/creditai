import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship

from app.db.session import Base


class LenderDecision(Base):
    __tablename__ = "lender_decisions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    report_id = Column(String, ForeignKey("credit_reports.id"), nullable=False)
    lender_id = Column(String, ForeignKey("users.id"), nullable=False)
    decision = Column(
        Enum("approved", "declined", "manual_review", name="lender_decision_type"),
        nullable=False,
    )
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    report = relationship("CreditReport", back_populates="lender_decisions")
    lender = relationship("User")

    def __repr__(self):
        return f"<LenderDecision id={self.id} decision={self.decision}>"
