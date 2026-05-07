"""MoveFileTool — safely move/rename a file."""

from __future__ import annotations

from typing import Any

from nanobot.agent.tools.base import tool_parameters
from nanobot.agent.tools.filesystem.filesystem_base import _FsTool
from nanobot.agent.tools.schema import p


@tool_parameters(properties={
    "source": p("string", "The source file path"),
    "dest": p("string", "The destination file path"),
}, required=["source", "dest"])
class MoveFileTool(_FsTool):
    """Move or rename a file. Workspace-guarded, single-file only."""

    name = "move_file"
    description = "Move or rename a file. Safer than exec mv — workspace-guarded and single-file only."

    async def execute(self, source: str | None = None, dest: str | None = None, **kwargs: Any) -> str:
        if not source or not dest:
            return "Error: source and dest are required"
        try:
            src_resolved = self._resolve(source)
            dst_resolved = self._resolve(dest)
        except ValueError as e:
            return f"Error: {e}"

        if not src_resolved.exists():
            return f"Error: source does not exist: {src_resolved}"
        if src_resolved.is_dir():
            return f"Error: source is a directory (use exec mv for directories): {src_resolved}"

        if dst_resolved.exists():
            return f"Error: destination already exists: {dst_resolved}"

        dst_resolved.parent.mkdir(parents=True, exist_ok=True)
        src_resolved.rename(dst_resolved)
        return f"Moved: {src_resolved} -> {dst_resolved}"
