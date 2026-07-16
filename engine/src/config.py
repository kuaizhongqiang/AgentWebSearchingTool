# SPDX-License-Identifier: MIT
"""Configuration loader for the engine."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

DEFAULT_CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    """Load configuration from YAML file, with env var overrides."""
    config_path = Path(path) if path else DEFAULT_CONFIG_PATH

    config: dict[str, Any] = {
        "searxng_core": {
            "auto_start": True,
            "port": 8888,
            "bind_address": "127.0.0.1",
            "secret": "",
            "path": "",
            "settings_path": "",
            "proxies": {},
        },
        "search": {
            "provider": "searxng",
            "searxng_url": "http://127.0.0.1:8888",
            "default_engine": "google",
            "max_results": 20,
        },
        "fetch": {
            "strategy": "hybrid",
            "request_interval": 1.0,
            "max_concurrent": 5,
            "respect_robots_txt": True,
            "user_agent_rotation": True,
        },
        "extract": {
            "engine": "trafilatura",
            "max_content_length": 10000,
        },
        "retrieval": {
            "embedding": {
                "provider": "dashscope",
                "dashscope": {
                    "model": "text-embedding-v4",
                },
                "lmstudio": {
                    "base_url": "http://localhost:1234/v1",
                    "model": "",
                },
            },
            "cross_encoder": {
                "model": "",
            },
            "top_k_coarse": 20,
            "top_k": 5,
        },
        "server": {
            "host": "0.0.0.0",
            "port": 8000,
        },
    }

    if config_path.exists():
        with open(config_path, encoding="utf-8") as f:
            user_config = yaml.safe_load(f) or {}
            _deep_merge(config, user_config)

    # Environment variable overrides
    if os.environ.get("SEARXNG_URL"):
        config["search"]["searxng_url"] = os.environ["SEARXNG_URL"]
    if os.environ.get("ENGINE_PORT"):
        config["server"]["port"] = int(os.environ["ENGINE_PORT"])
    if os.environ.get("DASHSCOPE_API_KEY"):
        config["retrieval"]["embedding"]["dashscope"]["api_key"] = os.environ["DASHSCOPE_API_KEY"]
    # SearXNG env var overrides
    if os.environ.get("SEARXNG_SECRET"):
        config["searxng_core"]["secret"] = os.environ["SEARXNG_SECRET"]
    if os.environ.get("SEARXNG_PORT"):
        config["searxng_core"]["port"] = int(os.environ["SEARXNG_PORT"])
    if os.environ.get("SEARXNG_BIND_ADDRESS"):
        config["searxng_core"]["bind_address"] = os.environ["SEARXNG_BIND_ADDRESS"]
    if os.environ.get("SEARXNG_CORE_PATH"):
        config["searxng_core"]["path"] = os.environ["SEARXNG_CORE_PATH"]

    return config


def _deep_merge(base: dict, override: dict) -> None:
    """Deep merge override dict into base dict."""
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
