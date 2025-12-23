from __future__ import annotations

import json
import structlog
from typing import Optional

from ..llm.providers import LLMRouter
from ..tools.schemas import ExecutionResult

log = structlog.get_logger(__name__)

REFLECTION_SYSTEM = """You are a self-critique assistant.
Given the original task, the executed plan, and the output, decide:
- success: bool (did the plan achieve the goal?)
- retry: bool (should we retry with a revised plan?)
- notes: str (concise reason)
Return JSON only:
{"success": bool, "retry": bool, "notes": str}"""


class ReflectionAuditor:
    def __init__(self, router: LLMRouter):
        self.router = router

    def critique(
        self, task: str, plan_json: str, result: ExecutionResult
    ) -> tuple[bool, bool, str]:
        client = self.router.for_phase("fallback")  # cheaper / faster model
        client.response_model = None
        messages = [
            {"role": "system", "content": REFLECTION_SYSTEM},
            {
                "role": "user",
                "content": f"Task: {task}\nPlan: {plan_json}\nResult: {result.model_dump_json()}",
            },
        ]
        raw = client.generate(messages, temperature=0.2, max_tokens=200)
        try:
            data = json.loads(raw)
            return data["success"], data["retry"], data["notes"]
        except Exception:
            log.warning("Reflection parse failed", raw=raw)
            return result.success, False, "Parse error – assume success"
