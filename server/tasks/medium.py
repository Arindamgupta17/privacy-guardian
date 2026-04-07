"""
Task 2 — MEDIUM: Contextual PII Redaction
==========================================
PII is embedded in natural language without obvious formatting.
Examples:
  - "I spoke with Sarah from Delhi about her account"
  - "My brother Raj handles all billing queries"
  - "The patient's son, Arjun, can be contacted"

Ground truth PII is defined at dataset creation time (not inferred dynamically).
This makes the grader fully deterministic.

Grader: Check what % of ground-truth contextual PII tokens are absent from redacted text.
Exploit protection: redacted < 30% length of original → MIN_SCORE (0.01)

Score is always strictly in (0, 1) — never exactly 0.0 or 1.0.
"""

from typing import Dict, List, Tuple

MEDIUM_DOCUMENTS: List[Dict] = [
    {
        "id": "medium_001",
        "text": (
            "Call transcript — Customer Support\n\n"
            "Agent: Thank you for calling. May I know who I'm speaking with?\n"
            "Customer: Hi, this is Sneha Kulkarni. I'm calling about my husband Vikram's account.\n"
            "Agent: Sure Sneha, can you verify the registered mobile for Vikram's profile?\n"
            "Customer: Yes, it's under Vikram Kulkarni, he lives in Pune, Kothrud area.\n"
            "Agent: And your relationship to the account holder?\n"
            "Customer: I'm his wife. Our neighbour Ramesh also has an account with you.\n"
            "Agent: Noted. Let me pull up Vikram's account right away."
        ),
        "pii_items": [
            "Sneha Kulkarni",
            "Sneha",
            "Vikram",
            "Vikram Kulkarni",
            "Pune",
            "Kothrud",
            "Ramesh",
        ],
        "utility_keywords": ["account", "customer", "support", "registered", "mobile"],
    },
    {
        "id": "medium_002",
        "text": (
            "Email thread — Internal Escalation\n\n"
            "From: Support Agent\n"
            "Subject: Escalation for unhappy customer\n\n"
            "Hi Team,\n\n"
            "I spoke with Deepak Menon today regarding his complaint. He mentioned that his "
            "colleague Anjali had the same problem last month. Deepak is based out of "
            "Hyderabad and works at a firm near Banjara Hills. His manager, whose name he "
            "gave as Mr. Suresh Rao, has also been affected. Deepak said he would escalate "
            "to the consumer forum if not resolved by Friday.\n\n"
            "Please prioritize this ticket.\n\nRegards"
        ),
        "pii_items": [
            "Deepak Menon",
            "Deepak",
            "Anjali",
            "Hyderabad",
            "Banjara Hills",
            "Suresh Rao",
            "Mr. Suresh Rao",
        ],
        "utility_keywords": ["escalation", "complaint", "consumer", "ticket", "prioritize"],
    },
    {
        "id": "medium_003",
        "text": (
            "Patient intake form — Transcribed\n\n"
            "The patient, referred to us by Dr. Meera Joshi, presented with recurring "
            "migraines. The patient's emergency contact is her sister Kavitha who lives "
            "in Chennai. Her father, retired Colonel Srinivas, also has a history of "
            "hypertension. The patient mentioned she was previously treated at Apollo "
            "Hospital under a Dr. Prakash. She currently resides near Adyar, Chennai.\n\n"
            "Diagnosis: Chronic migraine with aura.\n"
            "Prescribed: Topiramate 50mg."
        ),
        "pii_items": [
            "Dr. Meera Joshi",
            "Meera Joshi",
            "Kavitha",
            "Chennai",
            "Colonel Srinivas",
            "Srinivas",
            "Dr. Prakash",
            "Prakash",
            "Adyar",
        ],
        "utility_keywords": ["migraine", "hypertension", "diagnosis", "prescribed", "topiramate"],
    },
]

# ── Score bounds — strictly open interval (0, 1) ──────────────────────────────
MIN_SCORE = 0.01
MAX_SCORE = 0.99


def _strict_score(value: float) -> float:
    """Clamp to strict open interval — never exactly 0.0 or 1.0."""
    clamped = max(MIN_SCORE, min(MAX_SCORE, float(value)))
    rounded = round(clamped, 4)
    return max(MIN_SCORE, min(MAX_SCORE, rounded))


def get_task_config() -> Dict:
    return {
        "name": "contextual_redaction",
        "description": (
            "Identify and redact PII that is embedded in natural language. "
            "Unlike obvious patterns (emails, phone numbers), this PII includes: "
            "person names mentioned in conversation, city/neighbourhood names tied "
            "to individuals, relationship references ('his wife', 'her sister'). "
            "Replace all personal names and location identifiers with [NAME] or [LOCATION]. "
            "Preserve the analytical/business content of the document."
        ),
        "pii_categories": ["NAME", "LOCATION", "RELATIONSHIP_REFERENCE"],
        "max_steps": 3,
    }


def get_document(step: int) -> Dict:
    idx = (step - 1) % len(MEDIUM_DOCUMENTS)
    return MEDIUM_DOCUMENTS[idx]


def score(original: str, redacted: str, doc: Dict) -> Tuple[float, str, Dict]:
    """
    Scoring breakdown:
      - Over-redaction guard: redacted < 30% of original → MIN_SCORE (0.01)
      - PII removal score (80%): % of ground-truth PII items absent from redacted text
      - Utility preservation (20%): utility keywords still present

    Score is always strictly in (MIN_SCORE, MAX_SCORE) — never exactly 0.0 or 1.0.
    """
    if len(redacted.strip()) < 0.30 * len(original):
        return (
            MIN_SCORE,
            "Over-redaction: document too short. Preserve non-PII content.",
            {"exploit": "over_redaction"},
        )

    pii_items: List[str] = doc["pii_items"]
    removed = 0
    missed = []

    for item in pii_items:
        if item.lower() not in redacted.lower():
            removed += 1
        else:
            missed.append(item)

    pii_score = removed / len(pii_items) if pii_items else 1.0

    # Utility keywords check
    utility_keywords = doc.get("utility_keywords", [])
    keywords_present = sum(1 for kw in utility_keywords if kw.lower() in redacted.lower())
    utility_ratio = keywords_present / len(utility_keywords) if utility_keywords else 1.0

    raw = pii_score * 0.80 + utility_ratio * 0.20
    final_score = _strict_score(raw)

    feedback_parts = []
    if missed:
        feedback_parts.append(
            f"Contextual PII still present: {missed[:3]}{'...' if len(missed) > 3 else ''}"
        )
    if utility_ratio < 0.75:
        feedback_parts.append("Important non-PII content was removed — preserve business context.")
    if not feedback_parts:
        feedback_parts.append("All contextual PII redacted and document utility preserved. Well done!")

    info = {
        "pii_total": len(pii_items),
        "pii_removed": removed,
        "pii_missed": missed,
        "utility_ratio": round(utility_ratio, 4),
        "pii_score": round(pii_score, 4),
        "final_score": final_score,
    }

    return final_score, " | ".join(feedback_parts), info
