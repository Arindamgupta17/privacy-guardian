"""
Task 2 — MEDIUM: Contextual NER Redaction
Scores are strictly in (0.05, 0.95) — never exactly 0.0 or 1.0.
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
        "pii_items": ["Sneha Kulkarni", "Sneha", "Vikram", "Vikram Kulkarni", "Pune", "Kothrud", "Ramesh"],
        "utility_keywords": ["account", "customer", "support", "registered", "mobile"],
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
        "pii_items": ["Deepak Menon", "Deepak", "Anjali", "Hyderabad", "Banjara Hills", "Suresh Rao", "Mr. Suresh Rao"],
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
            "Diagnosis: Chronic migraine with aura.\nPrescribed: Topiramate 50mg."
        ),
        "pii_items": ["Dr. Meera Joshi", "Meera Joshi", "Kavitha", "Chennai", "Colonel Srinivas", "Srinivas", "Dr. Prakash", "Prakash", "Adyar"],
        "utility_keywords": ["migraine", "hypertension", "diagnosis", "prescribed", "topiramate"],
    },
    {
        "id": "medium_004",
        "text": (
            "HR Referral Note — Confidential\n\n"
            "Following up on the referral from Priya Mehta in the sales team. "
            "Her referral, Arjun Desai, has applied for the Senior Engineer role. "
            "Arjun previously worked under Rajesh at Infosys Pune. "
            "His reference, a Mr. Venkat from TCS Chennai, spoke highly of his "
            "problem-solving skills. Arjun currently lives in Whitefield, Bengaluru."
        ),
        "pii_items": ["Priya Mehta", "Priya", "Arjun Desai", "Arjun", "Rajesh", "Mr. Venkat", "Venkat", "Whitefield", "Bengaluru"],
        "utility_keywords": ["referral", "engineer", "technical", "infosys", "schedule"],
    },
    {
        "id": "medium_005",
        "text": (
            "Legal Deposition Summary\n\n"
            "The witness, a Mrs. Lalitha Iyer from Coimbatore, testified that on the "
            "evening of the incident, she saw the defendant speaking with a man named "
            "Sunil near the market. She confirmed that her neighbour Krishnamurthy, "
            "who works at the local bank, was also present. The opposing counsel, "
            "represented by advocate Ramachandran, objected to the line of questioning."
        ),
        "pii_items": ["Mrs. Lalitha Iyer", "Lalitha Iyer", "Lalitha", "Coimbatore", "Sunil", "Krishnamurthy", "Ramachandran"],
        "utility_keywords": ["witness", "testimony", "defendant", "counsel", "objection"],
    },
]

MIN_SCORE = 0.05
MAX_SCORE = 0.95


def get_task_config() -> Dict:
    return {
        "name": "contextual_redaction",
        "description": (
            "Identify and redact PII embedded in natural language — person names, "
            "city names linked to individuals, and relationship references. "
            "Replace names with [NAME] and locations with [LOCATION]. "
            "Preserve all business and analytical content."
        ),
        "pii_categories": ["NAME", "LOCATION", "RELATIONSHIP_REFERENCE"],
        "max_steps": 3,
    }


def get_document(step: int) -> Dict:
    return MEDIUM_DOCUMENTS[(step - 1) % len(MEDIUM_DOCUMENTS)]


def score(original: str, redacted: str, doc: Dict) -> Tuple[float, str, Dict]:
    if len(redacted.strip()) < 0.30 * len(original):
        return MIN_SCORE, "Over-redaction: document too short. Preserve non-PII content.", {"exploit": "over_redaction"}

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
    utility_ratio = keywords_present / len(utility_keywords) if utility_keywords else 1.0

    raw_score = pii_score * 0.80 + utility_ratio * 0.20

    # Strictly between MIN_SCORE and MAX_SCORE
    final_score = round(max(MIN_SCORE, min(MAX_SCORE, raw_score)), 4)

    feedback_parts = []
    if missed:
        feedback_parts.append(f"Contextual PII still present ({len(missed)}): {missed[:3]}{'...' if len(missed) > 3 else ''}")
    if utility_ratio < 0.75:
        feedback_parts.append("Important content removed — preserve non-PII context.")
    if not feedback_parts:
        feedback_parts.append("All contextual PII redacted and document utility preserved!")

    info = {
        "pii_total": len(pii_items),
        "pii_removed": removed,
        "pii_missed": missed,
        "utility_ratio": round(utility_ratio, 4),
        "pii_score": round(pii_score, 4),
        "final_score": final_score,
    }

    return final_score, " | ".join(feedback_parts), info
