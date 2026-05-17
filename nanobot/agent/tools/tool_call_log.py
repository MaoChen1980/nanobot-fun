"""Tool call log: query tool execution history for debugging and context."""

from __future__ import annotations

from typing import Any

from nanobot.agent.db import NanobotDB
from nanobot.agent.tools.base import Tool, tool_parameters
from nanobot.agent.tools.schema import p, tool_parameters_schema


@tool_parameters(
    tool_parameters_schema(
        session_key=p("string",
            "Filter by session key (session identifier). "
            "To find the current session's key: run list_goals or check the "
            "session info at the top of your context (usually displayed as "
            "'Session: <key>' in the system prompt). "
            "Without a session_key filter, returns calls from all sessions."
        ),
        tool_name=p("string", "Filter by tool name (e.g. 'exec', 'read_file', 'grep')"),
        success=p("boolean", "Filter by success (1=success, 0=failed). Omit to return all."),
        min_result_size=p("integer", "Filter to results larger than N characters"),
        limit=p("integer", "Maximum number of records to return (default 20, max 100)"),
    )
)
class ToolCallLogTool(Tool):
    """Query tool execution log — who ran what, when, with what result."""

    def __init__(self, db: NanobotDB):
        self._db = db

    name = "tool_call_log"

    description = (
            "**用途**: 查询工具调用执行日志，用于调试失败的调用或追踪结果。\n\n"
            "**参数说明**:\n"
            "- session_key: 按会话过滤（当前会话 key 见 system prompt）\n"
            "- tool_name: 按工具名过滤（如 exec、read_file、grep）\n"
            "- success: 1=成功、0=失败、不传=不限\n"
            "- min_result_size: 仅返回结果大于 N 字符的调用\n"
            "- limit: 最多返回条数（默认 20，最大 100）\n\n"
            "**极简案例**: tool_call_log(tool_name='grep', limit=5)\n"
            "→ 返回最近 5 次 grep 调用记录"
        )

    read_only = True

    async def execute(
        self,
        session_key: str | None = None,
        tool_name: str | None = None,
        success: bool | None = None,
        min_result_size: int | None = None,
        limit: int = 20,
    ) -> str:
        limit = min(limit, 100)
        rows = self._db.query_tool_calls(
            session_key=session_key,
            tool_name=tool_name,
            success=success,
            min_result_size=min_result_size,
            limit=limit,
        )
        if not rows:
            return "No tool call records found matching the criteria."

        lines = []
        for r in rows:
            status = "✅" if r["success"] else "❌"
            dur = f" {r['duration_ms']}ms" if r.get("duration_ms") else ""
            error = f" [ERROR: {r.get('error', '')}]" if not r["success"] and r.get("error") else ""
            result_preview = (r["result"] or "")[:120].replace("\n", " ")
            if len(r["result"] or "") > 120:
                result_preview += "..."
            lines.append(
                f"{status}[iter {r['iteration']}/turn {r['turn']}] {r['tool_name']}{dur}{error}"
                f"\n  params: {r['params']}"
                f"\n  result: {result_preview}"
                f"\n  {r['timestamp']}"
            )
        return "\n\n".join(lines)
