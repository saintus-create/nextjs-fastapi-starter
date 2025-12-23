from __future__ import annotations

from pathlib import Path
import structlog
import aiofiles
import asyncio
from typing import Any, Dict

log = structlog.get_logger(__name__)


class FileSystemTool:
    def __init__(self, root: str | Path = "."):
        self.root = Path(root).resolve()

    def _resolve(self, path: str) -> Path:
        p = (self.root / path).resolve()
        if not str(p).startswith(str(self.root)):
            raise PermissionError("Sandbox escape detected")
        return p

    # ---------- synchronous wrappers ----------
    def write(self, path: str, content: str) -> Dict[str, Any]:
        target = self._resolve(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        log.info("file written", path=str(target), bytes=len(content))
        return {"success": True, "stdout": f"Wrote {len(content)} bytes to {path}"}

    def read(self, path: str) -> Dict[str, Any]:
        target = self._resolve(path)
        content = target.read_text(encoding="utf-8")
        log.info("file read", path=str(target), bytes=len(content))
        return {"success": True, "stdout": content}

    def list_dir(self, path: str = ".") -> Dict[str, Any]:
        target = self._resolve(path)
        if not target.is_dir():
            return {"success": False, "stderr": f"{path} is not a directory"}
        entries = sorted(p.name for p in target.iterdir())
        log.info("directory listed", path=str(target), entries=len(entries))
        return {"success": True, "stdout": "\n".join(entries)}
