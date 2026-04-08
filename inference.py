import asyncio
import os
import textwrap
from typing import Any, List, Optional

import httpx

API_BASE_URL     = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME       = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
HF_TOKEN         = os.getenv("HF_TOKEN")
API_KEY          = HF_TOKEN or os.getenv("API_KEY")
ENV_BASE_URL     = os.getenv("ENV_BASE_URL", "http://localhost:7860")

TASK_NAMES = [
    "pattern_redaction",
    "contextual_redaction",
    "utility_preserving_redaction",
]

BENCHMARK = "privacy-guardian-env"
MAX_STEPS = 3

MIN_SCORE = 0.05
MAX_SCORE = 0.95


def strict_score(value: float) -> float:
    return max(MIN_SCORE, min(MAX_SCORE, float(value)))


SYSTEM_PROMPT = textwrap.dedent("""
You are an expert Data Privacy Officer.
Redact all PII while preserving useful content.
Return ONLY the redacted text.
""").strip()


# ✅ FIXED LOGGING (NO ROUNDING BUG)

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    action_preview = action[:80].replace("\n", " ") if action else ""
    error_val = error if error else "null"
    done_val  = str(done).lower()

    # ✅ FIX: no 2-decimal rounding
    safe_reward = round(reward, 4)

    print(
        f"[STEP] step={step} action={action_preview!r} "
        f"reward={safe_reward} done={done_val} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, rewards: List[float]) -> None:
    # ✅ FIX: no 2-decimal rounding
    rewards_str = ",".join(str(round(r, 4)) for r in rewards)

    print(
        f"[END] success={str(success).lower()} steps={steps} rewards={rewards_str}",
        flush=True,
    )


async def get_redacted_text(
    client: httpx.AsyncClient,
    document: str,
    task_description: str,
    pii_categories: List[str],
    feedback: Optional[str],
) -> str:
    user_prompt = f"""
Task: {task_description}
PII categories: {', '.join(pii_categories)}
Feedback: {feedback or "None"}

Document:
{document}

Return ONLY redacted text.
"""

    try:
        response = await client.post(
            f"{API_BASE_URL}/chat/completions",
            json={
                "model": MODEL_NAME,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.2,
                "max_tokens": 1000,
            },
            headers={"Authorization": f"Bearer {API_KEY}"},
        )
        response.raise_for_status()
        text = response.json()["choices"][0]["message"]["content"]
        return text.strip() if text else document

    except Exception:
        return document


async def env_reset(http: httpx.AsyncClient, task_name: str) -> dict:
    r = await http.post(f"{ENV_BASE_URL}/reset", params={"task_name": task_name})
    r.raise_for_status()
    return r.json()


async def env_step(http: httpx.AsyncClient, redacted_text: str) -> dict:
    r = await http.post(f"{ENV_BASE_URL}/step", json={"redacted_text": redacted_text})
    r.raise_for_status()
    return r.json()


async def run_task(client: httpx.AsyncClient, http: httpx.AsyncClient, task_name: str):
    rewards = []
    steps_taken = 0

    log_start(task_name, BENCHMARK, MODEL_NAME)

    result = await env_reset(http, task_name)
    obs = result["observation"]

    for step in range(1, MAX_STEPS + 1):
        redacted = await get_redacted_text(
            client,
            obs["document"],
            obs["task_description"],
            obs["pii_categories"],
            obs.get("feedback"),
        )

        step_result = await env_step(http, redacted)

        # ✅ SAFE REWARD
        reward = strict_score(float(step_result["reward"]))
        done = step_result["done"]

        rewards.append(reward)
        steps_taken = step

        log_step(step, redacted, reward, done, None)

        obs = step_result["observation"]

        if done:
            break

    avg = sum(rewards) / len(rewards) if rewards else MIN_SCORE
    success = avg >= 0.5

    log_end(success, steps_taken, rewards)


async def main():
    async with httpx.AsyncClient() as http:
        async with httpx.AsyncClient() as client:
            for task in TASK_NAMES:
                await run_task(client, http, task)


if __name__ == "__main__":
    asyncio.run(main())