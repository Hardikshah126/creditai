import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, Text, Float
from sqlalchemy.orm import relationship

from app.db.session import Base


class AlternativeData(Base):
    __tablename__ = "alternative_data"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    submission_id = Column(String, ForeignKey("submissions.id"), nullable=False)
    doc_type = Column(
        Enum(
            "utility_bill",
            "rent_receipt",
            "mobile_recharge",
            "transaction_statement",
            name="doc_type",
        ),
        nullable=False,
    )
    file_name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)       # local path or S3 key
    file_size_bytes = Column(Float, nullable=True)
    mime_type = Column(String, nullable=True)
    extracted_text = Column(Text, nullable=True)      # raw OCR / parsed text
    extracted_features = Column(Text, nullable=True)  # JSON string of structured features
    confidence_score = Column(Float, nullable=True)   # 0.0 – 1.0
    processing_status = Column(
        Enum("uploaded", "processing", "extracted", "failed", name="data_processing_status"),
        default="uploaded",
    )
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    submission = relationship("Submission", back_populates="documents")

    def __repr__(self):
        return f"<AlternativeData id={self.id} doc_type={self.doc_type}>"
