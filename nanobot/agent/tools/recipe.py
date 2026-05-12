"""Recipe tool — multi-step operations composed from other tools in one call."""

from __future__ import annotations

from typing import Any, Callable, Coroutine

from nanobot.agent.tools.base import Tool, tool_parameters
from nanobot.agent.tools.schema import p, tool_parameters_schema


@tool_parameters(
    tool_parameters_schema(
        recipe=p("string", "Recipe name: find_and_read, explore_source"),
        pattern=p("string", "Search pattern (for find_and_read)"),
        path=p("string", "File or directory path"),
        max_files=p("integer", "Max files to read (for find_and_read)", minimum=1, maximum=50),
    ),
    required=["recipe"],
)
class RecipeTool(Tool):
    """Execute multi-step operations by composing other tools — one call instead of many.

    Built-in recipes:
      - find_and_read: grep for pattern → read matching files
      - explore_source: explore module → read key parts
    """

    name = "run_recipe"
    read_only = True

    description = (
        "Run a multi-step recipe — the framework chains tool calls for you in one call.\n\n"
        "Built-in recipes:\n"
        "  - find_and_read:  `pattern` + optional `path` + optional `max_files`\n"
        "                    Grep the codebase, then read matching files.\n"
        "  - explore_source: `path`\n"
        "                    Explore module structure, then read definitions.\n\n"
        "Use this when:\n"
        "- You need to search for code then immediately read the results\n"
        "- The task has a well-known multi-step pattern (search→read, explore→drill)\n\n"
        "Do NOT use when:\n"
        "- You only need one step (use grep, read_files, or explore_module directly)\n"
        "- You need tight control over each step's parameters\n\n"
        "Limits: max_files capped at 50."
    )

    def __init__(self, run_tool: Callable[[str, dict[str, Any]], Coroutine[Any, Any, Any]] | None = None):
        self._run_tool = run_tool

    async def execute(self, recipe: str = "", **kwargs: Any) -> str:
        handler_name = f"_recipe_{recipe.replace('-', '_')}"
        handler = getattr(self, handler_name, None)
        if not handler:
            available = [n.replace("_recipe_", "") for n in dir(self) if n.startswith("_recipe_")]
            return f"Error: Unknown recipe '{recipe}'. Available: {', '.join(sorted(available))}"
        return await handler(**kwargs)

    async def _call(self, tool: str, params: dict[str, Any]) -> str:
        if self._run_tool is None:
            return f"[Recipe would call {tool} with {params}]"
        result = await self._run_tool(tool, params)
        return str(result)

    # -- recipes ----------------------------------------------------------------

    async def _recipe_find_and_read(self, pattern: str = "", path: str = ".", max_files: int = 10, **kwargs: Any) -> str:
        grep_result = await self._call("grep", {
            "pattern": pattern, "path": path, "output_mode": "files_with_matches",
        })
        grep_str = str(grep_result)
        if grep_str.startswith("Error") or "No matches" in grep_str:
            return f"# find_and_read: pattern={pattern!r}\n\nNo files matched in {path}"

        read_result = await self._call("read_files", {
            "glob": "**/*", "grep": pattern, "path": path, "max_files": max_files,
        })
        return f"# find_and_read: pattern={pattern!r}\n\n{read_result}"

    async def _recipe_explore_source(self, path: str = "", **kwargs: Any) -> str:
        explore = await self._call("explore_module", {"path": path, "show_refs": True})
        explore_str = str(explore)
        if explore_str.startswith("Error"):
            return explore_str

        return f"# explore_source: {path}\n\n{explore_str}"
