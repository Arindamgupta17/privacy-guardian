"""
Typed Pydantic models for the Privacy Guardian environment.
Action, Observation, and State — required by OpenEnv spec.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ─────────────────────────────────────────────
# ACTION
# ─────────────────────────────────────────────

class RedactionAction(BaseModel):
    """
    The agent submits a redacted version of the document.
    All PII should be replaced with [REDACTED] or a category tag
    like [NAME], [EMAIL], [PHONE], [CREDIT_CARD], [ADDRESS].
    """
    redacted_text: str = Field(
        ...,
        description="The full document text with PII replaced by redaction tags."
    )


# ─────────────────────────────────────────────
# OBSERVATION
# ─────────────────────────────────────────────

class RedactionObservation(BaseModel):
    """
    What the agent sees at each step.
    """
    document: str = Field(
        ...,
        description="The original document text containing PII to be redacted."
    )
    task_name: str = Field(
        ...,
        description="Current task: pattern_redaction | contextual_redaction | utility_preserving_redaction"
    )
    task_description: str = Field(
        ...,
        description="Natural language description of what the agent must do."
    )
    pii_categories: List[str] = Field(
        ...,
        description="List of PII categories the agent should look for in this task."
    )
    step: int = Field(..., description="Current step number within the episode.")
    last_reward: float = Field(
        0.0,
        description="Reward from the previous step. 0.0 at episode start."
    )
    feedback: Optional[str] = Field(
        None,
        description="Human-readable feedback on the last redaction attempt."
    )


# ─────────────────────────────────────────────
# STATE
# ─────────────────────────────────────────────

class RedactionState(BaseModel):
    """
    Full internal state of the environment — returned by state() endpoint.
    """
    episode_id: str = Field(..., description="Unique identifier for this episode.")
    task_name: str = Field(..., description="Active task name.")
    step: int = Field(..., description="Current step count.")
    max_steps: int = Field(..., description="Maximum steps allowed per episode.")
    done: bool = Field(..., description="Whether the episode has ended.")
    total_reward: float = Field(..., description="Cumulative reward so far.")
    pii_items_total: int = Field(..., description="Total PII items planted in the document.")
    pii_items_found: int = Field(..., description="PII items successfully redacted so far.")
    last_action: Optional[str] = Field(None, description="Last redacted text submitted.")


# ─────────────────────────────────────────────
# STEP RESULT  (returned by /step endpoint)
# ─────────────────────────────────────────────

class StepResult(BaseModel):
    observation: RedactionObservation
    reward: float = Field(..., description="Reward for this step, in [0.0, 1.0].")
    done: bool = Field(..., description="True if the episode is over.")
    info: Dict[str, Any] = Field(default_factory=dict, description="Extra diagnostic info.")


# ─────────────────────────────────────────────
# RESET RESULT (returned by /reset endpoint)
# ─────────────────────────────────────────────

class ResetResult(BaseModel):
    observation: RedactionObservation
