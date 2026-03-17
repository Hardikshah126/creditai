"""Initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-03-09
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # users
    op.create_table(
        "users",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("phone", sa.String, unique=True, nullable=False),
        sa.Column("email", sa.String, unique=True, nullable=True),
        sa.Column("country", sa.String, nullable=False),
        sa.Column("hashed_password", sa.String, nullable=False),
        sa.Column("role", sa.Enum("applicant", "lender", name="user_role"), nullable=False, server_default="applicant"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    # submissions
    op.create_table(
        "submissions",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("user_id", sa.String, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.Enum("pending", "processing", "scored", "failed", name="submission_status"), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_submissions_user_id", "submissions", ["user_id"])

    # alternative_data
    op.create_table(
        "alternative_data",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("submission_id", sa.String, sa.ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("doc_type", sa.Enum("utility_bill", "rent_receipt", "mobile_recharge", "transaction_statement", name="doc_type"), nullable=False),
        sa.Column("file_name", sa.String, nullable=False),
        sa.Column("file_path", sa.String, nullable=False),
        sa.Column("file_size_bytes", sa.Float, nullable=True),
        sa.Column("mime_type", sa.String, nullable=True),
        sa.Column("extracted_text", sa.Text, nullable=True),
        sa.Column("extracted_features", sa.Text, nullable=True),
        sa.Column("confidence_score", sa.Float, nullable=True),
        sa.Column("processing_status", sa.Enum("uploaded", "processing", "extracted", "failed", name="data_processing_status"), server_default="uploaded"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_alt_data_submission_id", "alternative_data", ["submission_id"])

    # agent_conversations
    op.create_table(
        "agent_conversations",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("submission_id", sa.String, sa.ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.Enum("ai", "user", name="conversation_role"), nullable=False),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("chips", sa.Text, nullable=True),
        sa.Column("turn_index", sa.String, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_conversations_submission_id", "agent_conversations", ["submission_id"])

    # credit_reports
    op.create_table(
        "credit_reports",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("submission_id", sa.String, sa.ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("score", sa.Integer, nullable=False),
        sa.Column("risk_tier", sa.Enum("low", "medium", "high", name="risk_tier"), nullable=False),
        sa.Column("model_version", sa.String, nullable=False, server_default="xgb_v1"),
        sa.Column("features_json", sa.Text, nullable=True),
        sa.Column("breakdown_json", sa.Text, nullable=True),
        sa.Column("summary_text", sa.Text, nullable=True),
        sa.Column("positive_signals_json", sa.Text, nullable=True),
        sa.Column("improvement_areas_json", sa.Text, nullable=True),
        sa.Column("share_token", sa.String, unique=True, nullable=True),
        sa.Column("is_shared_with_lender", sa.Boolean, server_default="false"),
        sa.Column("pdf_path", sa.String, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_reports_submission_id", "credit_reports", ["submission_id"])
    op.create_index("ix_reports_share_token", "credit_reports", ["share_token"])

    # lender_decisions
    op.create_table(
        "lender_decisions",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("report_id", sa.String, sa.ForeignKey("credit_reports.id", ondelete="CASCADE"), nullable=False),
        sa.Column("lender_id", sa.String, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("decision", sa.Enum("approved", "declined", "manual_review", name="lender_decision_type"), nullable=False),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_decisions_report_id", "lender_decisions", ["report_id"])


def downgrade():
    op.drop_table("lender_decisions")
    op.drop_table("credit_reports")
    op.drop_table("agent_conversations")
    op.drop_table("alternative_data")
    op.drop_table("submissions")
    op.drop_table("users")
