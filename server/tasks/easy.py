"""
Task 1 — EASY: Pattern PII Redaction
Scores are strictly in (0.05, 0.95) — never exactly 0.0 or 1.0.
"""
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
        "pii_items": ["amit.sharma@gmail.com", "9876543210", "4111 1111 1111 1111", "1234 5678 9012"],
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
        "pii_items": ["priya.nair@outlook.com", "+91-98765-43210", "080-22334455", "5500 0000 0000 0004", "9876 5432 1098"],
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
        "pii_items": ["rahul.v@ymail.com", "7654321098", "3782 822463 10005"],
        "utility_keywords": ["transaction", "amazon", "banking", "helpline"],
    },
    {
        "id": "easy_004",
        "text": (
            "KYC Verification Request\n\n"
            "Dear Customer,\n"
            "We need to verify your KYC details for account activation.\n"
            "Name: Sunita Rao\n"
            "Email: sunita.rao@rediffmail.com\n"
            "Mobile: 9988776655\n"
            "Aadhaar: 2345 6789 0123\n"
            "Please submit your documents within 48 hours to avoid account suspension."
        ),
        "pii_items": ["sunita.rao@rediffmail.com", "9988776655", "2345 6789 0123"],
        "utility_keywords": ["kyc", "account", "verification", "documents"],
    },
    {
        "id": "easy_005",
        "text": (
            "Insurance Claim Form\n\n"
            "Claimant: Vikram Singh\n"
            "Policy Email: vikram.singh@insureme.in\n"
            "Contact: 8123456789\n"
            "Card on file: 4000 0566 5566 5556\n"
            "Aadhaar: 5678 9012 3456\n"
            "Claim Type: Health — Hospitalization\n"
            "Amount Claimed: Rs. 1,25,000\n"
            "Status: Under review."
        ),
        "pii_items": ["vikram.singh@insureme.in", "8123456789", "4000 0566 5566 5556", "5678 9012 3456"],
        "utility_keywords": ["insurance", "claim", "hospitalization", "health"],
    },
]

# Score boundaries — strictly between 0 and 1
MIN_SCORE = 0.05
MAX_SCORE = 0.95


def get_task_config() -> Dict:
    return {
        "name": "pattern_redaction",
        "description": (
            "Redact all clearly formatted PII from the document. "
            "Replace emails with [EMAIL], phones with [PHONE], "
            "card numbers with [CREDIT_CARD], Aadhaar numbers with [AADHAAR]. "
            "Preserve all other content exactly."
        ),
        "pii_categories": ["EMAIL", "PHONE", "CREDIT_CARD", "AADHAAR"],
        "max_steps": 3,
    }


def get_document(step: int) -> Dict:
    return EASY_DOCUMENTS[(step - 1) % len(EASY_DOCUMENTS)]


def score(original: str, redacted: str, doc: Dict) -> Tuple[float, str, Dict]:
    info = {}

    # Over-redaction guard — never return exactly 0.0
    if len(redacted.strip()) < 0.30 * len(original):
        return MIN_SCORE, "Over-redaction: document too short. Only replace PII tokens, preserve everything else.", {"exploit": "over_redaction"}

    pii_items: List[str] = doc["pii_items"]
    removed, missed = 0, []
    for item in pii_items:
        if item.lower() not in redacted.lower():
            removed += 1
        else:
            missed.append(item)

    pii_score = removed / len(pii_items) if pii_items else 1.0

    utility_keywords = doc.get("utility_keywords", [])
    keywords_present = sum(1 for kw in utility_keywords if kw.lower() in redacted.lower())
    utility_bonus = 0.1 if keywords_present >= len(utility_keywords) * 0.75 else 0.0

    raw_score = pii_score * 0.9 + utility_bonus

    # Clamp strictly between MIN_SCORE and MAX_SCORE — never 0.0 or 1.0
    final_score = round(max(MIN_SCORE, min(MAX_SCORE, raw_score)), 4)

    feedback_parts = []
    if missed:
        feedback_parts.append(f"Missed PII: {missed[:3]}{'...' if len(missed) > 3 else ''}")
    if utility_bonus == 0.0:
        feedback_parts.append("Some utility content removed — preserve non-PII text.")
    if not feedback_parts:
        feedback_parts.append("Excellent redaction! All PII removed and document utility preserved.")

    info = {
        "pii_total": len(pii_items),
        "pii_removed": removed,
        "pii_missed": missed,
        "utility_keywords_present": keywords_present,
        "pii_score": round(pii_score, 4),
        "utility_bonus": utility_bonus,
        "final_score": final_score,
    }

    return final_score, " | ".join(feedback_parts), info
