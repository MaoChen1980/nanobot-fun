"""DeleteFileTool — safely delete a single file."""

from __future__ import annotations

from typing import Any

from nanobot.agent.tools.base import PathExists, PathType, FileDeleted, tool_parameters
from nanobot.agent.tools.filesystem.filesystem_base import _FsTool
from nanobot.agent.tools.schema import p


@tool_parameters(properties={
    "path": p("string", "The file path to delete"),
}, required=["path"])
class DeleteFileTool(_FsTool):
    """Delete a single file. Supports workspace-relative and absolute paths."""

    name = "delete_file"
    description = (
        "Delete a file. Safer than exec rm — workspace-guarded and single-file only.\n"
        "Framework auto-verifies: path exists, path is a file (not directory).\n"
        "Auto-confirms deletion after execution."
    )

    _pre_validators = [PathExists("path"), PathType("path", "file")]
    _post_validators = [FileDeleted("path")]

    async def execute(self, path: str = "", **kwargs: Any) -> str:
        resolved = self._resolve(path)
        resolved.unlink()
        return f"Deleted: {resolved}"
