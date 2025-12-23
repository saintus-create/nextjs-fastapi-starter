from __future__ import annotations

import structlog
import json
from typing import Any

from ..config import load_config
from ..logging_config import setup_logging
from ..llm.providers import LLMRouter
from ..tools.schemas import Plan, PlanStep, ExecutionResult
from ..tools.file_system import FileSystemTool
from ..tools.git_tool import GitTool
from ..tools.mcp_client import MCPClient
from ..tools.safety_auditor import SafetyAuditor
from ..tools.reflection_auditor import ReflectionAuditor

log = structlog.get_logger(__name__)

# ---------- prompt templates ----------
PLAN_SYSTEM = """You are an autonomous developer agent.
Produce a JSON plan that satisfies the user request.
Each step must use EXACTLY one tool: "file_system", "git", or "mcp".
Allowed commands:
  file_system.[read|write|list_dir]
  git.[status|add|commit]
  mcp.[invoke]
Return JSON matching the schema: {"steps": [{"tool": str, "command": str, "args": list[str]}]}"""

EXEC_SYSTEM = """You are an autonomous developer agent.
Execute the provided JSON plan step-by-step and return a JSON summary:
{"success": bool, "stdout": str|None, "stderr": str|None}"""


class Agent:
    def __init__(self, config: dict | None = None):
        self.cfg = config or load_config()
        setup_logging(self.cfg["logging"]["level"], self.cfg["logging"]["renderer"])
        self.router = LLMRouter(self.cfg)
        self.fs = FileSystemTool(self.cfg["project_root"])
        self.git = GitTool(self.cfg["project_root"])
        self.mcp = MCPClient(self.cfg.get("mcp_server_url", "http://localhost:8000"))
        self.safety = SafetyAuditor()
        self.reflection = ReflectionAuditor(self.router)

    # ---------- high-level API ----------
    def plan(self, task: str) -> Plan:
        client = self.router.for_phase("plan")
        client.response_model = Plan
        messages = [
            {"role": "system", "content": PLAN_SYSTEM},
            {"role": "user", "content": task},
        ]
        log.debug("agent.plan.request", task=task)
        return client.generate_structured(messages)

    def execute(self, plan: Plan) -> ExecutionResult:
        client = self.router.for_phase("execute")
        client.response_model = ExecutionResult
        messages = [
            {"role": "system", "content": EXEC_SYSTEM},
            {"role": "user", "content": plan.model_dump_json()},
        ]
        log.debug("agent.execute.request", steps=len(plan.steps))
        return client.generate_structured(messages)

    def run_tool(self, step: PlanStep) -> dict[str, Any]:
        """Low-level tool dispatcher."""
        if step.tool == "file_system":
            return getattr(self.fs, step.command)(*step.args)
        if step.tool == "git":
            return getattr(self.git, step.command)(*step.args)
        if step.tool == "mcp":
            return self.mcp.invoke("shadcn", step.command, {"args": step.args})
        raise ValueError(f"Unknown tool: {step.tool}")

    def refine_plan(self, task: str, current_plan: Plan, feedback: str) -> Plan:
        """Refine the current plan based on user feedback."""
        client = self.router.for_phase("plan")
        client.response_model = Plan
        messages = [
            {"role": "system", "content": PLAN_SYSTEM},
            {"role": "user", "content": task},
            {"role": "assistant", "content": current_plan.model_dump_json()},
            {"role": "user", "content": f"Please revise the plan: {feedback}"},
        ]
        log.debug("agent.refine_plan.request", task=task, feedback=feedback)
        return client.generate_structured(messages)

    def run_task(self, task: str, mode: str = "plan_act") -> ExecutionResult:
        """Plan → execute with safety + reflection loop."""
        for attempt in range(3):
            plan = self.plan(task)

            # ---------- safety audit ----------
            plan_json = plan.model_dump_json()
            safe, reasons = self.safety.audit(plan_json)
            if not safe:
                log.warning("plan.blocked", reasons=reasons)
                error_msg = f"🚫 Safety violation blocked execution:\n{chr(10).join(f'• {reason}' for reason in reasons)}"
                return ExecutionResult(success=False, stderr=error_msg)

            # ---------- execute ----------
            result = self.execute(plan)

            # ---------- reflection ----------
            ok, retry, notes = self.reflection.critique(task, plan_json, result)
            log.info("reflection.complete", ok=ok, retry=retry, notes=notes)
            if ok or not retry:
                # Format successful result for conversational output
                if result.success:
                    formatted_output = self._format_success_output(task, plan, result)
                    return ExecutionResult(success=True, stdout=formatted_output, stderr=result.stderr)
                else:
                    # Format error result
                    formatted_error = self._format_error_output(task, result)
                    return ExecutionResult(success=False, stdout=result.stdout, stderr=formatted_error)

            log.info("reflection.retry", attempt=attempt + 1)

        # All attempts failed
        error_msg = f"❌ Task failed after {attempt + 1} attempts. The agent was unable to complete '{task}' successfully."
        return ExecutionResult(success=False, stderr=error_msg)

    def _format_success_output(self, task: str, plan: Plan, result: ExecutionResult) -> str:
        """Format successful execution results for conversational display."""
        output_lines = []

        # Task summary
        output_lines.append(f"**Task:** {task}")
        output_lines.append("")

        # Plan summary
        step_count = len(plan.steps)
        output_lines.append(f"**Execution Plan:** {step_count} step{'s' if step_count != 1 else ''}")
        for i, step in enumerate(plan.steps, 1):
            output_lines.append(f"  {i}. {step.tool}.{step.command}({', '.join(repr(arg) for arg in step.args)})")
        output_lines.append("")

        # Results
        if result.stdout and result.stdout.strip():
            output_lines.append("**Output:**")
            # Format code blocks if present
            stdout = result.stdout.strip()
            if '```' in stdout or 'def ' in stdout or 'class ' in stdout:
                output_lines.append(f"```\n{stdout}\n```")
            else:
                output_lines.append(stdout)
        else:
            output_lines.append("*Task completed with no output*")

        return "\n".join(output_lines)

    def _format_error_output(self, task: str, result: ExecutionResult) -> str:
        """Format error results for conversational display."""
        output_lines = []

        output_lines.append(f"**Task Failed:** {task}")
        output_lines.append("")

        if result.stderr and result.stderr.strip():
            error_text = result.stderr.strip()
            # Clean up error formatting
            if "Safety block:" in error_text:
                output_lines.append("**Safety Violation:**")
                output_lines.append(error_text.replace("Safety block: ", ""))
            else:
                output_lines.append("**Error Details:**")
                output_lines.append(error_text)
        else:
            output_lines.append("*No error details available*")

        output_lines.append("")
        output_lines.append("*The autonomous agent encountered an issue. Try rephrasing your request or breaking it into smaller steps.*")

        return "\n".join(output_lines)
