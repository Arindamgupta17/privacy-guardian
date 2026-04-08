"""
Task 2 — MEDIUM: Contextual PII Redaction
Scores strictly in (0.05, 0.95).
Fix: clamp ONLY final score once, not intermediate values.
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
        "pii_items": ["Sneha Kulkarni","Sneha","Vikram","Vikram Kulkarni","Pune","Kothrud","Ramesh"],
        "utility_keywords": ["account","customer","support","registered","mobile"],
    },
    {
        "id": "medium_002",
        "text": (
            "Email thread — Internal Escalation\n\n"
            "From: Support Agent\nSubject: Escalation for unhappy customer\n\n"
            "Hi Team,\n\n"
            "I spoke with Deepak Menon today regarding his complaint. He mentioned that his "
            "colleague Anjali had the same problem last month. Deepak is based out of "
            "Hyderabad and works at a firm near Banjara Hills. His manager, whose name he "
            "gave as Mr. Suresh Rao, has also been affected. Deepak said he would escalate "
            "to the consumer forum if not resolved by Friday.\n\nPlease prioritize this ticket."
        ),
        "pii_items": ["Deepak Menon","Deepak","Anjali","Hyderabad","Banjara Hills","Suresh Rao","Mr. Suresh Rao"],
        "utility_keywords": ["escalation","complaint","consumer","ticket","prioritize"],
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
            "Diagnosis: Chronic migraine with aura.\nPrescribed: Topiramate 50mg."
        ),
        "pii_items": ["Dr. Meera Joshi","Meera Joshi","Kavitha","Chennai","Colonel Srinivas","Srinivas","Dr. Prakash","Prakash","Adyar"],
        "utility_keywords": ["migraine","hypertension","diagnosis","prescribed","topiramate"],
    },
    {
        "id": "medium_004",
        "text": (
            "Insurance Escalation Notes\n\n"
            "The claimant Neelima Rao called regarding a delayed settlement. "
            "She said her brother Harish submitted documents from Mysuru last week. "
            "Their family consultant Vivek from Jayanagar confirmed the policy copy was valid. "
            "Neelima requested priority review before month-end closure."
        ),
        "pii_items": ["Neelima Rao","Neelima","Harish","Mysuru","Vivek","Jayanagar"],
        "utility_keywords": ["claimant","settlement","documents","policy","priority"],
    },
    {
        "id": "medium_005",
        "text": (
            "Vendor Risk Review Summary\n\n"
            "During the review, consultant Farhan Ali noted that operations head Lata Menon "
            "had approved access changes from the Kochi branch. "
            "Farhan mentioned that coordinator Joseph from Ernakulam tracked the incident timeline. "
            "Lata asked the audit team to finalize the mitigation report by Friday."
        ),
        "pii_items": ["Farhan Ali","Farhan","Lata Menon","Lata","Kochi","Joseph","Ernakulam"],
        "utility_keywords": ["review","operations","incident","audit","mitigation"],
    },
]


def clamp(value: float) -> float:
    """Clamp to strictly (0.05, 0.95) — called ONCE on final score only."""
    return round(max(0.05, min(0.95, float(value))), 4)


def get_task_config() -> Dict:
    return {
        "name": "contextual_redaction",
        "description": (
            "Identify and redact PII embedded in natural language — "
            "person names, city/neighbourhood names tied to individuals, "
            "and relationship references. "
            "Replace names with [NAME] and locations with [LOCATION]. "
            "Preserve all analytical and business content."
        ),
        "pii_categories": ["NAME","LOCATION","RELATIONSHIP_REFERENCE"],
        "max_steps": 3,
    }


def get_document(step: int) -> Dict:
    return MEDIUM_DOCUMENTS[(step - 1) % len(MEDIUM_DOCUMENTS)]


def score(original: str, redacted: str, doc: Dict) -> Tuple[float, str, Dict]:
    # Exploit guard
    if len(redacted.strip()) < 0.30 * len(original):
        return 0.05, "Over-redaction: document too short. Preserve non-PII content.", {"exploit": "over_redaction"}

    pii_items = doc["pii_items"]
    removed, missed = 0, []
    for item in pii_items:
        if item.lower() not in redacted.lower():
            removed += 1
        else:
            missed.append(item)

    # Raw intermediate values — NOT clamped individually
    pii_ratio = removed / len(pii_items) if pii_items else 0.0

    utility_keywords = doc.get("utility_keywords", [])
    keywords_present = sum(1 for kw in utility_keywords if kw.lower() in redacted.lower())
    utility_ratio = keywords_present / len(utility_keywords) if utility_keywords else 0.0

    raw = pii_ratio * 0.80 + utility_ratio * 0.20

    # Clamp ONCE at the end
    final_score = clamp(raw)

    feedback_parts = []
    if missed:
        feedback_parts.append(f"Contextual PII still present ({len(missed)}): {missed[:3]}{'...' if len(missed)>3 else ''}")
    if utility_ratio < 0.75:
        feedback_parts.append("Important content removed — preserve non-PII context.")
    if not feedback_parts:
        feedback_parts.append("All contextual PII redacted and document utility preserved!")

    info = {
        "pii_total": len(pii_items),
        "pii_removed": removed,
        "pii_missed": missed,
        "utility_ratio": round(utility_ratio, 4),
        "pii_ratio": round(pii_ratio, 4),
        "final_score": final_score,
    }
    return final_score, " | ".join(feedback_parts), info
