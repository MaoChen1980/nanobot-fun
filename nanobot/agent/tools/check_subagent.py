"""Tool to check the status of a running subagent."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from nanobot.agent.tools.base import Tool, tool_parameters
from nanobot.agent.tools.schema import p, tool_parameters_schema

if TYPE_CHECKING:
    from nanobot.agent.subagent import SubagentManager


@tool_parameters(
    tool_parameters_schema(
        task_id=p("string", "The subagent task ID to check (from spawn return value)"),
        required=["task_id"],
    )
)
class CheckSubagentTool(Tool):
    """Tool to query the execution status of a background subagent."""

    def __init__(self, manager: "SubagentManager") -> None:
        self._manager = manager

    name = "check_subagent"

    @property
    def description(self) -> str:
        return (
            "**用途**: 查询后台子任务（spawn 启动的）的执行进度和结果。\n\n"
            "**使用时机**:\n"
            "- spawn 启动子任务后，主动查询完成情况\n"
            "- 想确认子任务进度而不等通知\n\n"
            "**参数**:\n"
            "- task_id: 子任务 ID（spawn 返回信息中会包含）\n\n"
            "**返回**: 当前阶段、迭代次数、已执行工具、完成结果或错误信息\n\n"
            "**极简案例**: check_subagent(task_id='abc12345')\n"
            "→ 返回子任务的当前状态"
        )

    async def execute(self, task_id: str, **kwargs: Any) -> str:
        status = self._manager.get_status(task_id)
        if status is None:
            return f"Subagent '{task_id}' not found (already completed or never existed)."

        lines = [f"Subagent [{status.label}] status:"]
        lines.append(f"  Phase: {status.phase}")
        lines.append(f"  Iteration: {status.iteration}")
        if status.tools_ran:
            lines.append(f"  Tools executed: {', '.join(status.tools_ran)}")
        if status.usage:
            usage = status.usage
            prompt = usage.get("prompt_tokens", 0)
            completion = usage.get("completion_tokens", 0)
            lines.append(f"  Token usage: {prompt} prompt / {completion} completion")
        if status.error:
            lines.append(f"  Error: {status.error}")
        if status.stop_reason:
            lines.append(f"  Stop reason: {status.stop_reason}")
        return "\n".join(lines)
