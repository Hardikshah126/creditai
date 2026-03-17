"""
Report Service
==============
India-specific: all currency shown in INR (₹).
1. generate_report_text() – Gemini writes human-readable report summary.
2. build_pdf()            – renders a PDF using reportlab.
3. derive_signals()       – builds positive_signals and improvement_areas lists.
"""
from __future__ import annotations

import io
import json
from typing import List

from google import genai
from app.core.config import settings

client = genai.Client(api_key=settings.GEMINI_API_KEY)

USD_TO_INR = 83  # 1 USD = 83 INR

REPORT_SYSTEM = """You are a friendly financial advisor writing a plain-English credit report
for an Indian user who has no formal credit history. Your tone is warm, encouraging, and clear.
Never use jargon. Use Indian context (rupees ₹, UPI payments, utility bills, etc).
Keep the report to 3-4 short paragraphs."""


async def generate_report_text(
    name: str,
    score: int,
    risk_tier: str,
    breakdown: list[dict],
    positive_signals: list[str],
    improvement_areas: list[str],
) -> str:
    prompt = f"""
Write a personal credit report for {name}, an Indian user.

Score: {score}/100  |  Risk tier: {risk_tier}

Score breakdown:
{json.dumps(breakdown, indent=2)}

Positive signals:
{json.dumps(positive_signals)}

Areas to improve:
{json.dumps(improvement_areas)}

Write 3-4 paragraphs explaining the score in plain English using Indian context
(mention UPI, utility bills, rupees ₹ where relevant). Be specific about what
the person did well and give one concrete action they can take to improve their score.
"""
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={"system_instruction": REPORT_SYSTEM},
        )
        return response.text.strip()
    except Exception:
        return (
            f"{name}, your credit score is {score}/100, placing you in the "
            f"{risk_tier} risk category. This score is based on your alternative "
            f"financial data including payment history and UPI transaction patterns."
        )


# ── Signal derivation ─────────────────────────────────────────────────────────

def derive_signals(features: dict, breakdown: list[dict]) -> tuple[list[str], list[str]]:
    positive: List[str] = []
    improve: List[str] = []

    streak = features.get("utility_payment_streak_months", 0) or 0
    util_rate = features.get("utility_on_time_rate", 0) or 0
    recharge = features.get("recharge_consistency_score", 0) or 0
    recharge_amt_usd = features.get("avg_monthly_recharge_usd", 0) or 0
    recharge_amt_inr = round(recharge_amt_usd * USD_TO_INR)
    rent = features.get("rent_payment_consistency", 0) or 0
    income = features.get("income_stability_score", 0) or 0
    tx_vol_usd = features.get("avg_monthly_tx_volume_usd", 0) or 0
    tx_vol_inr = round(tx_vol_usd * USD_TO_INR)
    tx_freq = features.get("upi_tx_frequency_per_month", 0) or 0

    if streak >= 12:
        positive.append(f"Paid utility bills consistently for {int(streak)} months")
    elif streak >= 6:
        positive.append(f"{int(streak)} months of utility payment history found")
    elif streak > 0:
        improve.append("Longer utility payment history would strengthen your score")
    else:
        improve.append("Start paying utility bills on time to build payment history")

    if util_rate >= 0.8:
        positive.append(f"{int(util_rate * 100)}% on-time utility payment rate")
    elif util_rate > 0:
        improve.append("Avoid late utility payments — they impact your score significantly")

    if recharge >= 0.7:
        if recharge_amt_inr > 0:
            positive.append(f"Regular mobile recharges — avg ₹{recharge_amt_inr}/month")
        else:
            positive.append("Regular monthly mobile recharge behaviour detected")
    else:
        improve.append("More consistent monthly recharges would improve your profile")

    if tx_freq >= 5:
        if tx_vol_inr > 0:
            positive.append(f"Active UPI usage — avg ₹{tx_vol_inr}/month in transactions")
        else:
            positive.append(f"{int(tx_freq)} UPI transactions/month shows active digital usage")
    elif tx_freq > 0:
        improve.append("Increasing your UPI/digital transaction frequency helps your profile")

    if rent >= 0.8:
        positive.append("Strong rent payment consistency")
    elif features.get("rent_payment_consistency") is not None:
        improve.append("Upload more rent receipts to document your payment history")

    if income >= 0.7:
        positive.append("Stable income reported")
    elif income > 0:
        improve.append("Consistent income documentation would help lenders assess your profile")

    completeness = features.get("data_completeness_score", 0.5) or 0.5
    if completeness < 0.8:
        improve.append("Upload additional document types (bank statement, rent receipt) to increase score confidence")

    if not positive:
        positive.append("Provided verifiable alternative financial data")
    if not improve:
        improve.append("Keep maintaining consistent payment behaviour")

    return positive[:4], improve[:3]


# ── Score breakdown builder ───────────────────────────────────────────────────

def build_score_breakdown(features: dict, score: int) -> list[dict]:
    """Build the 4 signal cards shown on the report page, with INR values."""

    streak = features.get("utility_payment_streak_months", 0) or 0
    util_rate = features.get("utility_on_time_rate", 0) or 0
    recharge_usd = features.get("avg_monthly_recharge_usd", 0) or 0
    recharge_inr = round(recharge_usd * USD_TO_INR)
    recharge_score = features.get("recharge_consistency_score", 0) or 0
    tx_freq = features.get("upi_tx_frequency_per_month", 0) or 0
    tx_vol_usd = features.get("avg_monthly_tx_volume_usd", 0) or 0
    tx_vol_inr = round(tx_vol_usd * USD_TO_INR)
    income = features.get("income_stability_score", 0) or 0

    def strength(val, thresholds=(0.3, 0.6, 0.8)):
        if val >= thresholds[2]: return "strong"
        if val >= thresholds[1]: return "good"
        if val >= thresholds[0]: return "moderate"
        return "weak"

    utility_pct = min(int((streak / 24) * 100), 100) if streak else int(util_rate * 100)
    recharge_pct = int(recharge_score * 100)
    tx_pct = min(int((tx_freq / 20) * 100), 100)
    income_pct = int(income * 100)

    return [
        {
            "title": "Utility Payments",
            "icon": "Zap",
            "contribution": round(score * 0.30),
            "strength": strength(util_rate),
            "percent": utility_pct,
            "detail": f"{int(streak)} months of payment history detected" if streak else "No utility payment history found",
        },
        {
            "title": "Mobile Recharge",
            "icon": "Smartphone",
            "contribution": round(score * 0.20),
            "strength": strength(recharge_score),
            "percent": recharge_pct,
            "detail": f"Avg ₹{recharge_inr}/month in recharges" if recharge_inr else "No recharge history detected",
        },
        {
            "title": "UPI & Transactions",
            "icon": "ArrowLeftRight",
            "contribution": round(score * 0.25),
            "strength": strength(tx_freq / 20),
            "percent": tx_pct,
            "detail": f"₹{tx_vol_inr}/month across {int(tx_freq)} UPI transactions" if tx_freq else "No transaction history detected",
        },
        {
            "title": "Income Stability",
            "icon": "TrendingUp",
            "contribution": round(score * 0.25),
            "strength": strength(income),
            "percent": income_pct,
            "detail": "Based on self-reported income and employment type",
        },
    ]


# ── PDF generation ────────────────────────────────────────────────────────────

def build_pdf(
    name: str,
    country: str,
    score: int,
    risk_tier: str,
    report_text: str,
    positive_signals: list[str],
    improvement_areas: list[str],
    report_id: str,
    generated_date: str,
) -> bytes:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.lib import colors
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        )

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4,
                                leftMargin=20*mm, rightMargin=20*mm,
                                topMargin=20*mm, bottomMargin=20*mm)
        styles = getSampleStyleSheet()
        BRAND = colors.HexColor("#6366F1")

        title_style = ParagraphStyle("title", parent=styles["Heading1"],
                                     textColor=BRAND, fontSize=22, spaceAfter=4)
        sub_style   = ParagraphStyle("sub", parent=styles["Normal"],
                                     textColor=colors.grey, fontSize=10)
        h2_style    = ParagraphStyle("h2", parent=styles["Heading2"],
                                     textColor=colors.HexColor("#111827"), fontSize=14,
                                     spaceBefore=12, spaceAfter=4)
        body_style  = ParagraphStyle("body", parent=styles["Normal"], fontSize=11,
                                     leading=16, spaceAfter=6)

        TIER_COLOR = {"low": "#10B981", "medium": "#F59E0B", "high": "#EF4444"}
        tier_color = colors.HexColor(TIER_COLOR.get(risk_tier.lower(), "#6366F1"))

        story = []
        story.append(Paragraph("CreditAI · Credit Report", title_style))
        story.append(Paragraph(f"Prepared for {name} · India · {generated_date}", sub_style))
        story.append(HRFlowable(width="100%", thickness=1, color=BRAND, spaceAfter=12))

        score_data = [
            [Paragraph(f"<b>{score}</b>", ParagraphStyle("score", fontSize=48,
                        textColor=tier_color, alignment=1)),
             Paragraph(f"<b>{risk_tier.upper()} RISK</b>",
                       ParagraphStyle("tier", fontSize=14, textColor=tier_color,
                                      alignment=1))],
            [Paragraph("out of 100", sub_style),
             Paragraph("Credit Risk Tier", sub_style)],
        ]
        t = Table(score_data, colWidths=[80*mm, 80*mm])
        t.setStyle(TableStyle([
            ("ALIGN",      (0, 0), (-1, -1), "CENTER"),
            ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
            ("BOX",        (0, 0), (-1, -1), 1, colors.HexColor("#E5E7EB")),
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F9FAFB")),
            ("TOPPADDING",    (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ]))
        story.append(t)
        story.append(Spacer(1, 12))

        story.append(Paragraph("Summary", h2_style))
        for para in report_text.split("\n\n"):
            if para.strip():
                story.append(Paragraph(para.strip(), body_style))

        story.append(Paragraph("Positive Signals", h2_style))
        for s in positive_signals:
            story.append(Paragraph(f"✓ {s}", body_style))

        story.append(Paragraph("Areas to Improve", h2_style))
        for a in improvement_areas:
            story.append(Paragraph(f"→ {a}", body_style))

        story.append(Spacer(1, 20))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
        story.append(Paragraph(
            f"Report ID: {report_id} · Generated by CreditAI India · Model: xgboost-v1",
            ParagraphStyle("footer", parent=styles["Normal"], fontSize=8, textColor=colors.grey)
        ))

        doc.build(story)
        return buf.getvalue()

    except Exception as e:
        return f"PDF generation failed: {e}".encode()