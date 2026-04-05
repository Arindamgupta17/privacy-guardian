"""
Inference Script — Privacy Guardian Environment
================================================
MANDATORY FORMAT — do not deviate:
  [START] task=<task_name> env=<benchmark> model=<model_name>
  [STEP]  step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
  [END]   success=<true|false> steps=<n> rewards=<r1,r2,...,rn>

Environment variables required:
  API_BASE_URL   The API endpoint for the LLM
  MODEL_NAME     The model identifier to use for inference
  HF_TOKEN       Your Hugging Face / API key
  IMAGE_NAME     Docker image name (if using from_docker_image())
  ENV_BASE_URL   Environment base URL (default: http://localhost:7860)
"""

import asyncio
import os
import textwrap
from typing import List, Optional

import httpx
from openai import OpenAI

# ── Config ────────────────────────────────────────────────────────────────────
API_KEY      = os.getenv("HF_TOKEN") or os.getenv("API_KEY")
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME   = os.getenv("MODEL_NAME",   "Qwen/Qwen2.5-72B-Instruct")
ENV_BASE_URL = os.getenv("ENV_BASE_URL", "http://localhost:7860")
IMAGE_NAME   = os.getenv("IMAGE_NAME")   # Docker image name if using from_docker_image()

TASK_NAMES = [
    "pattern_redaction",
    "contextual_redaction",
    "utility_preserving_redaction",
]

BENCHMARK               = "privacy-guardian-env"
MAX_STEPS               = 3
TEMPERATURE             = 0.2
MAX_TOKENS              = 1000
SUCCESS_SCORE_THRESHOLD = 0.5

SYSTEM_PROMPT = textwrap.dedent("""
    You are an expert Data Privacy Officer specializing in GDPR and HIPAA compliance.
    Your task is to redact Personally Identifiable Information (PII) from documents.

    Rules:
    1. Replace each PII item with an appropriate tag:
       - Person names           -> [NAME]
       - Email addresses        -> [EMAIL]
       - Phone numbers          -> [PHONE]
       - Credit/debit card nos  -> [CREDIT_CARD]
       - Aadhaar / national IDs -> [AADHAAR]
       - Physical addresses     -> [ADDRESS]
       - Other IDs (PAN, EmpID) -> [ID]
    2. Preserve ALL non-PII content — medical terms, financial figures,
       business context, and analytical information must remain intact.
    3. Return ONLY the redacted document text. No explanation, no preamble.
    4. Never leave the document blank — only replace PII tokens.
""").strip()


# ── Logging — strict format required by OpenEnv spec ──────────────────────────
def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    action_preview = action[:80].replace("\n", " ") if action else ""
    error_val = error if error else "null"
    done_val  = str(done).lower()
    print(
        f"[STEP] step={step} action={action_preview!r} "
        f"reward={reward:.2f} done={done_val} error={error_val}",
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
) -> str:
    user_prompt = textwrap.dedent(f"""
        Task: {task_description}
        PII categories to redact: {', '.join(pii_categories)}
        Previous feedback: {feedback or 'None — first attempt.'}

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
                {"role": "user",   "content": user_prompt},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            stream=False,
        )
        text = (completion.choices[0].message.content or "").strip()
        return text if text else document
    except Exception as exc:
        print(f"[DEBUG] Model request failed: {exc}", flush=True)
        return document


# ── Environment HTTP calls ────────────────────────────────────────────────────
async def env_reset(http: httpx.AsyncClient, task_name: str) -> dict:
    resp = await http.post(
        f"{ENV_BASE_URL}/reset",
        params={"task_name": task_name},
        timeout=30.0,
    )
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


async def env_close(http: httpx.AsyncClient) -> None:
    """Called after every episode — mirrors env.close() in the OpenEnv pattern."""
    try:
        await http.post(f"{ENV_BASE_URL}/reset", timeout=10.0)
        print("[DEBUG] env.close() — environment reset for cleanup", flush=True)
    except Exception as e:
        print(f"[DEBUG] env.close() error (non-critical): {e}", flush=True)


async def env_health(http: httpx.AsyncClient) -> bool:
    try:
        resp = await http.get(f"{ENV_BASE_URL}/health", timeout=10.0)
        return resp.status_code == 200
    except Exception:
        return False


# ── Single task loop ──────────────────────────────────────────────────────────
async def run_task(
    client: OpenAI,
    http: httpx.AsyncClient,
    task_name: str,
) -> dict:
    rewards: List[float] = []
    steps_taken = 0
    success = False

    log_start(task=task_name, env=BENCHMARK, model=MODEL_NAME)

    try:
        result = await env_reset(http, task_name)
        obs    = result["observation"]

        for step in range(1, MAX_STEPS + 1):
            if result.get("done", False):
                break

            redacted = get_redacted_text(
                client=client,
                document=obs["document"],
                task_description=obs["task_description"],
                pii_categories=obs["pii_categories"],
                feedback=obs.get("feedback"),
            )

            step_result = await env_step(http, redacted)
            reward = float(step_result.get("reward", 0.0))
            done   = step_result.get("done", False)
            error  = None

            rewards.append(reward)
            steps_taken = step

            log_step(step=step, action=redacted, reward=reward, done=done, error=error)

            obs    = step_result["observation"]
            result = step_result

            if done:
                break

        avg = sum(rewards) / len(rewards) if rewards else 0.0
        success = avg >= SUCCESS_SCORE_THRESHOLD

    except Exception as exc:
        print(f"[DEBUG] Task {task_name} error: {exc}", flush=True)
        rewards = rewards or [0.0]

    finally:
        # Always close — mirrors env.close() from the dashboard sample script
        try:
            await env_close(http)
        except Exception as e:
            print(f"[DEBUG] env.close() error (container cleanup): {e}", flush=True)

    log_end(success=success, steps=steps_taken, rewards=rewards)
    return {"task": task_name, "rewards": rewards, "success": success}


# ── Main ──────────────────────────────────────────────────────────────────────
async def main() -> None:
    print(f"[DEBUG] ENV_BASE_URL={ENV_BASE_URL}", flush=True)
    print(f"[DEBUG] API_BASE_URL={API_BASE_URL}", flush=True)
    print(f"[DEBUG] MODEL_NAME={MODEL_NAME}", flush=True)
    print(f"[DEBUG] IMAGE_NAME={IMAGE_NAME}", flush=True)

    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

    async with httpx.AsyncClient(timeout=60.0) as http:

        # Wait for environment to be healthy
        print("[DEBUG] Waiting for environment to be ready...", flush=True)
        for attempt in range(15):
            if await env_health(http):
                print(f"[DEBUG] Environment ready after {attempt+1} attempts", flush=True)
                break
            await asyncio.sleep(2)
        else:
            print("[DEBUG] WARNING: Environment health check failed — proceeding anyway", flush=True)

        # Run all 3 tasks sequentially
        all_results = []
        for task_name in TASK_NAMES:
            result = await run_task(client, http, task_name)
            all_results.append(result)
            await asyncio.sleep(1)

        # Summary
        print("\n[DEBUG] ====== SUMMARY ======", flush=True)
        for r in all_results:
            avg = sum(r["rewards"]) / len(r["rewards"]) if r["rewards"] else 0.0
            print(f"[DEBUG] {r['task']}: avg={avg:.2f} success={r['success']}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
