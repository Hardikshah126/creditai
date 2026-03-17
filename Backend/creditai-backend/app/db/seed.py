"""
Seed the database with demo data that mirrors dummy.ts exactly.
Run: python -m app.db.seed
"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone, timedelta

from sqlalchemy import text

from app.db.base import engine, Base, AsyncSessionLocal
from app.core.security import hash_password

# Import all models for table creation
from app.models.user import User
from app.models.submission import Submission, SubmissionStatus
from app.models.document import Document
from app.models.conversation import ConversationMessage
from app.models.report import CreditReport, RiskTier


DEMO_APPLICANTS = [
    {
        "name": "Amara Osei",
        "phone": "+233241234567",
        "country": "Ghana",
        "email": "amara@example.com",
        "score": 72,
        "risk_tier": "medium",
        "sources": ["Utility Bill", "Mobile Recharge"],
        "days_ago": 0,
    },
    {
        "name": "Priya Nair",
        "phone": "+919876543210",
        "country": "India",
        "email": "priya@example.com",
        "score": 85,
        "risk_tier": "low",
        "sources": ["Rent Receipt", "Utility Bill", "Transaction Statement"],
        "days_ago": 1,
    },
    {
        "name": "Carlos Mendez",
        "phone": "+5215551234567",
        "country": "Mexico",
        "email": "carlos@example.com",
        "score": 48,
        "risk_tier": "high",
        "sources": ["Mobile Recharge"],
        "days_ago": 2,
    },
    {
        "name": "Fatima Al-Rashid",
        "phone": "+2348012345678",
        "country": "Nigeria",
        "email": "fatima@example.com",
        "score": 91,
        "risk_tier": "low",
        "sources": ["Utility Bill", "Rent Receipt", "Mobile Recharge"],
        "days_ago": 3,
    },
    {
        "name": "Budi Santoso",
        "phone": "+6281234567890",
        "country": "Indonesia",
        "email": "budi@example.com",
        "score": 63,
        "risk_tier": "medium",
        "sources": ["Transaction Statement", "Utility Bill"],
        "days_ago": 4,
    },
]

SCORE_BREAKDOWN = [
    {"title": "Utility Payments", "icon": "Zap", "contribution": 24,
     "strength": "strong", "percent": 80, "detail": "18 months of consistent payments"},
    {"title": "Mobile Recharge", "icon": "Smartphone", "contribution": 18,
     "strength": "good", "percent": 65, "detail": "Regular monthly recharges detected"},
    {"title": "Transaction Activity", "icon": "ArrowLeftRight", "contribution": 16,
     "strength": "moderate", "percent": 55, "detail": "Some gaps in transaction history"},
    {"title": "Income Stability", "icon": "TrendingUp", "contribution": 14,
     "strength": "moderate", "percent": 50, "detail": "Self-reported stable income"},
]

POSITIVE_SIGNALS = [
    "Paid electricity bills consistently for 18 months",
    "Mobile recharge shows regular spending behavior",
    "No large unexplained gaps in payment history",
]

IMPROVEMENT_AREAS = [
    "Upload more months of transaction history",
    "Add a second utility bill type",
    "Consistent income documentation would help",
]

DEMO_FEATURES = {
    "utility_payment_streak_months": 18,
    "utility_on_time_rate": 0.9,
    "avg_monthly_recharge_usd": 12.0,
    "recharge_consistency_score": 0.75,
    "rent_payment_consistency": 0.8,
    "upi_tx_frequency_per_month": 8.0,
    "avg_monthly_tx_volume_usd": 120.0,
    "income_stability_score": 0.65,
    "employment_type": 2,
    "num_dependents": 1,
    "had_informal_loan": 0,
    "data_completeness_score": 0.85,
}


async def run():
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Tables created")

    async with AsyncSessionLocal() as db:
        # Idempotency check
        result = await db.execute(text("SELECT COUNT(*) FROM users"))
        if result.scalar() > 0:
            print("ℹ️  Data already exists – skipping seed")
            return

        # ── Lender ────────────────────────────────────────────────────────────
        lender = User(
            name="Apex Lending Officer",
            phone="+10000000001",
            country="USA",
            email="lender@apexlending.com",
            hashed_password=hash_password("lender1234"),
            role="lender",
            organization="Apex Lending Co.",
        )
        db.add(lender)
        await db.flush()

        # ── Applicants ────────────────────────────────────────────────────────
        for a in DEMO_APPLICANTS:
            created_at = datetime.now(timezone.utc) - timedelta(days=a["days_ago"])

            user = User(
                name=a["name"],
                phone=a["phone"],
                country=a["country"],
                email=a["email"],
                hashed_password=hash_password("demo1234"),
                role="applicant",
                created_at=created_at,
            )
            db.add(user)
            await db.flush()

            sub = Submission(
                user_id=user.id,
                status=SubmissionStatus.COMPLETED,
                extracted_features=json.dumps(DEMO_FEATURES),
                created_at=created_at,
            )
            db.add(sub)
            await db.flush()

            for source in a["sources"]:
                doc = Document(
                    submission_id=sub.id,
                    original_filename=f"{source.lower().replace(' ', '_')}.pdf",
                    file_path=f"uploads/demo/{source.lower().replace(' ', '_')}.pdf",
                    file_size_bytes=204_800,
                    mime_type="application/pdf",
                    doc_type=source,
                    extracted_text=f"Sample extracted text for {source}.",
                    extraction_confidence=0.92,
                    created_at=created_at,
                )
                db.add(doc)

            # Add a demo conversation
            for role, content in [
                ("ai", f"Hi {a['name'].split()[0]} 👋 I've reviewed your uploaded documents."),
                ("user", "Monthly income around $600"),
                ("ai", "What best describes your work?", ),
                ("user", "Self-employed"),
                ("ai", "Perfect! Generating your score now…"),
            ]:
                msg = ConversationMessage(
                    submission_id=sub.id, role=role, content=content,
                    created_at=created_at,
                )
                db.add(msg)

            report = CreditReport(
                submission_id=sub.id,
                user_id=user.id,
                score=a["score"],
                risk_tier=RiskTier(a["risk_tier"]),
                ml_probability=round(a["score"] / 100, 4),
                score_breakdown=json.dumps(SCORE_BREAKDOWN),
                positive_signals=json.dumps(POSITIVE_SIGNALS),
                improvement_areas=json.dumps(IMPROVEMENT_AREAS),
                report_text=(
                    f"{a['name']} demonstrates consistent financial behaviour based on "
                    f"alternative data sources including {', '.join(a['sources'])}. "
                    "Payment history shows reliability over an extended period."
                ),
                data_sources=json.dumps(a["sources"]),
                model_version="xgboost-v1",
                is_shared_with_lender=True,
                created_at=created_at,
            )
            db.add(report)

        await db.commit()
        print("✅ Demo data seeded")
        print()
        print("Demo credentials")
        print("  Applicant:  amara@example.com  /  demo1234")
        print("  Lender:     lender@apexlending.com  /  lender1234")


if __name__ == "__main__":
    asyncio.run(run())
