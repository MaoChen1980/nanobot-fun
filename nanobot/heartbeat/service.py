"""Heartbeat service - periodic alarm clock for the main session."""

from __future__ import annotations

import asyncio
import datetime as dt
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

from nanobot.bus.events import InboundMessage

if TYPE_CHECKING:
    from nanobot.agent.loop import AgentLoop


class HeartbeatService:
    """
    Periodic alarm clock that injects HEARTBEAT.md content into the main
    session via the message bus.

    The main session agent reads the embedded content, decides what to do
    (advance tasks, mark completed, prune stale entries >7 days), and writes
    the updated state back to HEARTBEAT.md.

    This service is intentionally dumb: no LLM pre-judgment, no independent
    task logic.  Just a timer + bus publish with embedded file content.
    """

    def __init__(
        self,
        agent_loop: "AgentLoop",
        interval_s: int = 30 * 60,
        enabled: bool = True,
    ):
        self.agent_loop = agent_loop
        self.interval_s = interval_s
        self.enabled = enabled
        self._running = False
        self._task: asyncio.Task | None = None

    @property
    def heartbeat_file(self) -> Path:
        return self.agent_loop.workspace / "HEARTBEAT.md"

    async def start(self) -> None:
        """Start the heartbeat service."""
        if not self.enabled:
            logger.info("Heartbeat disabled")
            return
        if self._running:
            logger.warning("Heartbeat already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Heartbeat started (every {}s)", self.interval_s)

    def stop(self) -> None:
        """Stop the heartbeat service."""
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None

    async def _run_loop(self) -> None:
        """Main heartbeat loop."""
        while self._running:
            try:
                await asyncio.sleep(self.interval_s)
                if self._running:
                    await self._tick()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Heartbeat error: {}", e)

    async def _tick(self) -> None:
        """Fire a heartbeat trigger into the main session via the bus."""
        if not self.enabled:
            return

        now_ts = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S %Z")

        raw = ""
        if self.heartbeat_file.exists():
            raw = self.heartbeat_file.read_text(encoding="utf-8").strip()

        if not raw:
            # 空文件，按模板创建
            template = (
                "# Heartbeat Task Tracker\n\n"
                "> Auto-processed by HEARTBEAT (30min interval, enabled=true)\n"
                f"> Last update: {now_ts}\n\n"
                "## Active Tasks\n\n"
                "*(none)*\n\n"
                "## Completed\n\n"
                "*(none)*\n\n"
                "> **Cleanup rule**: Completed tasks older than 7 days will be removed by LLM on heartbeat trigger"
            )
            self.heartbeat_file.write_text(template, encoding="utf-8")
            raw = template
            logger.info("Heartbeat: created HEARTBEAT.md template")

        msg = replace(
            InboundMessage(
                channel="cli",
                sender_id="heartbeat",
                chat_id="direct",
                content=(
                    f"[Heartbeat] {now_ts}\n\n"
                    f"=== HEARTBEAT.md ===\n{raw}\n"
                    f"=== END HEARTBEAT ===\n\n"
                    "Above is your last task state (with timestamps).\n"
                    "- Active tasks → continue, update progress\n"
                    "- Done → move to ## Completed, fill in created/completed times\n"
                    "- No longer needed → delete\n"
                    "- Completed tasks >7 days old → remove\n\n"
                    "Write the updated state back to HEARTBEAT.md when done."
                ),
                media=[],
            ),
            session_key_override="cli:direct",
        )
        await self.agent_loop.bus.publish_inbound(msg)
        logger.info("Heartbeat: trigger published to main session via bus")
