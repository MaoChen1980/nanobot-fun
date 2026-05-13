"""Tests for ContextOptimizer — two-stage context optimization."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from nanobot.agent.context_optimizer import ContextOptimizer
from nanobot.providers.base import LLMResponse, ToolCallRequest


def _mock_tool_registry():
    """Tool registry with one read-only tool and one write tool."""
    reg = MagicMock()
    read_tool = MagicMock()
    read_tool.read_only = True
    write_tool = MagicMock()
    write_tool.read_only = False
    reg._tools = {"memory_search": read_tool, "exec": write_tool}
    reg.get_definitions.return_value = [
        {"type": "function", "function": {"name": "memory_search", "description": "search"}},
        {"type": "function", "function": {"name": "exec", "description": "run"}},
    ]
    return reg


def _messages():
    return [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there"},
        {"role": "user", "content": "What is in this file?"},
    ]


class TestContextOptimizerDisabled:
    """When enabled=False, optimize() is a no-op."""

    @pytest.mark.asyncio
    async def test_returns_original_messages(self):
        optimizer = ContextOptimizer(
            provider=MagicMock(),
            tool_registry=_mock_tool_registry(),
            enabled=False,
        )
        msgs = _messages()
        result = await optimizer.optimize(msgs)
        assert result is msgs  # same list object, no copy


class TestContextOptimizerEnabled:
    """When enabled=True, optimize() calls the provider."""

    @pytest.mark.asyncio
    async def test_replaces_system_prompt_with_llm_output(self):
        provider = MagicMock()
        provider.chat_with_retry = AsyncMock(return_value=LLMResponse(
            content="Optimized system prompt with relevant context.",
        ))

        optimizer = ContextOptimizer(
            provider=provider,
            tool_registry=_mock_tool_registry(),
            enabled=True,
        )
        msgs = _messages()
        result = await optimizer.optimize(msgs)

        # System prompt replaced
        assert result[0]["content"] == "Optimized system prompt with relevant context."
        # History and user message preserved
        assert result[1:] == msgs[1:]
        # Original unchanged
        assert msgs[0]["content"] == "You are a helpful assistant."

    @pytest.mark.asyncio
    async def test_executes_tools_and_synthesizes(self):
        """When LLM calls tools, execute them then call again for final output."""
        provider = MagicMock()
        calls = iter([
            # First call: returns tool calls
            LLMResponse(
                content="Let me search memory first.",
                tool_calls=[ToolCallRequest(id="call1", name="memory_search", arguments={"q": "test"})],
                finish_reason="tool_calls",
            ),
            # Second call: synthesizes tool results
            LLMResponse(
                content="Found relevant context: test results. Optimized prompt.",
            ),
        ])
        provider.chat_with_retry = AsyncMock(side_effect=lambda *a, **kw: next(calls))

        reg = _mock_tool_registry()
        reg.execute = AsyncMock(return_value="memory result: found X")

        optimizer = ContextOptimizer(
            provider=provider,
            tool_registry=reg,
            enabled=True,
        )
        msgs = _messages()
        result = await optimizer.optimize(msgs)

        # Final system prompt contains synthesized output
        assert result[0]["content"] == "Found relevant context: test results. Optimized prompt."
        # Tool was called
        reg.execute.assert_called_once_with("memory_search", {"q": "test"})

    @pytest.mark.asyncio
    async def test_empty_llm_output_returns_original(self):
        provider = MagicMock()
        provider.chat_with_retry = AsyncMock(return_value=LLMResponse(
            content="",
        ))

        optimizer = ContextOptimizer(
            provider=provider,
            tool_registry=_mock_tool_registry(),
            enabled=True,
        )
        msgs = _messages()
        result = await optimizer.optimize(msgs)

        # Original messages unchanged
        assert result[0]["content"] == "You are a helpful assistant."
        assert len(result) == len(msgs)

    @pytest.mark.asyncio
    async def test_filters_to_read_only_tools(self):
        """Only read-only tools are passed to the LLM."""
        reg = _mock_tool_registry()

        optimizer = ContextOptimizer(
            provider=MagicMock(),
            tool_registry=reg,
            enabled=True,
        )

        schemas = optimizer._read_only_tool_schemas()
        assert schemas is not None
        names = [s["function"]["name"] for s in schemas]
        assert "memory_search" in names
        assert "exec" not in names  # write tools excluded
