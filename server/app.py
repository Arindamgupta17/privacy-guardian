"""
Privacy Guardian — FastAPI Server
===================================
Exposes /reset, /step, /state, /health endpoints.
Compliant with OpenEnv spec.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .environment import PrivacyGuardianEnvironment
from .models import (
    RedactionAction,
    RedactionState,
    ResetResult,
    StepResult,
)

# Global environment instance (single session for HF Spaces deployment)
env = PrivacyGuardianEnvironment()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize environment on startup."""
    env.reset()
    yield


app = FastAPI(
    title="Privacy Guardian — PII Redaction Environment",
    description=(
        "An OpenEnv-compatible RL environment where an AI agent acts as a "
        "Data Privacy Officer, redacting PII from documents according to "
        "GDPR/HIPAA compliance rules."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok", "environment": "privacy-guardian-env"}


# ── reset ──────────────────────────────────────────────────────────────────────
@app.post("/reset", response_model=ResetResult)
async def reset(task_name: Optional[str] = None):
    """
    Reset the environment and return the initial observation.
    Optionally specify task_name:
      - pattern_redaction         (easy)
      - contextual_redaction      (medium)
      - utility_preserving_redaction (hard)
    """
    try:
        result = env.reset(task_name=task_name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── step ───────────────────────────────────────────────────────────────────────
@app.post("/step", response_model=StepResult)
async def step(action: RedactionAction):
    """
    Submit a redacted document and receive reward + next observation.
    """
    try:
        result = env.step(action)
        return result
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── state ──────────────────────────────────────────────────────────────────────
@app.get("/state", response_model=RedactionState)
async def state():
    """
    Return the current internal state of the environment.
    """
    try:
        return env.state()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── tasks list ────────────────────────────────────────────────────────────────
@app.get("/tasks")
async def list_tasks():
    """List all available tasks with metadata."""
    return {
        "tasks": [
            {
                "name": "pattern_redaction",
                "difficulty": "easy",
                "description": "Redact obvious PII patterns — emails, phones, credit cards, Aadhaar numbers.",
            },
            {
                "name": "contextual_redaction",
                "difficulty": "medium",
                "description": "Identify and redact PII embedded in natural language conversations.",
            },
            {
                "name": "utility_preserving_redaction",
                "difficulty": "hard",
                "description": "Redact all PII while preserving medical/financial/HR analytical value.",
            },
        ]
    }
