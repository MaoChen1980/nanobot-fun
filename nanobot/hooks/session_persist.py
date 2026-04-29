"""Session persistence hook — writes SESSION.md at end of every turn."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from nanobot.agent.hook import AgentHook, AgentHookContext

_UTC8 = timezone(timedelta(hours=8))


class SessionPersistHook(AgentHook):
    """Write SESSION.md at the end of each completed turn for cross-session recovery.

    Writes only on final iteration (when stop_reason is set).  Captures the
    last user message, tools called, stop reason, error state, and a brief
    progress indicator so the next session can resume context quickly.

    Workspace is auto-discovered by walking up from CWD looking for AGENTS.md.
    """

    @staticmethod
    def _now() -> str:
        return datetime.now(tz=_UTC8).strftime("%Y-%m-%d %H:%M")

    @staticmethod
    def _find_workspace() -> Path | None:
        p = Path.cwd()
        for _ in range(6):
            if (p / "AGENTS.md").exists():
                return p
            parent = p.parent
            if parent == p:
                break
            p = parent
        return None

    # ── lifecycle ──────────────────────────────────────────────────

    async def after_iteration(self, ctx: AgentHookContext) -> None:
        workspace = self._find_workspace()
        if not workspace:
            return

        # Only write on the final iteration of a turn
        if not ctx.stop_reason:
            return

        # Extract last user message (skip system, search from end)
        last_user = ""
        for msg in reversed(ctx.messages):
            if msg.get("role") == "user":
                raw = str(msg.get("content", ""))
                # Strip Runtime Context wrapper if present
                if "[/Runtime Context]" in raw:
                    idx = raw.rfind("[/Runtime Context]")
                    raw = raw[idx + len("[/Runtime Context]"):].strip()
                last_user = raw[:200]
                break

        # Extract tool names from assistant messages with tool_calls
        tools_set: set[str] = set()
        for msg in ctx.messages:
            if msg.get("role") == "assistant":
                tcs = msg.get("tool_calls") or []
                for tc in tcs:
                    name = tc.get("function", {}).get("name", tc.get("name", ""))
                    if name:
                        tools_set.add(name)
        tools = ", ".join(sorted(tools_set)) if tools_set else "none"

        stop = ctx.stop_reason or "unknown"
        error_summary = ctx.error or "None"

        # Derive progress from final content (first meaningful line)
        progress = ""
        if ctx.final_content:
            lines = ctx.final_content.strip().split("\n")
            for line in lines:
                stripped = line.strip()
                if stripped and not stripped.startswith("[") and not stripped.startswith(">"):
                    progress = stripped[:150]
                    break

        summary = (
            f"# Session State — {self._now()}\n"
            f"> Last: {last_user}\n"
            f"> Tools: {tools}. Stop: {stop}. Error: {error_summary}\n"
            f"> Progress: {progress or '?'}\n"
        )

        out = workspace / "SESSION.md"
        out.write_text(summary, encoding="utf-8")
