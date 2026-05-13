"""Constants for AgentRunner."""

from __future__ import annotations

_DEFAULT_ERROR_MESSAGE = "Sorry, I encountered an error calling the AI model."
_PERSISTED_MODEL_ERROR_PLACEHOLDER = "[Assistant reply unavailable due to model error.]"
_MAX_EMPTY_RETRIES = 2
_MAX_LENGTH_RECOVERIES = 3
_MAX_INJECTIONS_PER_TURN = 50
_MAX_INJECTION_CYCLES = 20
_SNIP_SAFETY_BUFFER = 1024
_MICROCOMPACT_KEEP_RECENT = 20
_MICROCOMPACT_MIN_CHARS = 500
_COMPACTABLE_TOOLS = frozenset({
    "read_file", "exec", "grep", "glob",
    "web_search", "web_fetch", "list_dir",
})
_BACKFILL_CONTENT = "[Tool result unavailable — call was interrupted or lost]"

# ----------------------------------------------------------------------
# Observe events (/think, /tool) — injected via runner callback
# ----------------------------------------------------------------------
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nanobot.agent.loop import AgentLoop

_cb_loop_ref: "AgentLoop | None" = None  # Set by loop before runner.run()

def _get_emit_callback() -> callable | None:
    loop = _cb_loop_ref
    if loop is None:
        from nanobot.agent.context_vars import _current_agent_loop
        loop = _current_agent_loop.get()
    if loop is None:
        return None
    return loop._emit_observe_event