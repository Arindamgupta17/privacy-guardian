"""
Task 3 — HARD: Utility-Preserving Redaction
Scores strictly in (0.05, 0.95).
Fix: clamp ONLY final score once, not intermediate values.
"""
from typing import Dict, List, Tuple

HARD_DOCUMENTS: List[Dict] = [
    {
        "id": "hard_001",
        "text": (
            "Patient Medical Record — Research Dataset\n\n"
            "Patient: Rohit Sharma\nAge: 34\n"
            "Contact: rohit.sharma@gmail.com | 9812345678\n"
            "Address: 15, Lajpat Nagar, New Delhi\n\n"
            "Chief Complaint: Persistent fatigue and increased thirst for 3 months.\n"
            "Diagnosis: Type 2 Diabetes Mellitus\nHbA1c: 8.4%\n"
            "Fasting Blood Sugar: 186 mg/dL\n"
            "Prescribed: Metformin 500mg twice daily, dietary modifications.\n"
            "Follow-up: 6 weeks.\n"
            "Referred by: Dr. Ananya Singh, City Clinic, Delhi.\n"
            "Insurance ID: HDFC-MED-2024-88123"
        ),
        "pii_items": ["Rohit Sharma","rohit.sharma@gmail.com","9812345678","15, Lajpat Nagar, New Delhi","Lajpat Nagar","Dr. Ananya Singh","Ananya Singh","City Clinic","HDFC-MED-2024-88123"],
        "utility_keywords": ["diabetes","hba1c","metformin","fasting","fatigue","diagnosis","prescribed","mg/dl","type 2"],
        "forbidden_removals": ["age","34","fatigue","thirst","diagnosis","metformin","follow-up","referred","dietary"],
        "min_length_ratio": 0.50,
    },
    {
        "id": "hard_002",
        "text": (
            "Financial Counselling Note — Anonymization Required\n\n"
            "Client: Meenakshi Iyer, 52, self-employed\n"
            "PAN: ABCDE1234F\nEmail: meenakshi.iyer@business.in\n"
            "Phone: 9900112233\n"
            "Address: Flat 7B, Prestige Towers, Koramangala, Bengaluru\n\n"
            "Income: Rs. 18,00,000 per annum\n"
            "Outstanding Loan: Rs. 12,50,000 (Home Loan, HDFC)\n"
            "Credit Score: 742\nMonthly EMI: Rs. 24,500\n"
            "Risk Profile: Moderate\n"
            "Recommendation: Increase SIP allocation to mutual funds by Rs. 5,000/month.\n"
            "Next review: Q3 2026.\nAdvisor: Prakash Mehta, CFP, Wealth360 Advisors"
        ),
        "pii_items": ["Meenakshi Iyer","Meenakshi","ABCDE1234F","meenakshi.iyer@business.in","9900112233","Flat 7B, Prestige Towers, Koramangala, Bengaluru","Koramangala","Bengaluru","Prakash Mehta","Wealth360 Advisors"],
        "utility_keywords": ["income","loan","credit score","emi","sip","mutual funds","risk","recommendation","hdfc","annum"],
        "forbidden_removals": ["income","loan","credit","emi","sip","risk","moderate","recommendation","annum","52"],
        "min_length_ratio": 0.50,
    },
    {
        "id": "hard_003",
        "text": (
            "HR Incident Report — Confidential\n\n"
            "Reported by: Sunil Mathew (Employee ID: EMP4421)\n"
            "Email: sunil.mathew@company.com\nDepartment: Engineering\n"
            "Date of Incident: 28-Mar-2026\n\n"
            "Nature: Alleged workplace harassment by a senior team lead.\n"
            "Description: During a sprint review meeting, a senior colleague "
            "made repeated derogatory comments about performance in front of "
            "the entire 12-person team, causing significant psychological distress.\n"
            "Witnesses: Pooja Reddy (EMP3312), Arjun Nair (EMP5567)\n"
            "Medical Leave Taken: 2 days (stress-related)\n"
            "Action Taken: HR formal inquiry initiated under Policy HR-09.\n"
            "Status: Under investigation."
        ),
        "pii_items": ["Sunil Mathew","Sunil","EMP4421","sunil.mathew@company.com","Pooja Reddy","Pooja","EMP3312","Arjun Nair","Arjun","EMP5567"],
        "utility_keywords": ["harassment","incident","investigation","hr","inquiry","engineering","performance","witnesses","department","psychological","policy"],
        "forbidden_removals": ["harassment","incident","investigation","engineering","performance","witnesses","department","sprint","meeting","distress"],
        "min_length_ratio": 0.50,
    },
    {
        "id": "hard_004",
        "text": (
            "Clinical Trial Enrollment Record\n\n"
            "Trial ID: CTRI/2026/04/NCT-8812\n"
            "Participant: Kavitha Subramaniam\nDOB: 12-Aug-1985\n"
            "Contact: kavitha.s@healthmail.com | 8765432109\n"
            "Emergency Contact: Ramesh Subramaniam (husband), 9123456780\n\n"
            "Condition: Rheumatoid Arthritis (moderate severity)\n"
            "CRP Level: 18.4 mg/L (elevated)\nESR: 62 mm/hr\n"
            "Current Medication: Hydroxychloroquine 200mg daily\n"
            "Trial Drug: Baricitinib 4mg (JAK inhibitor)\n"
            "Site: Apollo Research Centre, Chennai\n"
            "Principal Investigator: Dr. Venkat Krishnan"
        ),
        "pii_items": ["Kavitha Subramaniam","Kavitha","12-Aug-1985","kavitha.s@healthmail.com","8765432109","Ramesh Subramaniam","Ramesh","9123456780","Apollo Research Centre","Chennai","Dr. Venkat Krishnan","Venkat Krishnan"],
        "utility_keywords": ["rheumatoid","arthritis","crp","esr","hydroxychloroquine","baricitinib","jak","trial","enrollment","mg/l"],
        "forbidden_removals": ["rheumatoid","arthritis","crp","esr","hydroxychloroquine","baricitinib","trial","enrollment","moderate"],
        "min_length_ratio": 0.50,
    },
    {
        "id": "hard_005",
        "text": (
            "Legal Compliance Audit — Data Processing Record\n\n"
            "Data Controller: Prabhash Verma, Chief Privacy Officer\n"
            "Organisation: FinServ Solutions Pvt. Ltd.\n"
            "Auditor: Nalini Chandran, CIPP/E\n"
            "Contact: nalini.c@auditfirm.co.in | 9988776655\n\n"
            "Finding 1: Retention policy non-compliant — customer data stored "
            "beyond the 24-month statutory limit under DPDP Act 2023.\n"
            "Finding 2: Consent records missing for 1,240 data subjects.\n"
            "Finding 3: Cross-border transfer to Singapore entity lacks SCC documentation.\n"
            "Risk Level: HIGH\n"
            "Recommended Action: Immediate deletion of records older than 24 months.\n"
            "Regulatory Exposure: Up to Rs. 250 crore under DPDP Act Section 33."
        ),
        "pii_items": ["Prabhash Verma","Prabhash","Nalini Chandran","Nalini","nalini.c@auditfirm.co.in","9988776655","FinServ Solutions Pvt. Ltd."],
        "utility_keywords": ["retention","consent","dpdp","compliance","audit","cross-border","statutory","risk","deletion","regulatory"],
        "forbidden_removals": ["retention","consent","dpdp","compliance","cross-border","statutory","risk","regulatory","deletion","1,240","24-month"],
        "min_length_ratio": 0.50,
    },
]


def clamp(value: float) -> float:
    """Clamp to strictly (0.05, 0.95) — called ONCE on final score only."""
    return round(max(0.05, min(0.95, float(value))), 4)


def get_task_config() -> Dict:
    return {
        "name": "utility_preserving_redaction",
        "description": (
            "Redact ALL personal identifiers from medical/financial/HR documents "
            "but PRESERVE every piece of analytical content. "
            "Remove: names, emails, phones, IDs, DOB, specific addresses. "
            "Keep: medical terms, financial figures, legal findings, diagnoses, medications. "
            "Scoring: PII removal 35% + utility keywords 35% + non-PII preservation 20% + length 10%."
        ),
        "pii_categories": ["NAME","CONTACT","ADDRESS","ID","DOB"],
        "max_steps": 3,
    }


def get_document(step: int) -> Dict:
    return HARD_DOCUMENTS[(step - 1) % len(HARD_DOCUMENTS)]


def score(original: str, redacted: str, doc: Dict) -> Tuple[float, str, Dict]:
    # Exploit guard
    if len(redacted.strip()) < 0.30 * len(original):
        return 0.05, "Over-redaction: document too short. Preserve non-PII content.", {"exploit": "over_redaction"}

    feedback_parts = []
    redacted_lower = redacted.lower()

    # A: PII removal (35%) — raw ratio, NOT clamped
    pii_items = doc["pii_items"]
    removed, missed = 0, []
    for item in pii_items:
        if item.lower() not in redacted_lower:
            removed += 1
        else:
            missed.append(item)
    pii_ratio = removed / len(pii_items) if pii_items else 0.0
    if missed:
        feedback_parts.append(f"PII still present ({len(missed)}): {missed[:2]}{'...' if len(missed)>2 else ''}")

    # B: Utility keyword preservation (35%) — raw ratio, NOT clamped
    utility_keywords = doc["utility_keywords"]
    found_kw = [kw for kw in utility_keywords if kw.lower() in redacted_lower]
    utility_ratio = len(found_kw) / len(utility_keywords) if utility_keywords else 0.0
    if utility_ratio < 0.75:
        missing_kw = [kw for kw in utility_keywords if kw.lower() not in redacted_lower]
        feedback_parts.append(f"Lost keywords: {missing_kw[:3]} — preserve these.")

    # C: Forbidden removal check (20%) — raw ratio, NOT clamped
    forbidden = doc.get("forbidden_removals", [])
    preserved = [w for w in forbidden if w.lower() in redacted_lower]
    forbidden_ratio = len(preserved) / len(forbidden) if forbidden else 1.0
    if forbidden_ratio < 0.80:
        over_redacted = [w for w in forbidden if w.lower() not in redacted_lower]
        feedback_parts.append(f"Over-redacted non-PII: {over_redacted[:3]}")

    # D: Length preservation (10%) — raw ratio, NOT clamped
    min_ratio = doc.get("min_length_ratio", 0.50)
    length_ratio = len(redacted.strip()) / max(len(original), 1)
    length_score = 1.0 if length_ratio >= min_ratio else max(0.0, length_ratio / min_ratio)
    if length_score < 1.0:
        feedback_parts.append(f"Document too short ({length_ratio:.0%}). Preserve non-PII sentences.")

    # Weighted sum — raw, NOT clamped yet
    raw = (pii_ratio * 0.35 + utility_ratio * 0.35 + forbidden_ratio * 0.20 + length_score * 0.10)

    # Clamp ONCE at the end
    final_score = clamp(raw)

    if not feedback_parts:
        feedback_parts.append("Excellent utility-preserving redaction! All PII removed, analytical content intact.")

    info = {
        "pii_total": len(pii_items),
        "pii_removed": removed,
        "pii_missed": missed,
        "utility_ratio": round(utility_ratio, 4),
        "forbidden_ratio": round(forbidden_ratio, 4),
        "length_score": round(length_score, 4),
        "final_score": final_score,
    }
    return final_score, " | ".join(feedback_parts), info
