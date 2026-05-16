"""Tool to list all running background subagents."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from nanobot.agent.tools.base import Tool

if TYPE_CHECKING:
    from nanobot.agent.subagent import SubagentManager


class ListSubagentsTool(Tool):
    """Tool to query the status of all running background subagents."""

    def __init__(self, manager: "SubagentManager") -> None:
        self._manager = manager

    name = "list_subagents"

    @property
    def description(self) -> str:
        return (
            "**用途**: 列出所有正在运行的后台子任务及其状态。\n\n"
            "**使用时机**:\n"
            "- 想知道当前有多少子任务在跑\n"
            "- 忘记某个子任务的 task_id\n"
            "- 批量检查子任务进度\n\n"
            "**参数**: 无\n\n"
            "**返回**: 每个子任务的 ID、名称、阶段、迭代次数\n\n"
            "**极简案例**: list_subagents()\n"
            "→ 返回所有运行中的子任务列表"
        )

    async def execute(self, **kwargs: Any) -> str:
        statuses = self._manager.list_statuses()
        if not statuses:
            return "No subagents currently running."

        lines = [f"Running subagents ({len(statuses)}):"]
        for s in statuses:
            lines.append(f"  [{s.task_id}] {s.label} — phase: {s.phase}, iter: {s.iteration}")
        return "\n".join(lines)
