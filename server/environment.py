"""
Privacy Guardian — Core Environment Logic
==========================================
Implements the OpenEnv Environment base:
  reset()  → ResetResult
  step()   → StepResult
  state()  → RedactionState
"""

import uuid
from typing import Optional

from .models import (
    RedactionAction,
    RedactionObservation,
    RedactionState,
    ResetResult,
    StepResult,
)
from .tasks import TASK_MAP

# Task order for sequential episode flow
TASK_ORDER = ["pattern_redaction", "contextual_redaction", "utility_preserving_redaction"]
STRICT_MIN_REWARD = 0.05
STRICT_MAX_REWARD = 0.95


def _clamp_strict_score(value: float) -> float:
    clamped = max(STRICT_MIN_REWARD, min(STRICT_MAX_REWARD, float(value)))
    rounded = round(clamped, 4)
    return max(STRICT_MIN_REWARD, min(STRICT_MAX_REWARD, rounded))


class PrivacyGuardianEnvironment:
    def __init__(self):
        self._episode_id: str = ""
        self._task_name: str = TASK_ORDER[0]
        self._step: int = 0
        self._max_steps: int = 3
        self._done: bool = True
        self._total_reward: float = 0.0
        self._current_doc: Optional[dict] = None
        self._last_action: Optional[str] = None
        self._pii_found: int = 0

    # ── reset ──────────────────────────────────────────────────────────────────
    def reset(self, task_name: Optional[str] = None) -> ResetResult:
        self._episode_id = str(uuid.uuid4())
        self._task_name = task_name if task_name in TASK_MAP else TASK_ORDER[0]
        self._step = 0
        self._done = False
        self._total_reward = 0.0
        self._last_action = None
        self._pii_found = 0

        task_module = TASK_MAP[self._task_name]
        config = task_module.get_task_config()
        self._max_steps = config["max_steps"]

        self._step += 1
        self._current_doc = task_module.get_document(self._step)

        obs = RedactionObservation(
            document=self._current_doc["text"],
            task_name=self._task_name,
            task_description=config["description"],
            pii_categories=config["pii_categories"],
            step=self._step,
            last_reward=STRICT_MIN_REWARD,
            feedback="New episode started. Redact all PII from the document above.",
        )
        return ResetResult(observation=obs)

    # ── step ───────────────────────────────────────────────────────────────────
    def step(self, action: RedactionAction) -> StepResult:
        if self._done:
            raise RuntimeError("Episode is done. Call reset() to start a new episode.")

        task_module = TASK_MAP[self._task_name]
        config = task_module.get_task_config()

        original_text = self._current_doc["text"]
        redacted_text = action.redacted_text
        self._last_action = redacted_text

        reward, feedback, info = task_module.score(
            original=original_text,
            redacted=redacted_text,
            doc=self._current_doc,
        )

        reward = _clamp_strict_score(reward)

        self._total_reward += reward
        self._pii_found += info.get("pii_removed", 0)

        # Move to next document or end episode
        if self._step >= self._max_steps:
            self._done = True
            next_doc = self._current_doc  # stay on same for final obs
        else:
            self._step += 1
            next_doc = task_module.get_document(self._step)
            self._current_doc = next_doc

        obs = RedactionObservation(
            document=next_doc["text"] if not self._done else original_text,
            task_name=self._task_name,
            task_description=config["description"],
            pii_categories=config["pii_categories"],
            step=self._step,
            last_reward=round(reward, 4),
            feedback=feedback,
        )

        return StepResult(
            observation=obs,
            reward=reward,
            done=self._done,
            info=info,
        )

    # ── state ──────────────────────────────────────────────────────────────────
    def state(self) -> RedactionState:
        pii_total = len(self._current_doc["pii_items"]) if self._current_doc else 0
        return RedactionState(
            episode_id=self._episode_id,
            task_name=self._task_name,
            step=self._step,
            max_steps=self._max_steps,
            done=self._done,
            total_reward=round(self._total_reward, 4),
            pii_items_total=pii_total,
            pii_items_found=self._pii_found,
            last_action=self._last_action,
        )
