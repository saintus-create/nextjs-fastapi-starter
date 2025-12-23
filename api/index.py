# api/index.py
"""FastAPI serverless function for Vercel."""
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add backend to path for local dev
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from cline_agent.agent.core import Agent

app = FastAPI(title="Cline Agent API", version="0.8.0")

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RunTaskRequest(BaseModel):
    task: str
    mode: str = "plan_act"


class HealthResponse(BaseModel):
    status: str
    version: str


@app.get("/api/health")
async def health() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(status="healthy", version="0.8.0")


@app.post("/api/run-task")
async def run_task(payload: RunTaskRequest):
    """
    Execute a task using the cline-agent.
    Mirrors the CLI `cline-agent task` command.
    """
    try:
        agent = Agent()
        result = agent.run_task(payload.task, mode=payload.mode)
        return result.model_dump() if hasattr(result, "model_dump") else result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/config")
async def get_config():
    """Get current agent configuration (secrets masked)."""
    try:
        from cline_agent.config import load_config
        cfg = load_config()
        
        def _mask(obj):
            if isinstance(obj, dict):
                return {
                    k: "***" if "api_key" in k.lower() and v else _mask(v)
                    for k, v in obj.items()
                }
            if isinstance(obj, list):
                return [_mask(i) for i in obj]
            return obj
        
        return {"success": True, "config": _mask(cfg)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
