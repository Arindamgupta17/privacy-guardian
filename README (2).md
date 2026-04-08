# Privacy Guardian — PII Redaction RL Environment

> **OpenEnv-compatible** | **Meta × HuggingFace Hackathon 2026**

An RL environment where an AI agent acts as a **Data Privacy Officer**.
Given real-world style documents (customer support logs, medical records, HR reports),
the agent must identify and redact Personally Identifiable Information (PII)
according to GDPR/HIPAA compliance rules — while preserving the analytical utility
of the document for researchers.

---

## Why This Matters

Every tech company, hospital, fintech, and government agency must legally redact PII
before sharing data with researchers or third parties. Companies currently spend
millions on human redactors. A capable AI agent that can do this accurately and
at scale has immediate real-world value.

---

## Environment Description

The environment presents the agent with text documents containing planted PII.
The agent must return a redacted version of the document. It receives:
- A reward signal proportional to how much PII it successfully removed
- Partial credit for getting some but not all PII
- Penalties for over-redaction (removing useful non-PII content)

Episodes consist of 3 documents per task, with increasing difficulty.

---

## Action Space

```python
class RedactionAction(BaseModel):
    redacted_text: str  # The full document with PII replaced by tags
```

The agent replaces PII with category tags:
- `[NAME]` — person names
- `[EMAIL]` — email addresses
- `[PHONE]` — phone numbers
- `[CREDIT_CARD]` — card numbers
- `[AADHAAR]` — Indian national ID
- `[ADDRESS]` — physical addresses
- `[ID]` — other IDs (PAN, employee ID)

---

## Observation Space

```python
class RedactionObservation(BaseModel):
    document: str            # Document to redact
    task_name: str           # Current task name
    task_description: str    # What the agent must do
    pii_categories: List[str] # PII types to look for
    step: int                # Current step
    last_reward: float       # Reward from previous step
    feedback: Optional[str]  # Feedback on last attempt
```

---

## Tasks

### Task 1 — Pattern Redaction (Easy)
Documents contain clearly formatted, obvious PII: email addresses, phone numbers
(Indian formats including +91 prefix), credit/debit card numbers, Aadhaar numbers.

Any LLM with basic regex or pattern recognition will score well here.

**Expected score for a competent agent:** 0.85–1.0

---

### Task 2 — Contextual Redaction (Medium)
PII is embedded in natural language without obvious formatting:
- "I spoke with Sarah from Delhi about her account"
- "My colleague Anjali had the same problem"

The agent must understand language context to identify names and locations
tied to individuals. Ground-truth PII list is fixed at dataset creation time.

**Expected score for a competent agent:** 0.60–0.85

---

### Task 3 — Utility-Preserving Redaction (Hard)
The agent must redact ALL PII from medical/financial/HR documents but preserve
the analytical content. Removing a patient's name is correct. Removing their
diagnosis is wrong.

Grader checks three deterministic assertions:
1. All planted PII removed (40%)
2. Utility keywords intact (40%)
3. Document length preserved above 55% of original (20%)

**Expected score for a frontier model:** 0.50–0.80

---

## Reward Function

Each step returns a reward strictly in `(0, 1)` (implemented range: `[0.05, 0.95]`):

```
Easy:   reward = (pii_removed/pii_total) * 0.9 + utility_bonus
Medium: reward = (pii_removed/pii_total) * 0.8 + utility_ratio * 0.2
Hard:   reward = pii_score * 0.35 + utility_score * 0.35 + forbidden_score * 0.20 + length_score * 0.10
```

Exploit protection: if `len(redacted) < 30% of original` → reward = 0.05

---

## Setup & Usage

### Local Development

```bash
git clone <your-repo-url>
cd privacy-guardian-env

# Install dependencies
pip install -r server/requirements.txt

# Run server
uvicorn server.app:app --host 0.0.0.0 --port 7860 --reload
```

### Docker

```bash
docker build -t privacy-guardian-env .
docker run -p 7860:7860 privacy-guardian-env
```

### Run Baseline Inference

```bash
export HF_TOKEN=your_token_here
export API_BASE_URL=https://router.huggingface.co/v1
export MODEL_NAME=Qwen/Qwen2.5-72B-Instruct
export ENV_BASE_URL=http://localhost:7860

python inference.py
```

---

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Health check |
| `/reset` | POST | Start new episode (optional `?task_name=`) |
| `/step` | POST | Submit redacted document |
| `/state` | GET | Get current environment state |
| `/tasks` | GET | List all tasks |

---

## Baseline Scores

| Task | Model | Avg Score |
|---|---|---|
| pattern_redaction (easy) | Qwen2.5-72B | ~0.92 |
| contextual_redaction (medium) | Qwen2.5-72B | ~0.67 |
| utility_preserving_redaction (hard) | Qwen2.5-72B | ~0.54 |

---

## Project Structure

```
privacy-guardian-env/
├── inference.py              # Baseline inference script (root — required)
├── openenv.yaml              # OpenEnv manifest
├── Dockerfile                # Container definition
├── README.md
└── server/
    ├── app.py                # FastAPI endpoints
    ├── environment.py        # Core environment logic
    ├── models.py             # Pydantic Action/Observation/State
    ├── requirements.txt
    └── tasks/
        ├── easy.py           # Task 1 grader
        ├── medium.py         # Task 2 grader
        └── hard.py           # Task 3 grader
```
