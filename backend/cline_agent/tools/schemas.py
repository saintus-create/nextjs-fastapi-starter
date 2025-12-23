from __future__ import annotations

from pydantic import BaseModel, Field
from typing import List, Optional, Literal


class PlanStep(BaseModel):
    tool: Literal["file_system", "git", "mcp"]
    command: str
    args: List[str] = Field(default_factory=list)


class Plan(BaseModel):
    steps: List[PlanStep]


class ExecutionResult(BaseModel):
    success: bool
    stdout: Optional[str] = None
    stderr: Optional[str] = None
