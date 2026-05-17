"""Integration test: AgentRunner logs tool calls when db is provided."""

from __future__ import annotations

import tempfile, os
from unittest.mock import MagicMock, AsyncMock

import pytest

from nanobot.agent.db import NanobotDB
from nanobot.agent.runner import AgentRunSpec, AgentRunner
from nanobot.providers.base import LLMResponse, ToolCallRequest


@pytest.fixture
def db_path():
    p = os.path.join(tempfile.gettempdir(), f"nanobot_runner_log_test_{os.getpid()}.db")
    yield p
    try:
        if os.path.exists(p):
            os.remove(p)
    except PermissionError:
        pass  # Windows lock


@pytest.mark.asyncio
async def test_runner_logs_tool_call_to_db(db_path):
    db = NanobotDB(db_path=db_path)

    provider = MagicMock()
    call_count = {"n": 0}

    async def chat_with_retry(*, messages, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return LLMResponse(
                content="thinking",
                tool_calls=[ToolCallRequest(id="call_1", name="read_file", arguments={"path": "a.txt"})],
            )
        return LLMResponse(content="done", tool_calls=[], usage={})

    provider.chat_with_retry = chat_with_retry
    tools = MagicMock()
    tools.get_definitions.return_value = []
    tools.execute = AsyncMock(return_value="file content: hello")

    runner = AgentRunner(provider, db=db)
    logged = []
    orig = runner._log_tool_call
    runner._log_tool_call = lambda *a, **kw: logged.append((a, kw)) or orig(*a, **kw)

    result = await runner.run(AgentRunSpec(
        initial_messages=[{"role": "user", "content": "read a.txt"}],
        tools=tools,
        model="test-model",
        max_iterations=3,
        max_tool_result_chars=1000,
        session_key="test_session_xyz",
    ))

    assert result.final_content == "done"
    # Verify _log_tool_call was called
    assert len(logged) == 1, f"Expected 1 log call, got {len(logged)}: {logged}"
    args, kw = logged[0]
    assert args[3] == "read_file", f"Expected read_file, got {args[3]}"
    assert args[0] == "test_session_xyz", f"Expected test_session_xyz, got {args[0]}"
    # Verify DB persisted
    rows = db.query_tool_calls(limit=10)
    assert len(rows) == 1, f"Expected 1 DB row, got {rows}"
    assert rows[0]["tool_name"] == "read_file"
    assert rows[0]["session_key"] == "test_session_xyz"
    assert rows[0]["success"] == 1, f"Expected success=1, got {rows[0]['success']}"
    db.close()


@pytest.mark.asyncio
async def test_runner_logs_failed_tool_to_db(db_path):
    db = NanobotDB(db_path=db_path)

    provider = MagicMock()
    call_count = {"n": 0}

    async def chat_with_retry(*, messages, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return LLMResponse(
                content="try this",
                tool_calls=[ToolCallRequest(id="call_1", name="exec", arguments={"command": "bad"})],
            )
        return LLMResponse(content="done", tool_calls=[], usage={})

    provider.chat_with_retry = chat_with_retry
    tools = MagicMock()
    tools.get_definitions.return_value = []
    tools.execute = AsyncMock(return_value="Error: command failed")

    runner = AgentRunner(provider, db=db)
    logged = []
    orig = runner._log_tool_call
    runner._log_tool_call = lambda *a, **kw: logged.append((a, kw)) or orig(*a, **kw)

    result = await runner.run(AgentRunSpec(
        initial_messages=[{"role": "user", "content": "run bad"}],
        tools=tools,
        model="test-model",
        max_iterations=3,
        max_tool_result_chars=1000,
        session_key="test_session_fail",
    ))

    # Verify logging called once
    assert len(logged) == 1, f"Expected 1 log call, got {len(logged)}: {logged}"
    args, kw = logged[0]
    assert args[3] == "exec"
    assert args[0] == "test_session_fail"

    # Verify DB persisted
    rows = db.query_tool_calls(limit=10)
    assert rows[0]["tool_name"] == "exec"
    assert rows[0]["success"] == 0, f"Expected success=0, got {rows[0]['success']}"
    assert rows[0]["error"] is not None
    db.close()