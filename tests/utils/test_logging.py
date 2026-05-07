"""Tests for nanobot.utils.logging — LoggerConfig."""

from unittest.mock import patch

from nanobot.config.schema import LogConfig
from nanobot.utils.logging import LoggerConfig, logger_config


class TestLoggerConfig:
    def test_configure_returns_early_when_already_configured(self):
        """Second call to configure returns without re-adding handlers."""
        cfg = LoggerConfig()
        cfg._configured = True
        cfg.configure(LogConfig(enabled=True, level="DEBUG", console=False, file=None))
        assert cfg._configured is True

    def test_disabled_logging_skips_handlers(self):
        """When enabled=False, handlers are not added and _configured stays False."""
        cfg = LoggerConfig()
        cfg.configure(LogConfig(enabled=False, level="INFO", console=False, file=None))
        assert cfg._configured is False  # _configured only set to True after handlers added

    def test_disabled_console_and_file_no_error(self):
        """Configure with console=False and file=None works fine."""
        cfg = LoggerConfig()
        cfg.configure(LogConfig(enabled=True, level="WARNING", console=False, file=None))
        assert cfg._configured is True

    def test_global_logger_config_instance(self):
        assert logger_config is not None
        assert isinstance(logger_config, LoggerConfig)

    def test_file_handler_uses_data_dir(self, tmp_path):
        """File handler creates the log path under the data directory."""
        cfg = LoggerConfig()
        log_file = "sub/log.txt"
        expected_dir = tmp_path / "sub"
        with patch("nanobot.utils.logging.get_data_dir", return_value=tmp_path):
            cfg.configure(LogConfig(enabled=True, level="DEBUG", console=False, file=log_file))
        assert cfg._configured is True
        assert expected_dir.exists()
