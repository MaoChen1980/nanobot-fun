"""Context optimizer — two-stage context optimization for AgentLoop.

The optimizer runs an LLM call before the main agent loop to evaluate
and improve context quality. The LLM is instructed to analyze the
conversation context, optionally use read-only tools to gather
additional information, and produce an optimized system prompt.

Only the LLM's final output (the new system prompt) is carried forward
to the main loop — intermediate tool calls and results are discarded.
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from nanobot.agent.tools.registry import ToolRegistry
from nanobot.providers.base import LLMProvider
from nanobot.utils.helpers import build_assistant_message


_OPTIMIZER_PROMPT = """\
You are a context optimization assistant.

Your task is to analyze the conversation context below and produce an \
optimized version of the system prompt for the main assistant.

The conversation includes:
1. The previous system prompt (has been replaced by this instruction)
2. Conversation history
3. The user's latest message

You can:
- Call read-only tools (memory_search, read_file, etc.) to gather \
additional context
- Assess which information is relevant and what might be missing

After your analysis, output a new system prompt for the main assistant. \
This new prompt should include ALL relevant context the main assistant \
needs to respond effectively. You may restructure, summarize, or add \
information as needed.

If you called tools above, incorporate the results into your output.

Do NOT answer the user's question. Only output the optimized context.
"""


class ContextOptimizer:
    """Optimize context before the main agent loop via a dedicated LLM call.

    Enabled by default, returning original messages unchanged, when
    *enabled* is ``False`` (the default).
    """

    def __init__(
        self,
        provider: LLMProvider,
        tool_registry: ToolRegistry,
        model: str | None = None,
        enabled: bool = False,
        max_tool_calls: int = 5,
    ) -> None:
        self._provider = provider
        self._tool_registry = tool_registry
        self._model = model
        self._enabled = enabled
        self._max_tool_calls = max_tool_calls

    @property
    def enabled(self) -> bool:
        return self._enabled

    async def optimize(self, messages: list[dict]) -> list[dict]:
        """Return optimized messages, or unchanged when disabled.

        The first message (system prompt) is replaced with the LLM's
        optimized output when the optimizer runs. Intermediate tool
        results are discarded.
        """
        if not self._enabled:
            return messages

        logger.info("ContextOptimizer: starting optimization")

        # Build optimizer messages — replace system with optimizer prompt
        opt_messages: list[dict[str, Any]] = [
            {"role": "system", "content": _OPTIMIZER_PROMPT},
            *messages[1:],
        ]

        # First LLM call with read-only tools available
        response = await self._provider.chat_with_retry(
            messages=opt_messages,
            tools=self._read_only_tool_schemas(),
            model=self._model,
            max_tokens=4096,
        )

        # If tool calls, execute and let LLM synthesize
        if response.should_execute_tools:
            logger.info(
                "ContextOptimizer: executing {} tool call(s)",
                len(response.tool_calls),
            )
            opt_messages = await self._execute_tools(
                opt_messages, response.tool_calls[: self._max_tool_calls]
            )
            response = await self._provider.chat_with_retry(
                messages=opt_messages,
                model=self._model,
                max_tokens=4096,
            )

        # Replace system prompt with LLM's optimized output
        if response.content and response.content.strip():
            result = list(messages)
            result[0] = dict(messages[0])
            result[0]["content"] = response.content.strip()
            logger.info("ContextOptimizer: optimization complete")
            return result

        logger.info("ContextOptimizer: no output, returning original")
        return messages

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _read_only_tool_schemas(self) -> list[dict] | None:
        """Return tool schemas for read-only tools only."""
        ro_names: set[str] = set()
        for name, tool in self._tool_registry._tools.items():
            if tool.read_only:
                ro_names.add(name)
        if not ro_names:
            return None
        return [
            s
            for s in self._tool_registry.get_definitions()
            if s["function"]["name"] in ro_names
        ]

    async def _execute_tools(
        self,
        messages: list[dict[str, Any]],
        tool_calls: list,
    ) -> list[dict[str, Any]]:
        """Execute tool calls and append results to messages."""
        result = list(messages)
        result.append(build_assistant_message(None))

        for tc in tool_calls:
            try:
                raw = await self._tool_registry.execute(tc.name, tc.arguments)
                content = str(raw) if raw is not None else ""
            except Exception as exc:
                content = f"Error: {exc}"

            result.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": content,
                "name": tc.name,
            })

        return result
