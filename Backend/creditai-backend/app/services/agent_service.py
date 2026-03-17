"""
Agent Service — Hybrid: Python tracks features, Gemini writes natural responses.
India-specific: all currency in INR, context tailored for Indian users.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Optional

from google import genai

from app.core.config import settings

logger = logging.getLogger(__name__)

client = genai.Client(api_key=settings.GEMINI_API_KEY)

# ── Feature schema ────────────────────────────────────────────────────────────
FEATURE_KEYS = [
    "utility_payment_streak_months",
    "utility_on_time_rate",
    "avg_monthly_recharge_usd",      # stored as USD internally for ML model
    "recharge_consistency_score",
    "rent_payment_consistency",
    "upi_tx_frequency_per_month",
    "avg_monthly_tx_volume_usd",     # stored as USD internally for ML model
    "income_stability_score",
    "employment_type",               # 0=other,1=daily_wage,2=self_employed,3=employee
    "num_dependents",                # 0,1,2,3 where 3="6+"
    "had_informal_loan",             # 0/1
    "data_completeness_score",
]

CONVERSATIONAL_FEATURES = [
    "income_stability_score",
    "employment_type",
    "num_dependents",
    "had_informal_loan",
]

# INR to USD conversion rate for internal ML model storage
INR_TO_USD = 0.012  # 1 INR = 0.012 USD (approx 83 INR = 1 USD)

EMPLOYMENT_MAP = {
    "employee": 3, "salaried": 3, "government": 3, "govt": 3,
    "self-employed": 2, "self employed": 2, "business": 2,
    "freelance": 2, "freelancer": 2, "consultant": 2,
    "daily wage": 1, "daily-wage": 1, "daily wager": 1, "labour": 1, "labor": 1,
    "other": 0,
}
DEPENDENTS_MAP = {
    "0": 0, "none": 0, "nobody": 0, "no one": 0, "koi nahi": 0,
    "1": 1, "2": 1, "1-2": 1, "one": 1, "two": 1,
    "3": 2, "4": 2, "5": 2, "3-5": 2,
    "6": 3, "6+": 3, "many": 3,
}

CHIPS_MAP = {
    "employment_type": ["Salaried", "Self-employed", "Daily wage", "Other"],
    "num_dependents": ["None", "1-2", "3-5", "6+"],
    "had_informal_loan": ["Yes", "No"],
}

# ── Document extraction ───────────────────────────────────────────────────────

EXTRACTION_SYSTEM = """You are a financial data extractor for an Indian credit-scoring system.
Given raw text from Indian financial documents (utility bills, bank statements, rent receipts,
mobile recharge history, UPI transaction records), extract the following features as JSON.
Return ONLY valid JSON with these exact keys. Use null for any value you cannot determine.

All monetary values should be converted to USD (1 USD = 83 INR).

Keys:
- utility_payment_streak_months: integer – consecutive months of utility payments found
- utility_on_time_rate: float 0-1 – fraction of utility payments made on time
- avg_monthly_recharge_usd: float – average monthly mobile recharge in USD (divide INR by 83)
- recharge_consistency_score: float 0-1 – how regularly recharges happen (1 = every month)
- rent_payment_consistency: float 0-1 – fraction of months with rent paid
- upi_tx_frequency_per_month: float – average number of UPI/digital transactions per month
- avg_monthly_tx_volume_usd: float – average total transaction volume per month in USD

Be conservative. If a value is unclear, return null. Never invent numbers."""


async def extract_features_from_documents(doc_texts: list[dict]) -> dict:
    if not doc_texts:
        return {k: None for k in FEATURE_KEYS}

    combined = "\n\n".join(
        f"=== {d['doc_type']} ===\n{d['text']}" for d in doc_texts
    )

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=combined,
            config={"system_instruction": EXTRACTION_SYSTEM},
        )
        raw = response.text.strip()
        raw = re.sub(r"^```json\s*|^```\s*|\s*```$", "", raw, flags=re.MULTILINE).strip()
        extracted = json.loads(raw)
        logger.info(f"[Gemini] Document extraction success: {extracted}")
    except Exception as e:
        logger.error(f"[Gemini] Document extraction failed: {e}")
        extracted = {}

    features: dict = {k: None for k in FEATURE_KEYS}
    features.update({k: extracted.get(k) for k in FEATURE_KEYS if k in extracted})
    return features


# ── Feature tracking ─────────────────────────────────────────────────────────

def get_next_missing_feature(features: dict) -> Optional[str]:
    for key in CONVERSATIONAL_FEATURES:
        if features.get(key) is None:
            return key
    return None


def parse_user_answer(feature: str, answer: str) -> float | int | None:
    answer_lower = answer.strip().lower()

    if feature == "employment_type":
        for keyword, val in EMPLOYMENT_MAP.items():
            if keyword in answer_lower:
                return val
        if any(w in answer_lower for w in ["work", "job", "company", "office", "corporate", "naukri"]):
            return 3
        return 0

    if feature == "num_dependents":
        for label, val in DEPENDENTS_MAP.items():
            if label in answer_lower:
                return val
        m = re.search(r"\d+", answer)
        if m:
            return min(int(m.group()), 3)
        return 0

    if feature == "had_informal_loan":
        if any(w in answer_lower for w in ["yes", "yeah", "yep", "have", "did", "took", "liya", "haan"]):
            return 1
        return 0

    if feature == "income_stability_score":
        # Extract the largest number — could be INR (e.g. 25000) or k notation (e.g. 25k)
        answer_clean = answer_lower.replace(",", "").replace("k", "000").replace("lakh", "00000").replace("lac", "00000")
        numbers = re.findall(r"[\d]+\.?\d*", answer_clean)
        if numbers:
            income_inr = float(max(numbers, key=lambda x: float(x)))
            # Map INR monthly income to stability score
            # <5000=0.2, 5000-15000=0.4, 15000-30000=0.6, 30000-60000=0.8, >60000=0.9
            if income_inr < 5000:       return 0.2
            elif income_inr < 15000:    return 0.4
            elif income_inr < 30000:    return 0.6
            elif income_inr < 60000:    return 0.8
            else:                       return 0.9
        return 0.5

    return None


def get_chips_for_feature(feature: Optional[str]) -> Optional[list]:
    if feature is None:
        return None
    return CHIPS_MAP.get(feature)


# ── Gemini natural language response ─────────────────────────────────────────

FEATURE_FRIENDLY_NAMES = {
    "income_stability_score": "monthly income",
    "employment_type": "type of work",
    "num_dependents": "number of dependents",
    "had_informal_loan": "informal loan history",
}

NEXT_QUESTION_NATURAL = {
    "income_stability_score": "Could you share roughly how much you earn per month in rupees? Even a rough figure is fine!",
    "employment_type": "What kind of work do you do — salaried job, self-employed, daily wage, or something else?",
    "num_dependents": "How many family members depend on your income — like parents, spouse, or children you support?",
    "had_informal_loan": "One last thing — have you ever borrowed money informally, like from a friend, family member, or local moneylender, and paid it back?",
}


async def generate_natural_response(
    previous_feature: Optional[str],
    previous_answer: Optional[str],
    next_feature: Optional[str],
    user_first_name: str,
    doc_context: str,
    is_first_message: bool = False,
) -> str:
    """Use Gemini to generate a warm, natural India-specific response."""

    if is_first_message:
        next_q = NEXT_QUESTION_NATURAL.get(next_feature, "Can you tell me a bit about your finances?")
        prompt = (
            f"You are Aria, a friendly financial advisor at CreditAI India. "
            f"Start a warm, short conversation with {user_first_name}. "
            f"Tell them you've reviewed their documents ({doc_context}) and just need a few quick details. "
            f"Then ask this question naturally: {next_q} "
            f"Keep it to 2-3 sentences. Sound human and friendly. "
            f"Context: This is for Indian users building their credit profile."
        )
    elif next_feature is None:
        prev_name = FEATURE_FRIENDLY_NAMES.get(previous_feature, previous_feature or "that")
        prompt = (
            f"You are Aria, a friendly financial advisor at CreditAI India. "
            f"The user just told you their {prev_name} is '{previous_answer}'. "
            f"Acknowledge this briefly and warmly (1 sentence), "
            f"then tell them you have everything you need and are generating their credit score now. "
            f"2 sentences max. Be warm and encouraging."
        )
    else:
        prev_name = FEATURE_FRIENDLY_NAMES.get(previous_feature, previous_feature or "that")
        next_q = NEXT_QUESTION_NATURAL.get(next_feature, "Can you tell me more?")
        prompt = (
            f"You are Aria, a friendly financial advisor at CreditAI India. "
            f"The user just said '{previous_answer}' when asked about their {prev_name}. "
            f"Briefly acknowledge their answer warmly (1 sentence — vary your responses, "
            f"don't always say 'Got it'). "
            f"Then ask: {next_q} "
            f"2-3 sentences max. Sound like a real helpful person."
        )

    try:
        logger.info(f"[Gemini] Calling generate_natural_response, next_feature={next_feature}")
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        result = response.text.strip()
        logger.info(f"[Gemini] Response: {result[:100]}")
        return result
    except Exception as e:
        logger.error(f"[Gemini] generate_natural_response failed: {type(e).__name__}: {e}")
        return _static_response(next_feature, previous_feature, previous_answer)


def _static_response(next_feature, prev_feature, prev_answer) -> str:
    ack_map = {
        "income_stability_score": "Thanks for sharing that!",
        "employment_type": "Great, noted!",
        "num_dependents": "Understood, thanks!",
        "had_informal_loan": "Appreciated, thanks for being open!",
    }
    ack = ack_map.get(prev_feature, "Thanks!") if prev_answer else ""
    questions = {
        "income_stability_score": "Aapki approximate monthly income kitni hai? (roughly in rupees)",
        "employment_type": "Aap kya kaam karte hain — salaried, self-employed, ya daily wage?",
        "num_dependents": "Kitne family members aap par financially depend karte hain?",
        "had_informal_loan": "Kya aapne kabhi kisi se informal loan liya hai aur wapas kiya hai?",
    }
    if next_feature is None:
        return f"{ack} Perfect! I have everything I need — generating your credit score now! 🎉"
    return f"{ack} {questions.get(next_feature, 'Can you tell me more about your finances?')}"


def _build_doc_context(features: dict) -> str:
    known = []
    if features.get("utility_payment_streak_months") is not None:
        known.append(f"{features['utility_payment_streak_months']} months of utility payments")
    if features.get("utility_on_time_rate") is not None:
        known.append(f"{int(features['utility_on_time_rate'] * 100)}% on-time utility rate")
    if features.get("rent_payment_consistency") is not None:
        known.append(f"{int(features['rent_payment_consistency'] * 100)}% rent consistency")
    if features.get("avg_monthly_recharge_usd") is not None:
        inr = round(features['avg_monthly_recharge_usd'] * 83)
        known.append(f"₹{inr} avg monthly recharge")
    if features.get("avg_monthly_tx_volume_usd") is not None:
        inr = round(features['avg_monthly_tx_volume_usd'] * 83)
        known.append(f"₹{inr} avg monthly transactions")
    return ", ".join(known) if known else "your uploaded documents"


# ── Greeting / completion ─────────────────────────────────────────────────────

def build_completion_message() -> str:
    return "Perfect! I have everything I need. Generating your credit score now…"