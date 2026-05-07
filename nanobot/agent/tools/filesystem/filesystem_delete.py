"""DeleteFileTool — safely delete a single file."""

from __future__ import annotations

from typing import Any

from nanobot.agent.tools.base import tool_parameters
from nanobot.agent.tools.filesystem.filesystem_base import _FsTool
from nanobot.agent.tools.schema import p


@tool_parameters(properties={
    "path": p("string", "The file path to delete"),
}, required=["path"])
class DeleteFileTool(_FsTool):
    """Delete a single file. Supports workspace-relative and absolute paths."""

    name = "delete_file"
    description = "Delete a file. Safer than exec rm — workspace-guarded and single-file only."

    async def execute(self, path: str | None = None, **kwargs: Any) -> str:
        if not path:
            return "Error: path is required"
        try:
            resolved = self._resolve(path)
        except ValueError as e:
            return f"Error: {e}"

        if not resolved.exists():
            return f"Error: path does not exist: {resolved}"
        if resolved.is_dir():
            return f"Error: path is a directory (use exec rm -r for directories): {resolved}"

        resolved.unlink()
        return f"Deleted: {resolved}"
