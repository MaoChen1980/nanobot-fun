"""Tests for GatewayApplication — gateway service orchestration."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from nanobot.config.schema import Config
from nanobot.gateway.app import GatewayApplication


@pytest.fixture
def config() -> Config:
    return Config()


def test_init_stores_config(config: Config) -> None:
    app = GatewayApplication(config)
    assert app.config is config
    assert app.port == config.gateway.port


def test_init_port_override(config: Config) -> None:
    app = GatewayApplication(config, port=9999)
    assert app.port == 9999


def test_init_services_creates_all_components(config: Config) -> None:
    """Verify _init_services creates the expected services."""
    app = GatewayApplication(config)

    with (
        patch("nanobot.bus.queue.MessageBus") as mb,
        patch("nanobot.providers.factory.build_provider_snapshot") as bps,
        patch("nanobot.agent.db.NanobotDB") as ndb,
        patch("nanobot.session.manager.SessionManager") as sm,
        patch("nanobot.cron.service.CronService") as cs,
        patch("nanobot.agent.loop.AgentLoop") as al,
        patch("nanobot.bus.manager.ChannelManager") as chm,
        patch("nanobot.proxy.manager.ProxyManager") as pm,
        patch("nanobot.heartbeat.service.HeartbeatService") as hb,
        patch("nanobot.utils.gitstore.sync_workspace_templates"),
    ):
        provider_snapshot = MagicMock()
        provider_snapshot.model = "test-model"
        provider_snapshot.context_window_tokens = 128000
        provider_snapshot.signature = ("test",)
        bps.return_value = provider_snapshot

        app._init_services()

    assert app.bus is not None
    assert app.provider is not None
    assert app.nanobot_db is not None
    assert app.session_manager is not None
    assert app.cron is not None
    assert app.agent is not None
    assert app.channels is not None
    assert app.proxy_manager is not None
    assert app.heartbeat is not None


def test_shutdown_without_init_does_not_crash() -> None:
    """_shutdown must guard against None services."""
    app = GatewayApplication(Config())

    import asyncio
    asyncio.run(app._shutdown())
