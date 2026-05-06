"""Tests for TaskExecutor - goal execution coordinator."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from nanobot.agent.task_executor import TaskExecutor, SubtaskExecutionResult


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def provider():
    p = MagicMock()
    p.get_default_model.return_value = "test-model"
    return p


@pytest.fixture
def tools():
    t = MagicMock()
    t.get_definitions.return_value = []
    return t


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def executor(provider, tools, db):
    return TaskExecutor(provider=provider, db=db, tools=tools, model="test-model")


@pytest.fixture
def executor_no_db(provider, tools):
    return TaskExecutor(provider=provider, db=None, tools=tools, model="test-model")


def _make_goal(**overrides) -> dict:
    """Helper to build a minimal goal dict."""
    goal = {
        "id": "g1",
        "title": "Test Goal",
        "status": "in_progress",
        "description": "A test goal",
        "project": "test-project",
        "scope": {
            "structural_constraints": {
                "influential_files": ["config.json"],
                "operation_constraints": ["read_only"],
            }
        },
        "data": {
            "subtasks": [
                {"id": "s0", "title": "subtask_0", "status": "done"},
                {"id": "s1", "title": "subtask_1", "status": "todo"},
                {"id": "s2", "title": "subtask_2", "status": "todo"},
            ],
            "hypothesis_verification": {
                "assumption": {"claim": "test", "expected": "x"},
                "files_read": ["config.json"],
                "verification_attempts": [{"result": {}, "verdict": "passed"}],
                "verdict": "passed",
            },
        },
    }
    goal.update(overrides)
    return goal


def _make_subtask_result(
    stop_reason: str = "completed",
    messages: list | None = None,
) -> SubtaskExecutionResult:
    return SubtaskExecutionResult(
        stop_reason=stop_reason,
        final_content="done",
        messages=messages or [],
        tools_used=[],
    )


# ---------------------------------------------------------------------------
# _build_subtask_messages
# ---------------------------------------------------------------------------


class TestBuildSubtaskMessages:
    def test_includes_goal_title_and_description(self, executor):
        goal = _make_goal()
        subtask = goal["data"]["subtasks"][1]
        messages = executor._build_subtask_messages(goal, subtask)

        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"

        sys_content = messages[0]["content"]
        assert "Test Goal" in sys_content
        assert "A test goal" in sys_content
        assert "test-project" in sys_content

    def test_includes_subtask_info(self, executor):
        goal = _make_goal()
        subtask = goal["data"]["subtasks"][1]
        messages = executor._build_subtask_messages(goal, subtask)

        sys_content = messages[0]["content"]
        assert "subtask_1" in sys_content
        assert "s1" in sys_content
        assert "1/3 subtasks completed" in sys_content
        assert "declare_checkpoint" in sys_content

    def test_includes_structural_constraints(self, executor):
        goal = _make_goal()
        subtask = goal["data"]["subtasks"][1]
        messages = executor._build_subtask_messages(goal, subtask)

        sys_content = messages[0]["content"]
        assert "config.json" in sys_content
        assert "read_only" in sys_content

    def test_user_message_format(self, executor):
        goal = _make_goal()
        subtask = goal["data"]["subtasks"][1]
        messages = executor._build_subtask_messages(goal, subtask)

        assert messages[1]["content"] == "Execute subtask s1: subtask_1"

    def test_empty_goal_fields_dont_crash(self, executor):
        goal = _make_goal(title="", description="", project="")
        subtask = goal["data"]["subtasks"][0]
        messages = executor._build_subtask_messages(goal, subtask)
        assert len(messages) == 2

    def test_no_subtasks_shows_zero_progress(self, executor):
        goal = _make_goal(data={"subtasks": []})
        subtask = {"id": "s1", "title": "standalone"}
        messages = executor._build_subtask_messages(goal, subtask)
        assert "0/0 subtasks completed" in messages[0]["content"]


# ---------------------------------------------------------------------------
# _has_declared_checkpoint
# ---------------------------------------------------------------------------


class TestHasDeclaredCheckpoint:
    def test_no_messages_returns_false(self, executor):
        assert not executor._has_declared_checkpoint([], "s1")

    def test_matching_openai_format(self, executor):
        messages = [
            {
                "role": "assistant",
                "tool_calls": [
                    {
                        "function": {
                            "name": "declare_checkpoint",
                            "arguments": '{"subtask_id": "s1", "summary": "done"}',
                        }
                    }
                ],
            }
        ]
        assert executor._has_declared_checkpoint(messages, "s1")

    def test_non_matching_openai_format(self, executor):
        messages = [
            {
                "role": "assistant",
                "tool_calls": [
                    {
                        "function": {
                            "name": "declare_checkpoint",
                            "arguments": '{"subtask_id": "s2", "summary": "done"}',
                        }
                    }
                ],
            }
        ]
        assert not executor._has_declared_checkpoint(messages, "s1")

    def test_matching_anthropic_format(self, executor):
        messages = [
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "name": "declare_checkpoint",
                        "input": {"subtask_id": "s1", "summary": "done"},
                    }
                ],
            }
        ]
        assert executor._has_declared_checkpoint(messages, "s1")

    def test_non_matching_anthropic_format(self, executor):
        messages = [
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "name": "declare_checkpoint",
                        "input": {"subtask_id": "s2"},
                    }
                ],
            }
        ]
        assert not executor._has_declared_checkpoint(messages, "s1")

    def test_different_tool_ignored(self, executor):
        messages = [
            {
                "role": "assistant",
                "tool_calls": [
                    {"function": {"name": "read_file", "arguments": '{"path": "x"}'}}
                ],
            }
        ]
        assert not executor._has_declared_checkpoint(messages, "s1")

    def test_bad_json_arguments_doesnt_crash(self, executor):
        messages = [
            {
                "role": "assistant",
                "tool_calls": [
                    {
                        "function": {
                            "name": "declare_checkpoint",
                            "arguments": "not-json",
                        }
                    }
                ],
            }
        ]
        assert not executor._has_declared_checkpoint(messages, "s1")


# ---------------------------------------------------------------------------
# _check_subtask_done
# ---------------------------------------------------------------------------


class TestCheckSubtaskDone:
    def test_stop_reason_completed(self, executor):
        result = _make_subtask_result(stop_reason="completed")
        assert executor._check_subtask_done(result, {"id": "s1"})

    def test_declare_checkpoint_in_messages(self, executor):
        result = _make_subtask_result(
            stop_reason="max_iterations",
            messages=[
                {
                    "role": "assistant",
                    "tool_calls": [
                        {
                            "function": {
                                "name": "declare_checkpoint",
                                "arguments": '{"subtask_id": "s1", "summary": "x"}',
                            }
                        }
                    ],
                }
            ],
        )
        assert executor._check_subtask_done(result, {"id": "s1"})

    def test_declare_checkpoint_wrong_subtask(self, executor):
        result = _make_subtask_result(
            stop_reason="max_iterations",
            messages=[
                {
                    "role": "assistant",
                    "tool_calls": [
                        {
                            "function": {
                                "name": "declare_checkpoint",
                                "arguments": '{"subtask_id": "s999", "summary": "x"}',
                            }
                        }
                    ],
                }
            ],
        )
        assert not executor._check_subtask_done(result, {"id": "s1"})

    def test_no_declare_not_completed(self, executor):
        result = _make_subtask_result(stop_reason="max_iterations")
        assert not executor._check_subtask_done(result, {"id": "s1"})


# ---------------------------------------------------------------------------
# execute_goal (with mocked AgentRunner)
# ---------------------------------------------------------------------------


class TestExecuteGoal:
    async def test_already_completed(self, executor):
        goal = _make_goal(status="completed")
        result = await executor.execute_goal(goal_id="g1", goal=goal)
        assert result.status == "already_completed"

    async def test_blocked_and_cannot_resume(self, executor):
        goal = _make_goal(
            status="blocked",
            data={
                "subtasks": [{"id": "s0", "title": "s0", "status": "done"}],
                "hypothesis_verification": {
                    "files_read": ["config.json"],
                    "assumption": {"claim": "x"},
                    "verification_attempts": [{"result": {}, "verdict": "failed"}]
                    * 3,
                    "verdict": "failed",
                },
            },
        )
        result = await executor.execute_goal(goal_id="g1", goal=goal)
        assert result.status == "blocked"

    async def test_subtask_0_not_complete_returns_blocked(self, executor, db):
        goal = _make_goal(
            data={
                "subtasks": [{"id": "s0", "title": "s0", "status": "in_progress"}],
                "hypothesis_verification": {},
            },
        )
        db.get_goal.return_value = goal
        result = await executor.execute_goal(goal_id="g1", goal=goal)
        assert result.status == "blocked"
        assert "subtask_0" in (result.message or "")

    async def test_execute_goal_no_db(self, executor_no_db):
        executor_no_db._runner = MagicMock()
        executor_no_db._runner.run = AsyncMock(
            return_value=MagicMock(
                stop_reason="completed",
                final_content="done",
                messages=[],
                tools_used=[],
                usage={},
                tool_events=[],
                had_injections=False,
                error=None,
            )
        )
        # Only s0 (already done) — no subtasks to execute, so the goal
        # completes without needing _mark_subtask_done (which is a no-op without DB).
        goal = _make_goal(data={
            "subtasks": [
                {"id": "s0", "title": "s0", "status": "done"},
            ],
            "hypothesis_verification": {
                "assumption": {"claim": "test", "expected": "x"},
                "files_read": ["config.json"],
                "verification_attempts": [{"result": {}, "verdict": "passed"}],
                "verdict": "passed",
            },
        })
        result = await executor_no_db.execute_goal(goal_id="g1", goal=goal)
        assert result.status == "completed"

    async def test_execute_subtask_runs_agent(self, executor, db):
        """Verify that _execute_subtask creates AgentRunSpec with context."""
        goal = _make_goal()

        executor._runner = MagicMock()
        executor._runner.run = AsyncMock(
            return_value=MagicMock(
                stop_reason="completed",
                final_content="done",
                messages=[],
                tools_used=[],
                usage={},
                tool_events=[],
                had_injections=False,
                error=None,
            )
        )

        result = await executor.execute_goal(goal_id="g1", goal=goal)

        assert result.status == "completed"

        # Verify the spec had meaningful initial_messages
        call_args = executor._runner.run.call_args
        spec = call_args[0][0]
        assert len(spec.initial_messages) == 2
        assert "Test Goal" in spec.initial_messages[0]["content"]

    async def test_checkpoint_saved_after_subtask(self, executor, db):
        """Verify checkpoint is saved via insert_event."""
        # Use a mutable goal dict so in-place mutations by _mark_subtask_done
        # are visible when get_goal returns the same object.
        goal = _make_goal(
            data={
                "subtasks": [
                    {"id": "s0", "title": "s0", "status": "done"},
                    {"id": "s1", "title": "s1", "status": "todo"},
                ],
                "hypothesis_verification": {
                    "assumption": {"claim": "test", "expected": "x"},
                    "files_read": ["config.json"],
                    "verification_attempts": [{"result": {}, "verdict": "passed"}],
                    "verdict": "passed",
                },
            },
        )
        # get_goal returns the same mutable dict so status updates are visible
        db.get_goal.return_value = goal

        executor._runner = MagicMock()
        executor._runner.run = AsyncMock(
            return_value=MagicMock(
                stop_reason="completed",
                final_content="subtask done",
                messages=[],
                tools_used=["read_file"],
                usage={},
                tool_events=[],
                had_injections=False,
                error=None,
            )
        )

        await executor.execute_goal(goal_id="g1", goal=goal)

        insert_calls = [
            c
            for c in db.insert_event.call_args_list
            if c.kwargs.get("event_type") == "checkpoint"
        ]
        assert len(insert_calls) >= 1  # at least s1 checkpoint saved


# ---------------------------------------------------------------------------
# Checkpoint save/load
# ---------------------------------------------------------------------------


class TestCheckpoint:
    def test_save_uses_json(self, executor, db):
        result = _make_subtask_result(stop_reason="completed", messages=[])
        executor._save_checkpoint("g1", "s1", result)

        call = db.insert_event.call_args
        assert call is not None
        content = call.kwargs.get("content", "")
        parsed = json.loads(content)
        assert parsed["subtask_id"] == "s1"
        assert parsed["stop_reason"] == "completed"

    def test_load_returns_none_no_db(self, executor_no_db):
        assert executor_no_db._get_latest_checkpoint("g1") is None

    def test_load_parses_json(self, executor, db):
        db.list_events.return_value = [
            {
                "content": json.dumps(
                    {"subtask_id": "s1", "stop_reason": "completed"}
                ),
            }
        ]
        result = executor._get_latest_checkpoint("g1")
        assert result is not None
        assert result["subtask_id"] == "s1"

    def test_load_skips_non_json(self, executor, db):
        db.list_events.return_value = [
            {"content": "not-json-at-all"},
        ]
        result = executor._get_latest_checkpoint("g1")
        assert result is None


# ---------------------------------------------------------------------------
# resume_goal
# ---------------------------------------------------------------------------


class TestResumeGoal:
    async def test_goal_not_found(self, executor, db):
        db.get_goal.return_value = None
        result = await executor.resume_goal(goal_id="g1")
        assert result.status == "error"

    async def test_resume_blocked_rechecks_subtask_0(self, executor, db):
        goal = _make_goal(
            status="blocked",
            data={
                "subtasks": [{"id": "s0", "title": "s0", "status": "done"}],
                "hypothesis_verification": {},
            },
        )
        db.get_goal.return_value = goal
        result = await executor.resume_goal(goal_id="g1")
        assert result.status == "blocked"
