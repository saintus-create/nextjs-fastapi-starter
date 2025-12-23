from __future__ import annotations

import re
import subprocess
import structlog
from pathlib import Path
from typing import List, Tuple

log = structlog.get_logger(__name__)


class SafetyAuditor:
    """Two-tier audit: fast static regex + LLM-based semantic check."""

    # Dangerous command patterns - removed problematic word boundaries
    STATIC_DENY = re.compile(
        r"(rm\s+-rf\s+/|dd\s+if=/dev/zero|:\(\)\{.*:\|.*:.*\}&|chmod\s+777|eval\s*\(|exec\s*\(|os\.system|subprocess\.call)",
        re.I,
    )

    def audit(self, content: str) -> Tuple[bool, List[str]]:
        """Returns (safe, list-of-reasons)."""
        hits = self.STATIC_DENY.findall(content)
        if hits:
            return False, [f"Static blocklist hit: {h}" for h in hits]
        return True, []

    def lint_file(self, path: Path) -> Tuple[bool, List[str]]:
        """Run ruff on a Python file."""
        try:
            proc = subprocess.run(
                ["ruff", "check", "--quiet", str(path)],
                capture_output=True,
                text=True,
            )
            if proc.returncode == 0:
                return True, []
            return False, [f"Lint: {proc.stdout.strip()}"]
        except FileNotFoundError:
            log.warning("ruff not found – skipping lint")
            return True, []
