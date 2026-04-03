"""
Task 3 — HARD: Utility-Preserving Redaction
============================================
The agent must redact ALL PII but preserve the medical/financial/analytical
value of the document so researchers can still use it.

Example:
  Original:  "Patient Rohit Sharma, 34, diabetic, prescribed Metformin 500mg"
  Bad:       "[REDACTED] [REDACTED] [REDACTED] [REDACTED] [REDACTED]"
  Good:      "[NAME REDACTED], 34, diabetic, prescribed Metformin 500mg"

Grader checks THREE assertions deterministically:
  1. All planted PII names/contacts are gone           (40% weight)
  2. Medical/financial utility keywords still present  (40% weight)
  3. Document length preserved (> 55% of original)     (20% weight)

This makes the grader fully deterministic — no LLM judge required.
"""

from typing import Dict, List, Tuple

HARD_DOCUMENTS: List[Dict] = [
    {
        "id": "hard_001",
        "text": (
            "Patient Medical Record — Research Dataset\n\n"
            "Patient: Rohit Sharma\n"
            "Age: 34\n"
            "Contact: rohit.sharma@gmail.com | 9812345678\n"
            "Address: 15, Lajpat Nagar, New Delhi\n\n"
            "Chief Complaint: Persistent fatigue and increased thirst for 3 months.\n"
            "Diagnosis: Type 2 Diabetes Mellitus\n"
            "HbA1c: 8.4%\n"
            "Fasting Blood Sugar: 186 mg/dL\n"
            "Prescribed: Metformin 500mg twice daily, dietary modifications.\n"
            "Follow-up: 6 weeks.\n"
            "Referred by: Dr. Ananya Singh, City Clinic, Delhi."
        ),
        "pii_items": [
            "Rohit Sharma",
            "rohit.sharma@gmail.com",
            "9812345678",
            "15, Lajpat Nagar, New Delhi",
            "Lajpat Nagar",
            "New Delhi",
            "Dr. Ananya Singh",
            "Ananya Singh",
            "City Clinic",
        ],
        "utility_keywords": [
            "diabetes", "hba1c", "metformin", "fasting", "fatigue",
            "diagnosis", "prescribed", "follow-up", "mg/dl"
        ],
        "min_length_ratio": 0.55,
    },
    {
        "id": "hard_002",
        "text": (
            "Financial Counselling Note — Anonymization Required\n\n"
            "Client: Meenakshi Iyer, 52, self-employed\n"
            "PAN: ABCDE1234F\n"
            "Email: meenakshi.iyer@business.in\n"
            "Phone: 9900112233\n"
            "Address: Flat 7B, Prestige Towers, Koramangala, Bengaluru\n\n"
            "Income: Rs. 18,00,000 per annum\n"
            "Outstanding Loan: Rs. 12,50,000 (Home Loan, HDFC)\n"
            "Credit Score: 742\n"
            "Monthly EMI: Rs. 24,500\n"
            "Risk Profile: Moderate\n"
            "Recommendation: Increase SIP allocation to mutual funds by Rs. 5,000/month.\n"
            "Next review: Q3 2026."
        ),
        "pii_items": [
            "Meenakshi Iyer",
            "Meenakshi",
            "ABCDE1234F",
            "meenakshi.iyer@business.in",
            "9900112233",
            "Flat 7B, Prestige Towers, Koramangala, Bengaluru",
            "Koramangala",
            "Bengaluru",
        ],
        "utility_keywords": [
            "income", "loan", "credit score", "emi", "sip", "mutual funds",
            "risk", "recommendation", "hdfc", "annum"
        ],
        "min_length_ratio": 0.55,
    },
    {
        "id": "hard_003",
        "text": (
            "HR Incident Report — Confidential\n\n"
            "Reported by: Sunil Mathew (Employee ID: EMP4421)\n"
            "Email: sunil.mathew@company.com\n"
            "Department: Engineering\n"
            "Date: 02-Apr-2026\n\n"
            "Nature of Incident: Alleged workplace harassment by a team lead.\n"
            "Description: The employee reported that on 28-Mar-2026, during a team "
            "meeting, a senior colleague made repeated negative comments about his "
            "performance in front of the team, causing distress.\n"
            "Witnesses: Pooja Reddy, Arjun Nair (both present at the meeting)\n"
            "Action Taken: HR has initiated a formal inquiry.\n"
            "Status: Under investigation.\n"
            "Next Steps: Interview of witnesses scheduled for 10-Apr-2026."
        ),
        "pii_items": [
            "Sunil Mathew",
            "Sunil",
            "EMP4421",
            "sunil.mathew@company.com",
            "Pooja Reddy",
            "Pooja",
            "Arjun Nair",
            "Arjun",
        ],
        "utility_keywords": [
            "harassment", "incident", "investigation", "hr", "inquiry",
            "engineering", "performance", "witnesses", "department"
        ],
        "min_length_ratio": 0.55,
    },
]


def get_task_config() -> Dict:
    return {
        "name": "utility_preserving_redaction",
        "description": (
            "Redact all PII (names, contacts, IDs, specific addresses) from this "
            "medical/financial/HR document, but PRESERVE the analytical content. "
            "A researcher must still be able to use this document after redaction. "
            "Bad: removing diagnosis, medication, income, or incident type. "
            "Good: replacing names with [NAME], contacts with [CONTACT], "
            "addresses with [ADDRESS], while keeping all clinical/financial/HR facts. "
            "Your score depends on: (1) all PII removed, (2) utility keywords intact, "
            "(3) document length reasonably preserved."
        ),
        "pii_categories": ["NAME", "CONTACT", "ADDRESS", "ID"],
        "max_steps": 3,
    }


def get_document(step: int) -> Dict:
    idx = (step - 1) % len(HARD_DOCUMENTS)
    return HARD_DOCUMENTS[idx]


def score(original: str, redacted: str, doc: Dict) -> Tuple[float, str, Dict]:
    """
    Three deterministic assertions:
      A) PII removal score        — 40%
      B) Utility keyword score    — 40%
      C) Length preservation      — 20%
    """
    feedback_parts = []
    info = {}

    # ── Assertion A: PII removal ───────────────────────────────────────────────
    pii_items: List[str] = doc["pii_items"]
    removed = 0
    missed = []
    for item in pii_items:
        if item.lower() not in redacted.lower():
            removed += 1
        else:
            missed.append(item)

    pii_score = removed / len(pii_items) if pii_items else 1.0
    info["pii_removed"] = removed
    info["pii_total"] = len(pii_items)
    info["pii_missed"] = missed

    if missed:
        feedback_parts.append(f"PII still present: {missed[:3]}{'...' if len(missed) > 3 else ''}")

    # ── Assertion B: Utility keyword preservation ──────────────────────────────
    utility_keywords: List[str] = doc["utility_keywords"]
    keywords_found = [kw for kw in utility_keywords if kw.lower() in redacted.lower()]
    utility_score = len(keywords_found) / len(utility_keywords) if utility_keywords else 1.0
    info["utility_keywords_present"] = len(keywords_found)
    info["utility_keywords_total"] = len(utility_keywords)
    info["utility_score"] = round(utility_score, 4)

    if utility_score < 0.75:
        missing_kw = [kw for kw in utility_keywords if kw.lower() not in redacted.lower()]
        feedback_parts.append(f"Lost utility keywords: {missing_kw[:3]} — these must be preserved for research use.")

    # ── Assertion C: Length preservation ──────────────────────────────────────
    min_ratio: float = doc.get("min_length_ratio", 0.55)
    length_ratio = len(redacted.strip()) / max(len(original), 1)
    length_ok = length_ratio >= min_ratio
    length_score = 1.0 if length_ok else max(0.0, length_ratio / min_ratio)
    info["length_ratio"] = round(length_ratio, 4)
    info["length_ok"] = length_ok

    if not length_ok:
        feedback_parts.append(
            f"Document too short ({length_ratio:.0%} of original, minimum {min_ratio:.0%}). "
            "Do not remove non-PII content."
        )

    # ── Final score ────────────────────────────────────────────────────────────
    final_score = min(1.0, round(
        pii_score    * 0.40 +
        utility_score * 0.40 +
        length_score  * 0.20,
        4
    ))
    info["final_score"] = final_score

    if not feedback_parts:
        feedback_parts.append(
            "Perfect utility-preserving redaction! All PII removed, analytical content intact."
        )

    return final_score, " | ".join(feedback_parts), info
