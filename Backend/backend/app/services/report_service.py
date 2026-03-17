"""
Report generation service.
Uses Claude to write the human-readable credit report narrative
based on the score and extracted features.
"""
import json
import secrets
import anthropic

from app.core.config import settings

client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

REPORT_SYSTEM_PROMPT = """You are a fair and empathetic credit report writer.
Write a clear, plain-English credit report summary for an unbanked individual.
Be encouraging but honest. Avoid financial jargon. Keep the tone warm and accessible.
Return ONLY valid JSON — no markdown, no preamble."""


def generate_report_narrative(
    applicant_name: str,
    score: int,
    risk_tier: str,
    breakdown: list[dict],
    feature_vector: list[float],
) -> tuple[str, list[str], list[str]]:
    """
    Ask Claude to generate:
    - A 2–3 sentence summary of the score
    - A list of 3 positive signals
    - A list of 3 improvement suggestions

    Returns (summary_text, positive_signals, improvement_areas).
    """
    first_name = applicant_name.split()[0]
    breakdown_text = "\n".join(
        f"- {s['title']}: {s['strength']} ({s['percent']}%, +{s['contribution']} pts) — {s['detail']}"
        for s in breakdown
    )

    prompt = f"""Applicant: {first_name}
Credit Score: {score}/100
Risk Tier: {risk_tier.title()} Risk

Score signals:
{breakdown_text}

Generate a JSON response with exactly these keys:
{{
  "summary": "<2-3 sentence plain-English summary of the score>",
  "positive_signals": ["<signal 1>", "<signal 2>", "<signal 3>"],
  "improvement_areas": ["<suggestion 1>", "<suggestion 2>", "<suggestion 3>"]
}}"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=600,
            system=REPORT_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        data = json.loads(raw)
        return (
            data.get("summary", ""),
            data.get("positive_signals", []),
            data.get("improvement_areas", []),
        )
    except Exception as e:
        # Graceful fallback
        tier_desc = {"low": "good", "medium": "fair", "high": "limited"}.get(risk_tier, "moderate")
        return (
            f"{first_name}'s credit profile shows {tier_desc} financial behaviour "
            f"based on alternative data. Score: {score}/100.",
            ["Consistent payment history detected", "Regular financial activity observed"],
            ["Upload more document types", "Add more months of data", "Provide income documentation"],
        )


def generate_share_token() -> str:
    """Generate a secure random token for report sharing."""
    return secrets.token_urlsafe(24)
