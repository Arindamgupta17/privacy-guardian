"""
Task 1 — EASY: Pattern PII Redaction
=====================================
Documents contain clearly formatted, obvious PII:
  - Email addresses
  - Phone numbers (Indian + international formats)
  - Credit card numbers
  - Aadhaar numbers (Indian national ID)

Grader: Check what % of planted PII tokens are gone from the redacted text.
Exploit protection: If redacted text is < 30% length of original → score 0.0
"""

import re
from typing import Dict, List, Tuple

# ── Synthetic documents with planted PII ──────────────────────────────────────
# Each document has a ground-truth list of PII strings that MUST be redacted.

EASY_DOCUMENTS: List[Dict] = [
    {
        "id": "easy_001",
        "text": (
            "Dear Support Team,\n\n"
            "I am writing regarding my recent order. My name is Amit Sharma and you can "
            "reach me at amit.sharma@gmail.com or call me on 9876543210. My billing "
            "address is 42, MG Road, Bengaluru. I used my credit card 4111 1111 1111 1111 "
            "for this purchase. My Aadhaar number is 1234 5678 9012. Please resolve this "
            "at the earliest.\n\nRegards,\nAmit"
        ),
        "pii_items": [
            "amit.sharma@gmail.com",
            "9876543210",
            "4111 1111 1111 1111",
            "1234 5678 9012",
        ],
        "utility_keywords": ["order", "billing", "purchase", "support"],
    },
    {
        "id": "easy_002",
        "text": (
            "Customer complaint log — ID #4421\n\n"
            "Customer: Priya Nair\n"
            "Email: priya.nair@outlook.com\n"
            "Phone: +91-98765-43210\n"
            "Alternate: 080-22334455\n"
            "Card used: 5500 0000 0000 0004\n"
            "Issue: Refund not processed after 7 days.\n"
            "Aadhaar: 9876 5432 1098\n"
            "Status: Escalated to L2 support."
        ),
        "pii_items": [
            "priya.nair@outlook.com",
            "+91-98765-43210",
            "080-22334455",
            "5500 0000 0000 0004",
            "9876 5432 1098",
        ],
        "utility_keywords": ["refund", "escalated", "support", "complaint"],
    },
    {
        "id": "easy_003",
        "text": (
            "Transaction Alert — Online Banking\n\n"
            "Account holder: Rahul Verma\n"
            "Registered email: rahul.v@ymail.com\n"
            "Mobile: 7654321098\n"
            "Card number: 3782 822463 10005\n"
            "Transaction of Rs. 4,500 was made at Amazon.in on 01-Apr-2026.\n"
            "If this was not you, call our helpline immediately."
        ),
        "pii_items": [
            "rahul.v@ymail.com",
            "7654321098",
            "3782 822463 10005",
        ],
        "utility_keywords": ["transaction", "amazon", "banking", "helpline"],
    },
]

# ── Regex patterns for common PII ─────────────────────────────────────────────
EMAIL_RE    = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
PHONE_RE    = re.compile(r"(\+91[-\s]?)?[6-9]\d{9}|0\d{2,4}[-\s]\d{6,8}")
CARD_RE     = re.compile(r"\b(?:\d[ \-]?){13,16}\b")
AADHAAR_RE  = re.compile(r"\b\d{4}\s\d{4}\s\d{4}\b")


def get_task_config() -> Dict:
    return {
        "name": "pattern_redaction",
        "description": (
            "Redact all clearly formatted PII from the document. "
            "This includes email addresses, phone numbers (Indian formats), "
            "credit/debit card numbers, and Aadhaar numbers. "
            "Replace each PII item with an appropriate tag like [EMAIL], [PHONE], "
            "[CREDIT_CARD], or [AADHAAR]. Preserve all other content exactly."
        ),
        "pii_categories": ["EMAIL", "PHONE", "CREDIT_CARD", "AADHAAR"],
        "max_steps": 3,
    }


def get_document(step: int) -> Dict:
    idx = (step - 1) % len(EASY_DOCUMENTS)
    return EASY_DOCUMENTS[idx]


def score(original: str, redacted: str, doc: Dict) -> Tuple[float, str, Dict]:
    """
    Returns (score, feedback, info_dict).

    Scoring breakdown:
      - Over-redaction guard: if redacted < 30% length of original → 0.0
      - Base score: % of planted PII items successfully removed
      - Utility bonus: +0.1 if key utility keywords are still present
    """
    info = {}

    # ── Exploit guard ─────────────────────────────────────────────────────────
    if len(redacted.strip()) < 0.30 * len(original):
        return 0.0, "Over-redaction detected: the document is too short. Do not blank the entire document.", {"exploit": "over_redaction"}

    pii_items: List[str] = doc["pii_items"]
    removed = 0
    missed = []

    for item in pii_items:
        if item.lower() not in redacted.lower():
            removed += 1
        else:
            missed.append(item)

    pii_score = removed / len(pii_items) if pii_items else 1.0

    # ── Utility keyword check ─────────────────────────────────────────────────
    utility_keywords = doc.get("utility_keywords", [])
    keywords_present = sum(1 for kw in utility_keywords if kw.lower() in redacted.lower())
    utility_bonus = 0.1 if keywords_present >= len(utility_keywords) * 0.75 else 0.0

    final_score = min(1.0, round(pii_score * 0.9 + utility_bonus, 4))

    feedback_parts = []
    if missed:
        feedback_parts.append(f"Missed PII: {missed}")
    if utility_bonus == 0.0:
        feedback_parts.append("Some utility keywords were removed — preserve non-PII content.")
    if not feedback_parts:
        feedback_parts.append("Excellent redaction! All PII removed and document utility preserved.")

    info = {
        "pii_total": len(pii_items),
        "pii_removed": removed,
        "pii_missed": missed,
        "utility_keywords_present": keywords_present,
        "pii_score": round(pii_score, 4),
        "utility_bonus": utility_bonus,
    }

    return final_score, " | ".join(feedback_parts), info
