from __future__ import annotations

import subprocess
from pathlib import Path
import structlog
from typing import Any, Dict

log = structlog.get_logger(__name__)


class GitTool:
    def __init__(self, root: str | Path = "."):
        self.root = Path(root).resolve()

    def _run(self, args: list[str]) -> Dict[str, Any]:
        log.debug("git cmd", args=args, cwd=str(self.root))
        try:
            res = subprocess.run(
                ["git"] + args,
                cwd=self.root,
                capture_output=True,
                text=True,
                check=True,
            )
            return {"success": True, "stdout": res.stdout.strip()}
        except subprocess.CalledProcessError as exc:
            log.warning("git failed", args=args, returncode=exc.returncode, stderr=exc.stderr)
            return {"success": False, "stderr": exc.stderr.strip()}

    def status(self) -> Dict[str, Any]:
        return self._run(["status", "--short"])

    def add(self, path: str) -> Dict[str, Any]:
        return self._run(["add", path])

    def commit(self, message: str) -> Dict[str, Any]:
        return self._run(["commit", "-m", message])
