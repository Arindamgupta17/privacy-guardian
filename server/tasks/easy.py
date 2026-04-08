"""
Task 1 — EASY: Pattern PII Redaction
Scores strictly in (0.05, 0.95) — never 0.0 or 1.0.
"""

import re
from typing import Dict, List, Tuple

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
        "pii_items": ["amit.sharma@gmail.com","9876543210","4111 1111 1111 1111","1234 5678 9012"],
        "utility_keywords": ["order","billing","purchase","support"],
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
        "pii_items": ["priya.nair@outlook.com","+91-98765-43210","080-22334455","5500 0000 0000 0004","9876 5432 1098"],
        "utility_keywords": ["refund","escalated","support","complaint"],
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
        "pii_items": ["rahul.v@ymail.com","7654321098","3782 822463 10005"],
        "utility_keywords": ["transaction","amazon","banking","helpline"],
    },
    {
        "id": "easy_004",
        "text": (
            "Courier Delivery Update\n\n"
            "Hi Nisha, your package #PKG-7712 is out for delivery. "
            "Contact nisha.kapoor@mail.com or call 9987654321. "
            "Backup contact: +91 91234 56789. "
            "Payment was processed using card 6011 0009 9013 9424. "
            "Please keep OTP ready at the time of handover."
        ),
        "pii_items": ["nisha.kapoor@mail.com","9987654321","+91 91234 56789","6011 0009 9013 9424"],
        "utility_keywords": ["delivery","package","payment","otp"],
    },
    {
        "id": "easy_005",
        "text": (
            "Utility Bill Reminder\n\n"
            "Dear customer, your electricity bill for April is pending. "
            "Email: arjun.mehta@provider.net. "
            "Registered mobile: 9090909090. "
            "Customer support helpline: 022-44556677. "
            "Aadhaar linked to account: 4567 8912 3456. "
            "Kindly pay before due date to avoid late fee."
        ),
        "pii_items": ["arjun.mehta@provider.net","9090909090","022-44556677","4567 8912 3456"],
        "utility_keywords": ["bill","electricity","due date","late fee"],
    },
]


MIN_SCORE = 0.05
MAX_SCORE = 0.95


def clamp(value: float) -> float:
    """Clamp strictly between 0.05 and 0.95"""
    return round(max(MIN_SCORE, min(MAX_SCORE, float(value))), 4)


def get_task_config() -> Dict:
    return {
        "name": "pattern_redaction",
        "description": (
            "Redact all clearly formatted PII from the document. "
            "Replace emails with [EMAIL], phones with [PHONE], "
            "card numbers with [CREDIT_CARD], Aadhaar with [AADHAAR]. "
            "Preserve all other content exactly."
        ),
        "pii_categories": ["EMAIL","PHONE","CREDIT_CARD","AADHAAR"],
        "max_steps": 3,
    }


def get_document(step: int) -> Dict:
    return EASY_DOCUMENTS[(step - 1) % len(EASY_DOCUMENTS)]


def score(original: str, redacted: str, doc: Dict) -> Tuple[float, str, Dict]:

    # ✅ FIXED exploit guard (uses clamp)
    if len(redacted.strip()) < 0.30 * len(original):
        final_score = clamp(MIN_SCORE)
        return final_score, "Over-redaction: document too short. Only replace PII tokens.", {
            "exploit": "over_redaction",
            "final_score": final_score
        }

    pii_items = doc["pii_items"]
    removed, missed = 0, []

    for item in pii_items:
        if item.lower() not in redacted.lower():
            removed += 1
        else:
            missed.append(item)

    pii_ratio = removed / len(pii_items) if pii_items else MIN_SCORE

    utility_keywords = doc.get("utility_keywords", [])
    keywords_present = sum(1 for kw in utility_keywords if kw.lower() in redacted.lower())
    utility_bonus = 0.10 if keywords_present >= len(utility_keywords) * 0.75 else MIN_SCORE

    raw = pii_ratio * 0.9 + utility_bonus

    # ✅ Final clamp
    final_score = clamp(raw)

    feedback_parts = []
    if missed:
        feedback_parts.append(f"Missed PII: {missed[:3]}{'...' if len(missed)>3 else ''}")
    if keywords_present < len(utility_keywords) * 0.75:
        feedback_parts.append("Some utility content removed — preserve non-PII text.")
    if not feedback_parts:
        feedback_parts.append("Excellent! All PII removed and document utility preserved.")

    info = {
        "pii_missed": missed,
        "final_score": final_score,
    }

    # ✅ Safety check
    assert MIN_SCORE <= final_score <= MAX_SCORE, f"Invalid score: {final_score}"

    return final_score, " | ".join(feedback_parts), info