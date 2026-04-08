"""
Task 3 — HARD: Utility-Preserving Redaction
Scores strictly in (0.05, 0.95).
"""

from typing import Dict, List, Tuple

HARD_DOCUMENTS: List[Dict] = [
    {
        "id": "hard_001",
        "text": "Rohit Sharma has diabetes and is prescribed Metformin.",
        "pii_items": ["Rohit Sharma"],
        "utility_keywords": ["diabetes", "metformin"],
        "forbidden_removals": ["diabetes", "metformin"],
        "min_length_ratio": 0.5,
    }
]

MIN_SCORE = 0.05
MAX_SCORE = 0.95


def clamp(value: float) -> float:
    return round(max(MIN_SCORE, min(MAX_SCORE, float(value))), 4)

def get_task_config() -> Dict:
    return {
        "name": "utility_preserving_redaction",
        "description": "Redact PII while preserving analytical content.",
        "pii_categories": ["NAME","CONTACT","ADDRESS","ID","DOB"],
        "max_steps": 3,
    }

def get_document(step: int) -> Dict:
    return HARD_DOCUMENTS[(step - 1) % len(HARD_DOCUMENTS)]

def score(original: str, redacted: str, doc: Dict) -> Tuple[float, str, Dict]:

    # ✅ FIXED exploit guard (CRITICAL)
    if len(redacted.strip()) < 0.30 * len(original):
        final_score = clamp(MIN_SCORE)
        return final_score, "Over-redaction: document too short.", {
            "exploit": "over_redaction",
            "final_score": final_score
        }

    feedback_parts = []
    redacted_lower = redacted.lower()

    # A: PII removal
    pii_items = doc["pii_items"]
    removed, missed = 0, []

    for item in pii_items:
        if item.lower() not in redacted_lower:
            removed += 1
        else:
            missed.append(item)

    pii_ratio = removed / len(pii_items) if pii_items else MIN_SCORE

    if missed:
        feedback_parts.append(f"PII still present: {missed[:2]}")

    # B: Utility preservation
    utility_keywords = doc["utility_keywords"]
    found_kw = [kw for kw in utility_keywords if kw.lower() in redacted_lower]
    utility_ratio = len(found_kw) / len(utility_keywords) if utility_keywords else MIN_SCORE

    if utility_ratio < 0.75:
        feedback_parts.append("Lost important keywords")

    # C: Forbidden removal
    forbidden = doc.get("forbidden_removals", [])
    preserved = [w for w in forbidden if w.lower() in redacted_lower]
    forbidden_ratio = len(preserved) / len(forbidden) if forbidden else MIN_SCORE

    if forbidden_ratio < 0.80:
        feedback_parts.append("Over-redacted important info")

    # D: Length preservation
    min_ratio = doc.get("min_length_ratio", 0.50)
    length_ratio = len(redacted.strip()) / max(len(original), 1)
    length_score = MAX_SCORE if length_ratio >= min_ratio else max(MIN_SCORE, length_ratio / min_ratio)

    if length_score < MAX_SCORE:
        feedback_parts.append("Document too short")

    # Final weighted score
    raw = (
        pii_ratio * 0.35 +
        utility_ratio * 0.35 +
        forbidden_ratio * 0.20 +
        length_score * 0.10
    )

    final_score = clamp(raw)

    if not feedback_parts:
        feedback_parts.append("Excellent redaction")

    info = {
        "pii_missed": missed,
        "final_score": final_score
    }

    # ✅ SAFETY CHECK
    assert MIN_SCORE <= final_score <= MAX_SCORE, f"Invalid score: {final_score}"

    return final_score, " | ".join(feedback_parts), info