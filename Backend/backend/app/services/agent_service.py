"""
AI Agent service for conversational gap-filling.
Uses Claude to ask targeted follow-up questions when document
extraction leaves required features incomplete.
"""
import json
from typing import Optional

import anthropic

from app.core.config import settings

client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

# Features the ML model needs — the agent will ask about any that are still null
REQUIRED_FEATURES = [
    "income_stability_score",
    "employment_type",
    "num_dependents",
    "has_repaid_informal_loan",
]

# Map feature names to natural language questions + chip options
FEATURE_QUESTIONS = {
    "income_stability_score": {
        "question": "What is your approximate monthly income in USD?",
        "chips": None,
        "type": "numeric",
    },
    "employment_type": {
        "question": "What best describes your current work?",
        "chips": ["Salaried employee", "Self-employed", "Daily wage worker", "Unemployed", "Other"],
        "type": "choice",
    },
    "num_dependents": {
        "question": "How many people depend on your income?",
        "chips": ["0", "1–2", "3–5", "6 or more"],
        "type": "choice",
    },
    "has_repaid_informal_loan": {
        "question": "Have you ever taken and fully repaid an informal loan (from a friend, family, or local lender)?",
        "chips": ["Yes", "No", "Not sure"],
        "type": "choice",
    },
}

AGENT_SYSTEM_PROMPT = """You are a friendly, empathetic credit assistant helping people in emerging markets build their first credit profile.

Your job is to ask ONE follow-up question at a time to fill in missing information for the credit scoring model.

Rules:
- Keep all messages short, warm, and jargon-free
- Ask only one question per turn
- When the user answers, acknowledge briefly (1 sentence max) before asking the next question
- Never ask about the same feature twice
- When all required info is collected, respond with exactly: COMPLETE
- Write in plain English suitable for users with basic digital literacy
- Do not mention "credit scoring", "ML model", or technical terms"""


def get_missing_features(aggregated_features: dict) -> list[str]:
    """Return list of required feature names that are still missing."""
    missing = []
    for feat in REQUIRED_FEATURES:
        val = aggregated_features.get(feat)
        if val is None or val == "":
            missing.append(feat)
    return missing


def build_conversation_messages(history: list[dict]) -> list[dict]:
    """Convert DB conversation records to Anthropic message format."""
    messages = []
    for turn in history:
        role = "assistant" if turn["role"] == "ai" else "user"
        messages.append({"role": role, "content": turn["message"]})
    return messages


def get_next_question(
    missing_features: list[str],
    conversation_history: list[dict],
    user_name: str,
) -> tuple[str, Optional[list[str]], bool]:
    """
    Determine the next question to ask.
    Returns (ai_message, chips_or_None, is_complete).
    """
    if not missing_features:
        return (
            f"Perfect, {user_name.split()[0]}! I have everything I need. "
            "Generating your credit score now...",
            None,
            True,
        )

    next_feature = missing_features[0]
    feature_info = FEATURE_QUESTIONS.get(next_feature)

    if not feature_info:
        # Shouldn't happen, but skip unknown features
        return get_next_question(missing_features[1:], conversation_history, user_name)

    # If this is the first question, add a warm opener
    if not conversation_history:
        prefix = (
            f"Hi {user_name.split()[0]} 👋 I've reviewed your uploaded documents. "
            "To complete your credit profile, I just have a few quick questions — "
            "this will take under 2 minutes.\n\n"
        )
    else:
        prefix = ""

    question = prefix + feature_info["question"]
    chips = feature_info.get("chips")

    return question, chips, False


def parse_user_answer_to_feature(feature_name: str, answer: str) -> any:
    """
    Convert a free-text or chip answer into a typed feature value.
    """
    answer = answer.strip()

    if feature_name == "income_stability_score":
        # Extract a number from the answer and normalize to 0-1
        import re
        nums = re.findall(r"[\d,]+\.?\d*", answer.replace(",", ""))
        if nums:
            monthly = float(nums[0])
            # Rough normalization: $2000/month = score of 1.0
            return min(monthly / 2000.0, 1.0)
        return 0.5

    elif feature_name == "employment_type":
        mapping = {
            "salaried employee": "employee",
            "self-employed": "self_employed",
            "daily wage worker": "daily_wage",
            "unemployed": "unemployed",
        }
        return mapping.get(answer.lower(), "other")

    elif feature_name == "num_dependents":
        mapping = {"0": 0, "1–2": 1.5, "3–5": 4, "6 or more": 7}
        return mapping.get(answer, 2)

    elif feature_name == "has_repaid_informal_loan":
        return 1 if answer.lower() == "yes" else 0

    return answer


def extract_features_from_conversation(
    conversation_history: list[dict],
) -> dict:
    """
    Walk through conversation history and extract feature values
    from user answers in order.
    """
    features = {}
    # Pair AI questions with user answers
    turns = [t for t in conversation_history if t["role"] == "user"]

    for i, feature_name in enumerate(REQUIRED_FEATURES):
        if i < len(turns):
            features[feature_name] = parse_user_answer_to_feature(
                feature_name, turns[i]["message"]
            )
        else:
            features[feature_name] = None

    return features
