from __future__ import annotations

import sys
import typer
from typing import Literal

from .config import load_config
from .logging_config import setup_logging
from .agent.core import Agent

app = typer.Typer(pretty_exceptions_show_locals=False)

Mode = Literal["plan_act", "autonomous", "interactive"]


# ------------- interactive REPL -------------
def interactive_loop(agent: Agent, task: str) -> None:
    plan = agent.plan(task)
    while True:
        typer.secho("\n--- CURRENT PLAN ---", fg=typer.colors.CYAN, bold=True)
        typer.echo(plan.model_dump_json(indent=2))
        typer.echo("--------------------\n")
        choice = typer.prompt(
            "Actions: [a]pprove [e]dit [q]uit",
            default="a",
        ).lower()
        if choice == "a":
            typer.secho("\n🚀 Executing...", fg=typer.colors.GREEN)
            result = agent.run_task(task, mode="autonomous")
            typer.echo(result.model_dump_json(indent=2))
            return
        elif choice == "e":
            feedback = typer.prompt("What should be changed?")
            typer.echo("🔄 Refining plan...")
            plan = agent.refine_plan(task, plan, feedback)
        elif choice == "q":
            typer.echo("Operation cancelled.")
            sys.exit(0)
        else:
            typer.echo("Invalid choice.")


# ------------- top-level options -------------
@app.callback()
def _main(
    log_level: str = typer.Option("INFO", "--log-level", "-l"),
    json: bool = typer.Option(False, "--json"),
):
    setup_logging(level=log_level.upper(), renderer="json" if json else "console")


# ------------- commands -------------
@app.command()
def config():
    """Print resolved configuration (secrets masked)."""
    cfg = load_config()

    def _mask(obj, keys=("sambanova", "groq", "openai", "anthropic")):
        if isinstance(obj, dict):
            return {
                k: "***" if k in keys and v else _mask(v, keys)
                for k, v in obj.items()
            }
        if isinstance(obj, list):
            return [_mask(i, keys) for i in obj]
        return obj

    typer.secho("Effective configuration:", fg=typer.colors.GREEN)
    typer.echo(_mask(cfg))


@app.command()
def task(
    description: str = typer.Argument(..., help="Natural-language task"),
    mode: Mode = typer.Option("plan_act", "--mode", "-m", help="Execution mode"),
):
    """Plan and execute a task."""
    agent = Agent()
    if mode == "interactive":
        interactive_loop(agent, description)
    elif mode == "autonomous":
        result = agent.run_task(description, mode="autonomous")
        typer.echo("\n=== RESULT ===\n")
        typer.echo(result.model_dump_json(indent=2))
    elif mode == "plan_act":
        typer.secho("\n[PLAN]", fg=typer.colors.CYAN, bold=True)
        result = agent.run_task(description, mode="plan_act")
        typer.echo(result.model_dump_json(indent=2))
    else:
        raise ValueError(f"Unknown mode: {mode!r}")


if __name__ == "__main__":
    app()
