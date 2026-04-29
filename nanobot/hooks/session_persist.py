"""Session persistence hook — writes SESSION.md at end of every turn."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from nanobot.agent.hook import AgentHook, AgentHookContext

_UTC8 = timezone(timedelta(hours=8))


class SessionPersistHook(AgentHook):
    """Write SESSION.md at the end of each completed turn for cross-session recovery.

    Writes only on final iteration (when stop_reason is set).  The first 3 lines
    are auto-injected into the next session's system prompt by context.py, so we
    pack them with state: current goal, last action, and any blockers.

    Workspace is auto-discovered by walking up from CWD looking for AGENTS.md.
    """

    @staticmethod
    def _now() -> str:
        return datetime.now(tz=_UTC8).strftime("%Y-%m-%d %H:%M")

    @staticmethod
    def _resolve_workspace(ctx: AgentHookContext) -> Path | None:
        """Use ctx.workspace (injected by framework), fallback to CWD-based discovery."""
        if ctx.workspace:
            return ctx.workspace
        p = Path.cwd()
        for _ in range(6):
            if (p / "AGENTS.md").exists():
                return p
            parent = p.parent
            if parent == p:
                break
            p = parent
        home_ws = Path.home() / ".nanobot" / "workspace"
        if (home_ws / "AGENTS.md").exists():
            return home_ws
        return None

    # ── lifecycle ──────────────────────────────────────────────────

    async def after_iteration(self, ctx: AgentHookContext) -> None:
        workspace = self._resolve_workspace(ctx)
        if not workspace:
            return

        # Only write on the final iteration of a turn
        if not ctx.stop_reason:
            return

        # ── extract goal ──────────────────────────────────────────
        goal = ""
        goals_file = workspace / "memory" / "goals.md"
        if goals_file.exists():
            for line in goals_file.read_text(encoding="utf-8").split("\n"):
                s = line.strip()
                # Active goals are listed under "## 活跃目标" with "### Gx:" prefix
                if s.startswith("### G") and "→" in s:
                    goal = s.split("### ", 1)[-1] if "### " in s else s
                    break
        if not goal:
            # Fallback: top-line goal
            goal = "?"

        # ── extract last action ────────────────────────────────────
        # Derive from the final assistant content before stop
        last_action = ""
        if ctx.final_content:
            lines = ctx.final_content.strip().split("\n")
            for line in lines:
                s = line.strip()
                # Skip markup, metadata, and empty lines
                if not s or s.startswith("[") or s.startswith(">") or s.startswith("```") or s.startswith("---"):
                    continue
                # Take the first meaningful line as the action summary
                last_action = s[:200]
                break

        if not last_action:
            # Fallback: use tool names
            tools_set: set[str] = set()
            for msg in ctx.messages:
                if msg.get("role") == "assistant":
                    tcs = msg.get("tool_calls") or []
                    for tc in tcs:
                        name = tc.get("function", {}).get("name", tc.get("name", ""))
                        if name:
                            tools_set.add(name)
            tools = ", ".join(sorted(tools_set)) if tools_set else "none"
            last_action = f"tools: {tools}"

        # ── detect blockers ────────────────────────────────────────
        blocker = ""
        if ctx.stop_reason == "ask_user":
            blocker = "(waiting for user response)"
        elif ctx.error and ctx.error != "None":
            blocker = f"(error: {ctx.error[:80]})"

        status = blocker if blocker else "ok"

        # ── write SESSION.md ────────────────────────────────────────
        # First 3 lines → injected into system prompt.  Pack them with state.
        summary = (
            f"# Goal: {goal}\n"
            f"> Last: {last_action}\n"
            f"> Status: {status}\n"
        )
        out = workspace / "SESSION.md"
        out.write_text(summary, encoding="utf-8")

        # Append a narrative progress entry to process-log.md
        self._append_process_log(workspace, self._now(), ctx)

    # ── process log ─────────────────────────────────────────────────

    @staticmethod
    def _append_process_log(
        workspace: Path,
        now: str,
        ctx: AgentHookContext,
    ) -> None:
        """Append a brief narrative entry to memory/process-log.md.

        Uses the first meaningful line of final_content as the progress
        summary — not machine metrics.  If no content, skips.
        """
        log_file = workspace / "memory" / "process-log.md"
        log_file.parent.mkdir(parents=True, exist_ok=True)

        # Extract the first meaningful line of the assistant's response
        progress = ""
        if ctx.final_content:
            for line in ctx.final_content.strip().split("\n"):
                s = line.strip()
                # Skip markup, code blocks, empty lines
                if not s or s.startswith("```") or s.startswith("---"):
                    continue
                if s.startswith("[") or s.startswith(">"):
                    continue
                progress = s[:150]
                break

        if not progress:
            return  # nothing meaningful to record

        entry = f"### [{now}] {progress}"
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"\n{entry}\n")
        except Exception:
            pass  # non-critical
