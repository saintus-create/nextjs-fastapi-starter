"""Configuration loader for cline-agent."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

import yaml
from dotenv import load_dotenv

load_dotenv(".env.local")
load_dotenv(".env")


def load_config(config_path: str | Path | None = None) -> Dict[str, Any]:
    """Load configuration from YAML file and environment variables.
    
    Priority: Environment variables > config file > defaults
    """
    defaults = {
        "project_root": os.getcwd(),
        "mcp_server_url": os.getenv("MCP_SERVER_URL", "http://localhost:8000"),
        "logging": {
            "level": os.getenv("LOG_LEVEL", "INFO"),
            "renderer": os.getenv("LOG_RENDERER", "console"),
        },
        "llm": {
            "default_provider": os.getenv("LLM_PROVIDER", "openai"),
            "openai": {
                "api_key": os.getenv("OPENAI_API_KEY", ""),
                "model": os.getenv("OPENAI_MODEL", "gpt-4o"),
            },
            "anthropic": {
                "api_key": os.getenv("ANTHROPIC_API_KEY", ""),
                "model": os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
            },
            "groq": {
                "api_key": os.getenv("GROQ_API_KEY", ""),
                "model": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            },
            "sambanova": {
                "api_key": os.getenv("SAMBANOVA_API_KEY", ""),
                "model": os.getenv("SAMBANOVA_MODEL", "Meta-Llama-3.1-405B-Instruct"),
            },
            # Phase-specific model overrides
            "phases": {
                "plan": os.getenv("LLM_PLAN_MODEL", "openai"),
                "execute": os.getenv("LLM_EXECUTE_MODEL", "openai"),
                "fallback": os.getenv("LLM_FALLBACK_MODEL", "groq"),
            },
        },
    }

    # Load from config file if exists
    if config_path:
        config_file = Path(config_path)
    else:
        config_file = Path("cline-agent.yaml")

    if config_file.exists():
        with open(config_file, "r") as f:
            file_config = yaml.safe_load(f) or {}
        # Deep merge file config into defaults
        defaults = _deep_merge(defaults, file_config)

    return defaults


def _deep_merge(base: Dict, override: Dict) -> Dict:
    """Deep merge override into base dict."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result
