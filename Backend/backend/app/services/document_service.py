"""
Document extraction service.
Uses Claude to parse text from uploaded financial documents
and extract structured features used by the ML model.
"""
import json
import os
import base64
from typing import Optional

import anthropic
from pypdf import PdfReader
from PIL import Image
import pytesseract

from app.core.config import settings

client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

EXTRACTION_SYSTEM_PROMPT = """You are a financial document analyst specializing in alternative credit data for unbanked populations.

Your job is to read a financial document and extract structured features from it.
Return ONLY valid JSON — no explanation, no markdown fences.

Extract these fields (use null if not found):
{
  "doc_type_detected": "utility_bill|rent_receipt|mobile_recharge|transaction_statement|unknown",
  "months_of_data": <integer or null>,
  "on_time_payment_rate": <0.0-1.0 or null>,
  "payment_streak_months": <integer or null>,
  "average_monthly_amount": <float in USD or null>,
  "consistency_score": <0.0-1.0 or null>,
  "transaction_frequency_per_month": <float or null>,
  "currency_detected": "<string or null>",
  "date_range_start": "<YYYY-MM or null>",
  "date_range_end": "<YYYY-MM or null>",
  "confidence": <0.0-1.0>,
  "notes": "<any important observations or null>"
}"""


def extract_text_from_pdf(file_path: str) -> str:
    """Extract raw text from a PDF file."""
    try:
        reader = PdfReader(file_path)
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages).strip()
    except Exception as e:
        return f"[PDF extraction error: {e}]"


def extract_text_from_image(file_path: str) -> str:
    """OCR an image file to extract text."""
    try:
        img = Image.open(file_path)
        return pytesseract.image_to_string(img).strip()
    except Exception as e:
        return f"[OCR error: {e}]"


def extract_text_from_csv(file_path: str) -> str:
    """Return raw CSV content (Claude can parse it directly)."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception as e:
        return f"[CSV read error: {e}]"


def extract_text_from_file(file_path: str, mime_type: str) -> str:
    """Route to the right text extractor based on mime type."""
    mime = (mime_type or "").lower()
    if "pdf" in mime:
        return extract_text_from_pdf(file_path)
    elif mime in ("image/jpeg", "image/jpg", "image/png"):
        return extract_text_from_image(file_path)
    elif "csv" in mime or file_path.endswith(".csv"):
        return extract_text_from_csv(file_path)
    else:
        # Fallback: try PDF then text
        try:
            return extract_text_from_pdf(file_path)
        except Exception:
            return "[Unsupported file type]"


def extract_features_with_claude(
    document_text: str,
    declared_doc_type: str,
) -> tuple[dict, float]:
    """
    Send document text to Claude and get back structured features.
    Returns (features_dict, confidence_score).
    """
    user_message = f"""Document type declared by user: {declared_doc_type}

Document content:
---
{document_text[:8000]}  
---

Extract the structured financial features from this document."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=EXTRACTION_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )
        raw = response.content[0].text.strip()
        # Strip markdown fences if Claude wrapped them
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        features = json.loads(raw)
        confidence = float(features.get("confidence", 0.5))
        return features, confidence
    except (json.JSONDecodeError, Exception) as e:
        return {"error": str(e), "confidence": 0.0}, 0.0


def process_document(
    file_path: str,
    mime_type: str,
    declared_doc_type: str,
) -> tuple[str, dict, float]:
    """
    Full pipeline: extract text → run Claude extraction → return results.
    Returns (extracted_text, features_dict, confidence).
    """
    extracted_text = extract_text_from_file(file_path, mime_type)
    features, confidence = extract_features_with_claude(extracted_text, declared_doc_type)
    return extracted_text, features, confidence
