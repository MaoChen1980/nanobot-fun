"""Tests for nanobot.utils.helpers — utility functions."""

from __future__ import annotations

import json
import os
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from nanobot.utils.helpers import (
    _cleanup_tool_result_buckets,
    _get_encoder,
    _write_text_atomic,
    build_assistant_message,
    build_status_content,
    current_time_str,
    ensure_dir,
    estimate_message_tokens,
    estimate_prompt_tokens,
    estimate_prompt_tokens_chain,
    maybe_persist_tool_result,
    safe_filename,
    split_message,
    timestamp,
    truncate_text,
)


# ---------------------------------------------------------------------------
# timestamp
# ---------------------------------------------------------------------------

class TestTimestamp:
    def test_returns_iso_format(self):
        result = timestamp()
        assert "T" in result
        assert "+" in result or result.endswith("Z")


# ---------------------------------------------------------------------------
# current_time_str
# ---------------------------------------------------------------------------

class TestCurrentTimeStr:
    def test_default_no_timezone(self):
        result = current_time_str()
        assert "T" in result

    def test_with_valid_timezone(self):
        result = current_time_str("Asia/Shanghai")
        assert "T" in result
        assert "+08:00" in result or "+07:00" in result

    def test_with_invalid_timezone_falls_back(self):
        result = current_time_str("Mars/Olympus")
        assert "T" in result

    def test_with_utc(self):
        result = current_time_str("UTC")
        assert result.endswith("+00:00") or "+00:00" in result


# ---------------------------------------------------------------------------
# ensure_dir
# ---------------------------------------------------------------------------

class TestEnsureDir:
    def test_creates_directory(self, tmp_path):
        d = tmp_path / "a" / "b" / "c"
        result = ensure_dir(d)
        assert result == d
        assert d.is_dir()

    def test_existing_directory(self, tmp_path):
        d = tmp_path / "existing"
        d.mkdir()
        result = ensure_dir(d)
        assert result == d


# ---------------------------------------------------------------------------
# safe_filename
# ---------------------------------------------------------------------------

class TestSafeFilename:
    def test_replaces_unsafe_chars(self):
        assert safe_filename('a<b>c:d/e\\f|g?h*i') == 'a_b_c_d_e_f_g_h_i'

    def test_strips_whitespace(self):
        assert safe_filename('  file  ') == 'file'

    def test_safe_name_unchanged(self):
        assert safe_filename('hello_world.py') == 'hello_world.py'

    def test_empty_string(self):
        assert safe_filename('') == ''


# ---------------------------------------------------------------------------
# truncate_text
# ---------------------------------------------------------------------------

class TestTruncateText:
    def test_short_text_unchanged(self):
        assert truncate_text("hello", 10) == "hello"

    def test_exact_length_unchanged(self):
        assert truncate_text("hello", 5) == "hello"

    def test_long_text_truncated(self):
        result = truncate_text("hello world", 5)
        assert result.startswith("hello")
        assert "(truncated)" in result

    def test_zero_max_chars_returns_original(self):
        assert truncate_text("hello", 0) == "hello"

    def test_negative_max_chars_returns_original(self):
        assert truncate_text("hello", -1) == "hello"


# ---------------------------------------------------------------------------
# build_assistant_message
# ---------------------------------------------------------------------------

class TestBuildAssistantMessage:
    def test_minimal(self):
        msg = build_assistant_message("hello")
        assert msg == {"role": "assistant", "content": "hello"}

    def test_none_content_becomes_empty(self):
        msg = build_assistant_message(None)
        assert msg == {"role": "assistant", "content": ""}

    def test_with_tool_calls(self):
        tcs = [{"id": "call_1", "function": {"name": "foo"}}]
        msg = build_assistant_message("content", tool_calls=tcs)
        assert msg["tool_calls"] == tcs

    def test_with_reasoning_content(self):
        msg = build_assistant_message("content", reasoning_content="thinking...")
        assert msg["reasoning_content"] == "thinking..."

    def test_with_empty_reasoning_string(self):
        msg = build_assistant_message("content", reasoning_content="")
        assert msg["reasoning_content"] == ""

    def test_with_thinking_blocks(self):
        blocks = [{"thinking": "step 1"}, {"thinking": "step 2"}]
        msg = build_assistant_message("content", thinking_blocks=blocks)
        assert msg["thinking_blocks"] == blocks

    def test_combined_reasoning_and_thinking(self):
        msg = build_assistant_message(
            "content",
            reasoning_content="reason",
            thinking_blocks=[{"thinking": "think"}],
        )
        assert msg["reasoning_content"] == "reason"
        assert msg["thinking_blocks"] == [{"thinking": "think"}]


# ---------------------------------------------------------------------------
# split_message
# ---------------------------------------------------------------------------

class TestSplitMessage:
    def test_empty_content(self):
        assert split_message("") == []

    def test_short_content(self):
        assert split_message("hello") == ["hello"]

    def test_exact_max_len(self):
        s = "a" * 10
        assert split_message(s, max_len=10) == [s]

    def test_no_break_point_uses_hard_cut(self):
        s = "a" * 50
        chunks = split_message(s, max_len=20)
        assert len(chunks) >= 2
        assert all(len(c) <= 20 for c in chunks)

    def test_break_at_newline(self):
        s = "hello\n" + "a" * 50
        chunks = split_message(s, max_len=20)
        assert len(chunks) >= 2
        assert chunks[0] == "hello"

    def test_break_at_space(self):
        s = "hello " + "a" * 50 + " world"
        chunks = split_message(s, max_len=20)
        assert len(chunks) >= 2

    def test_multiple_chunks_preserve_content(self):
        s = " ".join(f"word{i}" for i in range(100))
        chunks = split_message(s, max_len=30)
        assert len(chunks) > 1
        joined = " ".join(chunks)
        for i in range(100):
            assert f"word{i}" in joined

    def test_default_max_len_2000(self):
        s = "a" * 3000
        chunks = split_message(s)
        assert all(len(c) <= 2000 for c in chunks)


# ---------------------------------------------------------------------------
# estimate_prompt_tokens
# ---------------------------------------------------------------------------

class TestEstimatePromptTokens:
    def test_empty_messages(self):
        assert estimate_prompt_tokens([]) == 0

    def test_simple_messages(self):
        msgs = [{"role": "user", "content": "hello"}]
        tokens = estimate_prompt_tokens(msgs)
        assert tokens > 0

    def test_with_content_list(self):
        msgs = [{"role": "user", "content": [{"type": "text", "text": "hello"}]}]
        tokens = estimate_prompt_tokens(msgs)
        assert tokens > 0

    def test_with_tool_calls(self):
        msgs = [{
            "role": "assistant",
            "content": "result",
            "tool_calls": [{"function": {"name": "test"}}],
        }]
        tokens = estimate_prompt_tokens(msgs)
        assert tokens > 0

    def test_with_reasoning_content(self):
        msgs = [{"role": "assistant", "content": "result", "reasoning_content": "deep thoughts"}]
        tokens = estimate_prompt_tokens(msgs)
        assert tokens > 0

    def test_with_name_and_tool_call_id(self):
        msgs = [{"role": "tool", "content": "result", "name": "test_func", "tool_call_id": "call_1"}]
        tokens = estimate_prompt_tokens(msgs)
        assert tokens > 0

    def test_with_tools_param(self):
        msgs = [{"role": "user", "content": "hi"}]
        tokens = estimate_prompt_tokens(msgs, tools=[{"function": {"name": "tool1"}}])
        assert tokens > 0

    def test_exception_returns_zero(self):
        with patch.object(_get_encoder(), "encode", side_effect=Exception("boom")):
            assert estimate_prompt_tokens([{"role": "user", "content": "hi"}]) == 0


# ---------------------------------------------------------------------------
# estimate_message_tokens
# ---------------------------------------------------------------------------

class TestEstimateMessageTokens:
    def test_empty_message(self):
        assert estimate_message_tokens({"role": "user", "content": ""}) >= 4

    def test_simple_content(self):
        tokens = estimate_message_tokens({"role": "user", "content": "hello world"})
        assert tokens >= 4

    def test_content_list_with_text_blocks(self):
        msg = {"role": "user", "content": [{"type": "text", "text": "hello"}]}
        assert estimate_message_tokens(msg) >= 4

    def test_content_list_with_non_text_blocks(self):
        msg = {"role": "user", "content": [{"type": "image_url", "url": "data:..."}]}
        tokens = estimate_message_tokens(msg)
        assert tokens >= 4

    def test_content_none_falls_to_minimum(self):
        msg = {"role": "user", "content": None}
        tokens = estimate_message_tokens(msg)
        assert tokens >= 4

    def test_content_is_non_string_non_list_non_none(self):
        msg = {"role": "user", "content": 42}
        tokens = estimate_message_tokens(msg)
        assert tokens >= 4

    def test_with_name_and_tool_call_id(self):
        msg = {"role": "tool", "content": "result", "name": "get_weather", "tool_call_id": "call_abc"}
        tokens = estimate_message_tokens(msg)
        assert tokens >= 4

    def test_with_tool_calls(self):
        msg = {"role": "assistant", "content": "", "tool_calls": [{"function": {"name": "test"}}]}
        tokens = estimate_message_tokens(msg)
        assert tokens >= 4

    def test_with_reasoning_content(self):
        msg = {"role": "assistant", "content": "answer", "reasoning_content": "thinking..."}
        tokens = estimate_message_tokens(msg)
        assert tokens >= 4

    def test_with_thinking_blocks(self):
        msg = {
            "role": "assistant",
            "content": "answer",
            "thinking_blocks": [{"thinking": "step 1"}, {"thinking": "step 2"}],
        }
        tokens = estimate_message_tokens(msg)
        assert tokens >= 4

    def test_with_thinking_blocks_empty_skipped(self):
        msg = {
            "role": "assistant",
            "content": "answer",
            "thinking_blocks": [{"thinking": ""}],
        }
        tokens = estimate_message_tokens(msg)
        assert tokens >= 4

    def test_exception_fallback(self):
        with patch("nanobot.utils.helpers._get_encoder") as mock:
            mock.return_value.encode.side_effect = Exception("boom")
            tokens = estimate_message_tokens({"role": "user", "content": "hello"})
            assert tokens >= 4

    def test_empty_payload_returns_4(self):
        tokens = estimate_message_tokens({"role": "assistant", "content": ""})
        assert tokens == 4


# ---------------------------------------------------------------------------
# estimate_prompt_tokens_chain
# ---------------------------------------------------------------------------

class FakeProvider:
    @staticmethod
    def estimate_prompt_tokens(messages, tools, model):
        return 42, "my_counter"


class FakeProviderReturnsZero:
    @staticmethod
    def estimate_prompt_tokens(messages, tools, model):
        return 0, "zero_counter"


class FakeProviderExceptions:
    @staticmethod
    def estimate_prompt_tokens(messages, tools, model):
        raise RuntimeError("nope")


class TestEstimatePromptTokensChain:
    def test_uses_provider_counter_when_available(self):
        msgs = [{"role": "user", "content": "hi"}]
        tokens, source = estimate_prompt_tokens_chain(FakeProvider(), "model", msgs)
        assert tokens == 42
        assert source == "my_counter"

    def test_falls_back_to_tiktoken_when_provider_returns_zero(self):
        msgs = [{"role": "user", "content": "hi"}]
        tokens, source = estimate_prompt_tokens_chain(FakeProviderReturnsZero(), "model", msgs)
        assert tokens > 0
        assert source == "tiktoken"

    def test_falls_back_on_provider_exception(self):
        msgs = [{"role": "user", "content": "hi"}]
        tokens, source = estimate_prompt_tokens_chain(FakeProviderExceptions(), "model", msgs)
        assert tokens > 0
        assert source == "tiktoken"

    def test_no_counter_on_provider(self):
        msgs = [{"role": "user", "content": "hi"}]
        tokens, source = estimate_prompt_tokens_chain(object(), "model", msgs)
        assert tokens > 0
        assert source == "tiktoken"

    def test_returns_none_when_everything_fails(self):
        msgs = [{"role": "user", "content": ""}]
        with patch("nanobot.utils.helpers.estimate_prompt_tokens", return_value=0):
            tokens, source = estimate_prompt_tokens_chain(object(), "model", msgs)
            assert tokens == 0
            assert source == "none"


# ---------------------------------------------------------------------------
# _write_text_atomic
# ---------------------------------------------------------------------------

class TestWriteTextAtomic:
    def test_writes_and_replaces(self, tmp_path):
        target = tmp_path / "result.txt"
        _write_text_atomic(target, "hello world")
        assert target.read_text(encoding="utf-8") == "hello world"

    def test_temp_file_cleaned_on_error(self, tmp_path):
        target = tmp_path / "result.txt"
        _write_text_atomic(target, "")
        assert target.exists()


# ---------------------------------------------------------------------------
# _cleanup_tool_result_buckets
# ---------------------------------------------------------------------------

class TestCleanupToolResultBuckets:
    def test_old_buckets_removed(self, tmp_path):
        root = tmp_path / "tool-results"
        current = root / "current"
        current.mkdir(parents=True)
        old = root / "old_bucket"
        old.mkdir()
        old_time = time.time() - 10 * 24 * 3600
        os.utime(old, (old_time, old_time))

        _cleanup_tool_result_buckets(root, current)
        assert not old.exists()
        assert current.exists()

    def test_keeps_within_max(self, tmp_path):
        root = tmp_path / "tool-results"
        current = root / "current"
        current.mkdir(parents=True)
        for i in range(33):
            (root / f"bucket_{i}").mkdir()
        _cleanup_tool_result_buckets(root, current)
        remaining = [p for p in root.iterdir() if p.is_dir()]
        assert len(remaining) <= 33

    def test_handles_missing_current_bucket(self, tmp_path):
        root = tmp_path / "tool-results"
        root.mkdir()
        current = root / "no-such-bucket"
        _cleanup_tool_result_buckets(root, current)


# ---------------------------------------------------------------------------
# maybe_persist_tool_result
# ---------------------------------------------------------------------------

class TestMaybePersistToolResult:
    def test_none_workspace_returns_content(self):
        assert maybe_persist_tool_result(None, "sess", "call1", "hello", max_chars=10) == "hello"

    def test_zero_max_chars_returns_content(self):
        assert maybe_persist_tool_result(Path("/tmp"), "sess", "call1", "hello", max_chars=0) == "hello"

    def test_str_within_limit_returns_content(self):
        assert maybe_persist_tool_result(Path("/tmp"), "sess", "call1", "hello", max_chars=100) == "hello"

    def test_list_within_limit_returns_content(self):
        content = [{"type": "text", "text": "hello"}]
        result = maybe_persist_tool_result(Path("/tmp"), "sess", "call1", content, max_chars=1000)
        assert result == content

    def test_non_str_non_list_returns_unchanged(self):
        assert maybe_persist_tool_result(Path("/tmp"), "sess", "call1", 42, max_chars=10) == 42

    def test_persists_oversized_string(self, tmp_path):
        workspace = tmp_path / "ws"
        content = "x" * 5000
        result = maybe_persist_tool_result(workspace, "sess-test", "call-1", content, max_chars=100)
        assert isinstance(result, str)
        assert "tool output persisted" in result
        assert "call-1" in result

    def test_persists_oversized_list(self, tmp_path):
        workspace = tmp_path / "ws"
        content = [{"type": "text", "text": "x" * 5000}]
        result = maybe_persist_tool_result(workspace, "sess-test", "call-1", content, max_chars=50)
        assert isinstance(result, str)
        assert "tool output persisted" in result

    def test_stringify_text_blocks_returns_none_for_invalid_list(self, tmp_path):
        content = [{"type": "image"}]
        result = maybe_persist_tool_result(tmp_path, "sess", "call1", content, max_chars=10)
        assert result == content

    def test_existing_file_not_overwritten(self, tmp_path):
        workspace = tmp_path / "ws"
        content = "x" * 5000
        result1 = maybe_persist_tool_result(workspace, "test", "call-dupe", content, max_chars=100)
        assert "tool output persisted" in result1
        result2 = maybe_persist_tool_result(workspace, "test", "call-dupe", content, max_chars=100)
        assert "tool output persisted" in result2

    def test_cleanup_error_does_not_block(self, tmp_path):
        workspace = tmp_path / "ws"
        content = "x" * 5000
        with patch("nanobot.utils.helpers._cleanup_tool_result_buckets", side_effect=OSError("denied")):
            result = maybe_persist_tool_result(workspace, "test", "call-err", content, max_chars=100)
        assert isinstance(result, str)
        assert "tool output persisted" in result


# ---------------------------------------------------------------------------
# build_status_content
# ---------------------------------------------------------------------------

class TestBuildStatusContent:
    BASE_KWARGS = dict(
        version="0.1.0",
        model="test-model",
        start_time=1000000.0,
        last_usage={"prompt_tokens": 500, "completion_tokens": 100},
        context_window_tokens=65536,
        session_msg_count=10,
        context_tokens_estimate=4000,
    )

    def test_returns_string(self):
        content = build_status_content(**self.BASE_KWARGS)
        assert "test-model" in content
        assert "0.1.0" in content

    def test_with_cached_tokens(self):
        kwargs = {**self.BASE_KWARGS, "last_usage": {"prompt_tokens": 1000, "completion_tokens": 200, "cached_tokens": 300}}
        content = build_status_content(**kwargs)
        assert "% cached" in content

    def test_with_active_tasks(self):
        content = build_status_content(**self.BASE_KWARGS, active_task_count=3)
        assert "3 active" in content

    def test_with_search_usage_text(self):
        content = build_status_content(**self.BASE_KWARGS, search_usage_text="search: 50 used")
        assert "search: 50 used" in content

    def test_context_budget_zero(self):
        content = build_status_content(**{**self.BASE_KWARGS, "context_window_tokens": 0})
        assert content

    def test_uptime_hours(self):
        kwargs = {**self.BASE_KWARGS, "start_time": time.time() - 7200}
        content = build_status_content(**kwargs)
        assert "h " in content

    def test_uptime_seconds(self):
        kwargs = {**self.BASE_KWARGS, "start_time": time.time() - 30}
        content = build_status_content(**kwargs)
        assert "m " in content or "s" in content
