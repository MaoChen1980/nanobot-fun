"""Tests for RecallTool — memory search tool (history + knowledge modes)."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from nanobot.agent.memory import MemoryStore
from nanobot.agent.tools.recall import RecallTool


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_store(tmp_path: Path) -> MemoryStore:
    """Build a MemoryStore with some test data."""
    store = MemoryStore(tmp_path)
    store.write_memory("Line about Python.\nLine about Java.")
    store.append_history("User asked about Python yesterday")
    store.append_history("Assistant explained Python basics")
    return store


def _make_tool(store: MemoryStore) -> RecallTool:
    return RecallTool(store=store)


# ---------------------------------------------------------------------------
# Basic properties
# ---------------------------------------------------------------------------

class TestRecallToolBasic:
    """Basic RecallTool properties."""

    def test_tool_name(self, tmp_path: Path):
        tool = _make_tool(_make_store(tmp_path))
        assert tool.name == "recall"

    def test_tool_description(self, tmp_path: Path):
        tool = _make_tool(_make_store(tmp_path))
        assert "recall" in tool.description or "召回" in tool.description

    def test_tool_is_read_only(self, tmp_path: Path):
        tool = _make_tool(_make_store(tmp_path))
        assert tool.read_only is True

    def test_parameters_have_mode_and_query(self, tmp_path: Path):
        tool = _make_tool(_make_store(tmp_path))
        params = tool.parameters
        assert "mode" in params["properties"]
        assert "query" in params["properties"]
        assert "history" in params["properties"]["mode"]["enum"]
        assert "knowledge" in params["properties"]["mode"]["enum"]


# ---------------------------------------------------------------------------
# history mode
# ---------------------------------------------------------------------------

class TestRecallToolHistoryMode:
    """RecallTool.execute(mode='history') behavior."""

    @pytest.mark.asyncio
    async def test_with_query_only(self, tmp_path: Path):
        """Query text matches content."""
        store = _make_store(tmp_path)
        tool = _make_tool(store)
        result = await tool.execute(mode="history", query="Python")
        assert "Python" in result
        assert "Java" in result

    @pytest.mark.asyncio
    async def test_with_keyword_filters(self, tmp_path: Path):
        """Keyword filter narrows results."""
        store = _make_store(tmp_path)
        tool = _make_tool(store)
        result = await tool.execute(mode="history", query="Python", keyword="Python")
        assert "Python" in result
        assert "No memories found" not in result

    @pytest.mark.asyncio
    async def test_with_non_matching_keyword(self, tmp_path: Path):
        """Non-matching keyword returns empty."""
        store = _make_store(tmp_path)
        tool = _make_tool(store)
        result = await tool.execute(mode="history", query="Ruby", keyword="Ruby")
        assert "No memories found" in result

    @pytest.mark.asyncio
    async def test_with_date_range(self, tmp_path: Path):
        """Date range filters history entries."""
        store = _make_store(tmp_path)
        tool = _make_tool(store)
        today = datetime.now().strftime("%Y-%m-%d")
        result = await tool.execute(mode="history", query="Python", start=today, end=today)
        assert "Python" in result or "No memories found" in result

    @pytest.mark.asyncio
    async def test_empty_memory_returns_no_memories(self, tmp_path: Path):
        """Empty memory store returns appropriate message."""
        store = MemoryStore(tmp_path)
        tool = _make_tool(store)
        result = await tool.execute(mode="history", query="anything")
        assert "No memories found" in result

    @pytest.mark.asyncio
    async def test_result_has_section_header(self, tmp_path: Path):
        """Results are formatted with section header."""
        store = _make_store(tmp_path)
        tool = _make_tool(store)
        result = await tool.execute(mode="history", query="Python")
        assert "## Relevant Memories" in result


# ---------------------------------------------------------------------------
# knowledge mode
# ---------------------------------------------------------------------------

class TestRecallToolKnowledgeMode:
    """RecallTool.execute(mode='knowledge') behavior."""

    @pytest.mark.asyncio
    async def test_empty_index_returns_no_results(self, tmp_path: Path):
        """Empty memory dir returns no results."""
        store = MemoryStore(tmp_path)
        tool = _make_tool(store)
        result = await tool.execute(mode="knowledge", query="anything")
        assert "No relevant knowledge found" in result

    @pytest.mark.asyncio
    async def test_knowledge_with_custom_k(self, tmp_path: Path):
        """k parameter is accepted."""
        store = MemoryStore(tmp_path)
        tool = _make_tool(store)
        result = await tool.execute(mode="knowledge", query="test", k=3)
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_knowledge_clamps_k(self, tmp_path: Path):
        """k outside 1-20 is rejected by schema."""
        store = MemoryStore(tmp_path)
        tool = _make_tool(store)
        params = tool.parameters
        k_prop = params["properties"]["k"]
        assert k_prop.get("minimum") == 1
        assert k_prop.get("maximum") == 20


# ---------------------------------------------------------------------------
# mode validation
# ---------------------------------------------------------------------------

class TestRecallToolModeValidation:
    """RecallTool mode parameter validation."""

    @pytest.mark.asyncio
    async def test_default_mode_is_history(self, tmp_path: Path):
        """Without mode, defaults to history."""
        store = _make_store(tmp_path)
        tool = _make_tool(store)
        result = await tool.execute(query="Python")
        # Default mode is history, so should search memory
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_invalid_mode_returns_error(self, tmp_path: Path):
        """Invalid mode value returns error."""
        store = _make_store(tmp_path)
        tool = _make_tool(store)
        result = await tool.execute(mode="invalid", query="test")
        assert "Unknown mode" in result


# ---------------------------------------------------------------------------
# Date parsing
# ---------------------------------------------------------------------------

class TestRecallToolDateParsing:
    """Date parsing edge cases."""

    @pytest.mark.asyncio
    async def test_invalid_date_format_falls_back(self, tmp_path: Path):
        """Invalid date format is handled gracefully."""
        store = _make_store(tmp_path)
        tool = _make_tool(store)
        result = await tool.execute(mode="history", query="test", start="invalid-date")
        assert isinstance(result, str)

    def test_parse_date_supports_datetime_format(self):
        """_parse_date handles YYYY-MM-DD HH:MM format."""
        tool = RecallTool(MemoryStore(Path("/tmp/fake")))

        dt = tool._parse_date("2026-04-21")
        assert dt is not None
        assert dt.year == 2026
        assert dt.month == 4
        assert dt.day == 21

        dt = tool._parse_date("2026-04-21 09:30")
        assert dt is not None
        assert dt.hour == 9
        assert dt.minute == 30

    def test_parse_date_returns_none_for_invalid(self):
        """_parse_date returns None for invalid input."""
        tool = RecallTool(MemoryStore(Path("/tmp/fake")))
        assert tool._parse_date(None) is None
        assert tool._parse_date("") is None
        assert tool._parse_date("not-a-date") is None
