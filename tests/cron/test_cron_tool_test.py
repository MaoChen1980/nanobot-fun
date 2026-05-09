"""Test cron action=test with dry_run."""

import pytest, asyncio
from pathlib import Path

from nanobot.cron.service import CronService
from nanobot.agent.tools.cron import CronTool


def _make_tool(tmp_path: Path) -> CronTool:
    service = CronService(tmp_path / "cron" / "jobs.json")
    return CronTool(service)


def _make_tool_with_on_job(tmp_path: Path) -> CronTool:
    """Tool with a no-op on_job handler so execution can be tested."""
    service = CronService(tmp_path / "cron" / "jobs.json")
    service.on_job = lambda job: asyncio.sleep(0)
    return CronTool(service)


@pytest.mark.asyncio
async def test_test_job_shows_execution_log(tmp_path: Path) -> None:
    """action=test runs the job immediately and returns step-by-step log."""
    tool = _make_tool_with_on_job(tmp_path)
    tool.set_context("telegram", "chat-1")
    result = tool._add_job("test-task", "check the weather for Beijing", 300, None, None, None, True)
    assert "Created job" in result
    job_id = result.split("id: ")[1].split(")")[0].strip()

    # Run test: expect execution log in result
    test_result = await tool._test_job(job_id, dry_run=True)
    assert "Test running job" in test_result
    assert job_id in test_result
    assert ("Dry run" in test_result or "[Mode]" in test_result)


@pytest.mark.asyncio
async def test_test_job_without_job_id_uses_current_context(tmp_path: Path) -> None:
    """When inside a cron job, job_id defaults to current job."""
    tool = _make_tool_with_on_job(tmp_path)
    tool.set_context("telegram", "chat-1")
    result = tool._add_job("task-2", "say hello", 300, None, None, None, True)
    job_id = result.split("id: ")[1].split(")")[0].strip()

    # Simulate being inside a cron job
    token = tool._in_cron_context.set(True)
    tool.set_current_job_id(job_id)
    try:
        test_result = await tool._test_job(None, dry_run=True)
        assert "Test running job" in test_result
    finally:
        tool._in_cron_context.reset(token)


@pytest.mark.asyncio
async def test_test_job_not_found_returns_error(tmp_path: Path) -> None:
    """action=test with unknown job_id returns error."""
    tool = _make_tool_with_on_job(tmp_path)
    tool.set_context("telegram", "chat-1")
    result = await tool._test_job("nonexistent-id", dry_run=False)
    assert "not found" in result


@pytest.mark.asyncio
async def test_test_job_dry_run_skips_delivery(tmp_path: Path) -> None:
    """dry_run=True sets deliver=False for the execution."""
    tool = _make_tool_with_on_job(tmp_path)
    tool.set_context("telegram", "chat-1")
    result = tool._add_job("dryrun-task", "test message", 300, None, None, None, True)
    job_id = result.split("id: ")[1].split(")")[0].strip()

    # Check dry_run flag is passed
    test_result = await tool._test_job(job_id, dry_run=True)
    assert "Dry run" in test_result or "[Test Execution Log]" in test_result


def test_validate_params_test_requires_job_id(tmp_path: Path) -> None:
    """action=test outside cron context requires job_id."""
    tool = _make_tool_with_on_job(tmp_path)
    tool.set_context("telegram", "chat-1")
    errors = tool.validate_params({"action": "test"})
    assert any("job_id" in e for e in errors)


def test_validate_params_test_skips_job_id_in_cron_context(tmp_path: Path) -> None:
    """action=test inside cron context does NOT require job_id."""
    tool = _make_tool_with_on_job(tmp_path)
    tool.set_context("telegram", "chat-1")
    token = tool._in_cron_context.set(True)
    try:
        errors = tool.validate_params({"action": "test"})
        assert not any("job_id" in e for e in errors)
    finally:
        tool._in_cron_context.reset(token)


def test_execute_method_routes_test_action(tmp_path: Path) -> None:
    """execute() routes action=test to _test_job()."""
    tool = _make_tool_with_on_job(tmp_path)
    tool.set_context("telegram", "chat-1")
    result = tool._add_job("route-test", "check something", 300, None, None, None, True)
    job_id = result.split("id: ")[1].split(")")[0].strip()

    result = asyncio.run(tool.execute(action="test", job_id=job_id, dry_run=True))
    assert "Test running job" in result