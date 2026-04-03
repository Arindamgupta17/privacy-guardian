"""
Inference Script — Privacy Guardian Environment
================================================
MANDATORY FORMAT — do not deviate:
  [START] task=<task_name> env=<benchmark> model=<model_name>
  [STEP]  step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
  [END]   success=<true|false> steps=<n> rewards=<r1,r2,...,rn>

Environment variables required:
  API_BASE_URL   — LLM API endpoint
  MODEL_NAME     — model identifier
  HF_TOKEN       — API key
  IMAGE_NAME     — Docker image name (if using from_docker_image)
"""

import asyncio
import os
import textwrap
from typing import List, Optional

import httpx
from openai import OpenAI

# ── Configuration ─────────────────────────────────────────────────────────────
API_KEY      = os.getenv("HF_TOKEN") or os.getenv("API_KEY")
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME   = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
ENV_BASE_URL = os.getenv("ENV_BASE_URL", "http://localhost:7860")

TASK_NAMES = [
    "pattern_redaction",
    "contextual_redaction",
    "utility_preserving_redaction",
]
BENCHMARK   = "privacy-guardian-env"
MAX_STEPS   = 3
TEMPERATURE = 0.2   # Low — redaction needs precision, not creativity
MAX_TOKENS  = 1000
SUCCESS_SCORE_THRESHOLD = 0.5

SYSTEM_PROMPT = textwrap.dedent("""
    You are an expert Data Privacy Officer specializing in GDPR and HIPAA compliance.
    Your task is to redact Personally Identifiable Information (PII) from documents.

    Rules:
    1. Replace each PII item with an appropriate tag:
       - Person names → [NAME]
       - Email addresses → [EMAIL]
       - Phone numbers → [PHONE]
       - Credit/debit card numbers → [CREDIT_CARD]
       - Aadhaar / national ID numbers → [AADHAAR]
       - Physical addresses → [ADDRESS]
       - Other IDs (PAN, employee ID) → [ID]
    2. Preserve ALL non-PII content exactly — do not remove medical terms,
       financial figures, business context, or analytical information.
    3. Return ONLY the redacted document text. No explanations, no preamble.
    4. Do not leave the document blank — only replace PII tokens, keep everything else.
""").strip()


# ── Logging helpers ────────────────────────────────────────────────────────────
def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    # Truncate action to avoid huge log lines
    action_preview = action[:80].replace("\n", " ") if action else ""
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(
        f"[STEP] step={step} action={action_preview!r} reward={reward:.2f} "
        f"done={done_val} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} rewards={rewards_str}",
        flush=True,
    )


# ── LLM call ──────────────────────────────────────────────────────────────────
def get_redacted_text(
    client: OpenAI,
    document: str,
    task_description: str,
    pii_categories: List[str],
    feedback: Optional[str],
    step: int,
) -> str:
    categories_str = ", ".join(pii_categories)
    user_prompt = textwrap.dedent(f"""
        Task: {task_description}

        PII categories to redact: {categories_str}

        Previous feedback: {feedback or 'None — this is your first attempt.'}

        Document to redact:
        ---
        {document}
        ---

        Return ONLY the redacted document. No explanation.
    """).strip()

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            stream=False,
        )
        text = (completion.choices[0].message.content or "").strip()
        return text if text else document  # fallback: return original if empty
    except Exception as exc:
        print(f"[DEBUG] Model request failed: {exc}", flush=True)
        return document  # safe fallback


# ── Environment HTTP client ────────────────────────────────────────────────────
async def env_reset(http: httpx.AsyncClient, task_name: str) -> dict:
    resp = await http.post(f"{ENV_BASE_URL}/reset", params={"task_name": task_name})
    resp.raise_for_status()
    return resp.json()


async def env_step(http: httpx.AsyncClient, redacted_text: str) -> dict:
    resp = await http.post(
        f"{ENV_BASE_URL}/step",
        json={"redacted_text": redacted_text},
        timeout=30.0,
    )
    resp.raise_for_status()
    return resp.json()


# ── Main loop ──────────────────────────────────────────────────────────────────
async def run_task(client: OpenAI, http: httpx.AsyncClient, task_name: str) -> dict:
    all_rewards: List[float] = []
    steps_taken = 0
    success = False

    log_start(task=task_name, env=BENCHMARK, model=MODEL_NAME)

    try:
        result = await env_reset(http, task_name)
        obs = result["observation"]

        for step in range(1, MAX_STEPS + 1):
            if result.get("done", False):
                break

            redacted = get_redacted_text(
                client=client,
                document=obs["document"],
                task_description=obs["task_description"],
                pii_categories=obs["pii_categories"],
                feedback=obs.get("feedback"),
                step=step,
            )

            step_result = await env_step(http, redacted)
            reward = step_result.get("reward", 0.0)
            done   = step_result.get("done", False)
            error  = None

            all_rewards.append(reward)
            steps_taken = step

            log_step(step=step, action=redacted, reward=reward, done=done, error=error)

            obs = step_result["observation"]
            result = step_result

            if done:
                break

        avg_score = sum(all_rewards) / len(all_rewards) if all_rewards else 0.0
        success = avg_score >= SUCCESS_SCORE_THRESHOLD

    except Exception as exc:
        print(f"[DEBUG] Task {task_name} error: {exc}", flush=True)
        all_rewards = all_rewards or [0.0]

    log_end(success=success, steps=steps_taken, rewards=all_rewards)
    return {"task": task_name, "rewards": all_rewards, "success": success}


async def main() -> None:
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

    async with httpx.AsyncClient(timeout=60.0) as http:
        # Wait for environment to be ready
        for attempt in range(10):
            try:
                resp = await http.get(f"{ENV_BASE_URL}/health")
                if resp.status_code == 200:
                    break
            except Exception:
                pass
            await asyncio.sleep(2)

        # Run all 3 tasks sequentially
        for task_name in TASK_NAMES:
            await run_task(client, http, task_name)


if __name__ == "__main__":
    asyncio.run(main())
