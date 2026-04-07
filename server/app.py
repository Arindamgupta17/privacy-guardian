"""
Privacy Guardian — FastAPI Server
===================================
Exposes /reset, /step, /state, /health, /metadata, /schema, /mcp endpoints.
Fully compliant with OpenEnv spec.

Environment variables:
  ENV_ENABLE_WEB_INTERFACE=true   Enable the visual dashboard UI (default: true)
"""

import os
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from .environment import PrivacyGuardianEnvironment
from .models import (
    RedactionAction,
    RedactionState,
    ResetResult,
    StepResult,
)

# Config from environment variables
ENABLE_WEB_UI = os.getenv("ENV_ENABLE_WEB_INTERFACE", "true").lower() == "true"
STATIC_DIR    = Path(__file__).parent.parent / "static"

# Global environment instance
env = PrivacyGuardianEnvironment()
_START_TIME = datetime.utcnow()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"===== Application Startup at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} =====")
    print(f"  Web UI enabled: {ENABLE_WEB_UI}")
    env.reset()
    print("  Environment initialized successfully")
    yield


app = FastAPI(
    title="Privacy Guardian — PII Redaction Environment",
    description="An OpenEnv-compatible RL environment for PII redaction. Set ENV_ENABLE_WEB_INTERFACE=true for the visual dashboard.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

if ENABLE_WEB_UI and STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    if ENABLE_WEB_UI:
        index = STATIC_DIR / "index.html"
        if index.exists():
            return HTMLResponse(content=index.read_text(), status_code=200)
    return HTMLResponse(content="<h1>Privacy Guardian</h1><a href='/docs'>API Docs</a>")

# ── FIX 1: /health must return "healthy" ──────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "healthy", "environment": "privacy-guardian-env"}


# ── reset ──────────────────────────────────────────────────────────────────────
@app.post("/reset", response_model=ResetResult)
async def reset(task_name: Optional[str] = None):
    """Reset the environment and return the initial observation."""
    try:
        result = env.reset(task_name=task_name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── step ───────────────────────────────────────────────────────────────────────
@app.post("/step", response_model=StepResult)
async def step(action: RedactionAction):
    """Submit a redacted document and receive reward + next observation."""
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
    """Return the current internal state of the environment."""
    try:
        return env.state()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── FIX 2: /metadata ──────────────────────────────────────────────────────────
@app.get("/metadata")
async def metadata():
    """Environment metadata — required by OpenEnv spec."""
    return {
        "name": "privacy-guardian-env",
        "version": "1.0.0",
        "description": (
            "An RL environment where an AI agent acts as a Data Privacy Officer. "
            "Given documents containing PII, the agent must identify and redact "
            "sensitive data according to GDPR/HIPAA compliance rules while "
            "preserving the analytical utility of the document."
        ),
        "author": "Arindam170304",
        "tags": ["openenv", "pii", "gdpr", "privacy", "compliance", "nlp"],
        "tasks": [
            {"name": "pattern_redaction",            "difficulty": "easy"},
            {"name": "contextual_redaction",         "difficulty": "medium"},
            {"name": "utility_preserving_redaction", "difficulty": "hard"},
        ],
        "reward_range": [0.0, 1.0],
    }


# ── FIX 3: /schema ────────────────────────────────────────────────────────────
@app.get("/schema")
async def schema():
    """Action, Observation and State schemas — required by OpenEnv spec."""
    return {
        "action": {
            "type": "object",
            "properties": {
                "redacted_text": {
                    "type": "string",
                    "description": "Document with PII replaced by tags like [NAME],[EMAIL],[PHONE],[CREDIT_CARD],[AADHAAR],[ADDRESS],[ID].",
                }
            },
            "required": ["redacted_text"],
        },
        "observation": {
            "type": "object",
            "properties": {
                "document":         {"type": "string"},
                "task_name":        {"type": "string"},
                "task_description": {"type": "string"},
                "pii_categories":   {"type": "array", "items": {"type": "string"}},
                "step":             {"type": "integer"},
                "last_reward":      {"type": "number"},
                "feedback":         {"type": "string"},
            },
            "required": ["document", "task_name", "task_description", "pii_categories", "step", "last_reward"],
        },
        "state": {
            "type": "object",
            "properties": {
                "episode_id":      {"type": "string"},
                "task_name":       {"type": "string"},
                "step":            {"type": "integer"},
                "max_steps":       {"type": "integer"},
                "done":            {"type": "boolean"},
                "total_reward":    {"type": "number"},
                "pii_items_total": {"type": "integer"},
                "pii_items_found": {"type": "integer"},
                "last_action":     {"type": "string"},
            },
            "required": ["episode_id", "task_name", "step", "max_steps", "done", "total_reward"],
        },
    }


# ── FIX 4: /mcp ───────────────────────────────────────────────────────────────
@app.post("/mcp")
async def mcp(request: Dict[str, Any] = {}):
    """MCP JSON-RPC 2.0 endpoint — required by OpenEnv spec."""
    method = request.get("method", "")
    req_id = request.get("id", 1)
    params = request.get("params", {})

    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": [
                    {
                        "name": "reset",
                        "description": "Reset the environment and get a new document to redact.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "task_name": {
                                    "type": "string",
                                    "enum": ["pattern_redaction", "contextual_redaction", "utility_preserving_redaction"],
                                }
                            },
                        },
                    },
                    {
                        "name": "step",
                        "description": "Submit a redacted document and receive a reward score.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "redacted_text": {"type": "string"}
                            },
                            "required": ["redacted_text"],
                        },
                    },
                    {
                        "name": "state",
                        "description": "Get the current environment state.",
                        "inputSchema": {"type": "object", "properties": {}},
                    },
                ]
            },
        }

    if method == "tools/call":
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})
        try:
            if tool_name == "reset":
                result = env.reset(task_name=arguments.get("task_name"))
                return {"jsonrpc": "2.0", "id": req_id,
                        "result": {"content": [{"type": "text", "text": result.model_dump_json()}]}}
            elif tool_name == "step":
                action = RedactionAction(redacted_text=arguments.get("redacted_text", ""))
                result = env.step(action)
                return {"jsonrpc": "2.0", "id": req_id,
                        "result": {"content": [{"type": "text", "text": result.model_dump_json()}]}}
            elif tool_name == "state":
                result = env.state()
                return {"jsonrpc": "2.0", "id": req_id,
                        "result": {"content": [{"type": "text", "text": result.model_dump_json()}]}}
            else:
                return {"jsonrpc": "2.0", "id": req_id,
                        "error": {"code": -32601, "message": f"Tool not found: {tool_name}"}}
        except Exception as e:
            return {"jsonrpc": "2.0", "id": req_id,
                    "error": {"code": -32000, "message": str(e)}}

    # Default — return server capabilities
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "privacy-guardian-env", "version": "1.0.0"},
        },
    }


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


# ── Entry point for pyproject.toml [project.scripts] ──────────────────────────
def main():
    """Main entry point — used by openenv multi-mode deployment."""
    import uvicorn
    uvicorn.run(
        "server.app:app",
        host="0.0.0.0",
        port=7860,
        workers=1,
        log_level="info",
    )


if __name__ == "__main__":
    main()
