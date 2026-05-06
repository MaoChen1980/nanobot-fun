"""Utility functions for AgentLoop."""

from __future__ import annotations

import asyncio
import re
from typing import TYPE_CHECKING, Any

from loguru import logger

if TYPE_CHECKING:
    from nanobot.agent.loop import AgentLoop


def strip_think(text: str | None) -> str | None:
    """Remove thinking blocks, unclosed trailing tags, and tokenizer-level
    template leaks occasionally emitted by some models (notably Gemma 4's
    Ollama renderer).

    Covers:
      1. Well-formed ``<think>...</think>`` and ``<thought>...</thought>`` blocks.
      2. Streaming prefixes where the block is never closed.
      3. *Malformed* opening tags missing the ``>`` -- e.g. ``<think广场…``.
      4. Harmony-style channel markers like ``<channel|>`` / ``<|channel|>``
         **at the start of the text** -- conservative to avoid eating
         explanatory prose that mentions these tokens.
      5. Orphan closing tags ``</think>`` / ``</thought>`` **at the very start
         or end of the text** only, for the same reason.
    """
    if not text:
        return text
    text = re.sub(r"<think>[\s\S]*?</think>", "", text)
    text = re.sub(r"^\s*<think>[\s\S]*$", "", text)
    text = re.sub(r"<thought>[\s\S]*?</thought>", "", text)
    text = re.sub(r"^\s*<thought>[\s\S]*$", "", text)
    text = re.sub(r"<think(?![A-Za-z0-9_\-:>/])", "", text)
    text = re.sub(r"<thought(?![A-Za-z0-9_\-:>/])", "", text)
    text = re.sub(r"^\s*</think>\s*", "", text)
    text = re.sub(r"\s*</think>\s*$", "", text)
    text = re.sub(r"^\s*</thought>\s*", "", text)
    text = re.sub(r"\s*</thought>\s*$", "", text)
    text = re.sub(r"^\s*<\|?channel\|?>\s*", "", text)
    return text.strip()


def runtime_chat_id(msg: Any) -> str:
    """Return the chat id shown in runtime metadata for the model."""
    return str(msg.metadata.get("context_chat_id") or msg.chat_id)


def tool_hint(tool_calls: list) -> str:
    """Format tool calls as concise hints with smart abbreviation."""
    from nanobot.utils.tool_hints import format_tool_hints
    return format_tool_hints(tool_calls)


def effective_session_key(loop: Any, msg: Any) -> str:
    """Return the session key used for task routing and mid-turn injections."""
    from nanobot.agent.loop_constants import UNIFIED_SESSION_KEY
    if loop._unified_session and not msg.session_key_override:
        return UNIFIED_SESSION_KEY
    return msg.session_key


def replay_token_budget(loop: Any) -> int:
    """Derive a token budget for session history replay from the context window."""
    if loop.context_window_tokens <= 0:
        return 0
    max_output = getattr(getattr(loop.provider, "generation", None), "max_tokens", 4096)
    try:
        reserved_output = int(max_output)
    except (TypeError, ValueError):
        reserved_output = 4096
    budget = loop.context_window_tokens - max(1, reserved_output) - 1024
    return budget if budget > 0 else max(128, loop.context_window_tokens // 2)


async def cancel_active_tasks(loop: Any, key: str) -> int:
    """Cancel and await all active tasks and subagents for *key*.

    Returns the total number of cancelled tasks + subagents.
    """
    tasks = loop._active_tasks.pop(key, [])
    cancelled = sum(1 for t in tasks if not t.done() and t.cancel())
    for t in tasks:
        try:
            await t
        except (asyncio.CancelledError, Exception):
            pass
    sub_cancelled = await loop.subagents.cancel_by_session(key)
    return cancelled + sub_cancelled