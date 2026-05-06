"""Registry for proxy channel modules — no BaseChannel inheritance required."""

from __future__ import annotations

import importlib
import pkgutil
from typing import Any

from loguru import logger

_INTERNAL = frozenset({"__init__"})


def discover_channel_names() -> list[str]:
    """Return all proxy channel module names by scanning the package."""
    import nanobot.proxy.channels as pkg

    return [
        name
        for _, name, ispkg in pkgutil.iter_modules(pkg.__path__)
        if name not in _INTERNAL and not ispkg
    ]


def get_channel_info(name: str) -> dict[str, Any] | None:
    """Load channel info dict from proxy channel module.

    Returns dict with keys:
      - display_name: str
      - config_cls: the *Config class (if found)
      - default_config: callable returning default config dict (if config_cls found)
    Returns None if the module can't be loaded.
    """
    try:
        mod = importlib.import_module(f"nanobot.proxy.channels.{name}")
    except Exception as e:
        logger.debug("Skipping channel '{}': {}", name, e)
        return None

    # Display name: from ProxyChannel class or fallback to name
    proxy_cls = getattr(mod, f"{name.title().replace('_', '')}ProxyChannel", None) or \
                getattr(mod, f"{name.capitalize()}ProxyChannel", None)
    display_name = getattr(proxy_cls, "display_name", name.capitalize()) if proxy_cls else name.capitalize()

    # Config class: named {Name}Config or {Name}ProxyConfig
    config_cls = getattr(mod, f"{name.title().replace('_', '')}Config", None) or \
                 getattr(mod, f"{name.capitalize()}Config", None)

    default_config = getattr(config_cls, "model_dump", None) if config_cls else None

    return {
        "display_name": display_name,
        "config_cls": config_cls,
        "default_config": default_config,
    }


def discover_all() -> dict[str, dict[str, Any]]:
    """Return all proxy channels as {name: info_dict}."""
    result = {}
    for name in discover_channel_names():
        info = get_channel_info(name)
        if info is not None:
            result[name] = info
    return result
