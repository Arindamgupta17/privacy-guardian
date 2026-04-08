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

TASK_ORDER = ["pattern_redaction", "contextual_redaction", "utility_preserving_redaction"]

MIN_SCORE = 0.05
MAX_SCORE = 0.95


class PrivacyGuardianEnvironment:
    def __init__(self):
        self._episode_id: str = ""
        self._task_name: str = TASK_ORDER[0]
        self._step: int = 0
        self._max_steps: int = 3
        self._done: bool = True
        self._total_reward: float = 0.0
        self._reward_count: int = 0
        self._current_doc: Optional[dict] = None
        self._last_action: Optional[str] = None
        self._pii_found: int = 0

    def reset(self, task_name: Optional[str] = None) -> ResetResult:
        self._episode_id = str(uuid.uuid4())
        self._task_name = task_name if task_name in TASK_MAP else TASK_ORDER[0]
        self._step = 0
        self._done = False
        self._total_reward = 0.0
        self._reward_count = 0
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
            last_reward=MIN_SCORE,
            feedback="New episode started. Redact all PII.",
        )

        return ResetResult(observation=obs)

    def step(self, action: RedactionAction) -> StepResult:
        if self._done:
            raise RuntimeError("Episode is done. Call reset()")

        task_module = TASK_MAP[self._task_name]
        config = task_module.get_task_config()

        original_text = self._current_doc["text"]
        redacted_text = action.redacted_text

        reward, feedback, info = task_module.score(
            original=original_text,
            redacted=redacted_text,
            doc=self._current_doc,
        )

        # ✅ FINAL FIX: ONLY ONE SAFE CLAMP
        reward = max(MIN_SCORE, min(MAX_SCORE, float(reward)))

        self._total_reward += reward
        self._reward_count += 1

        # Step progression
        if self._step >= self._max_steps:
            self._done = True
            next_doc = self._current_doc
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
            last_reward=reward,  # ✅ NO ROUNDING
            feedback=feedback,
        )

        return StepResult(
            observation=obs,
            reward=reward,  # ✅ RAW SAFE VALUE
            done=self._done,
            info=info,
        )

    def state(self) -> RedactionState:
        pii_total = len(self._current_doc["pii_items"]) if self._current_doc else 0

        avg_reward = (
            max(MIN_SCORE, min(MAX_SCORE, self._total_reward / self._reward_count))
            if self._reward_count > 0
            else MIN_SCORE
        )

        return RedactionState(
            episode_id=self._episode_id,
            task_name=self._task_name,
            step=self._step,
            max_steps=self._max_steps,
            done=self._done,
            total_reward=avg_reward,
            pii_items_total=pii_total,
            pii_items_found=self._pii_found,
            last_action=self._last_action,
        )