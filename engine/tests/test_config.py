# SPDX-License-Identifier: MIT
"""Tests for config loading."""

import os
import tempfile
from pathlib import Path

from src.config import load_config, _deep_merge


def test_default_config():
    config = load_config(path="nonexistent.yaml")
    assert config["search"]["provider"] == "searxng"
    assert config["search"]["searxng_url"] == "http://127.0.0.1:8888"
    assert config["fetch"]["strategy"] == "hybrid"
    assert config["server"]["port"] == 8000


def test_config_override_via_env():
    os.environ["SEARXNG_URL"] = "http://localhost:9999"
    try:
        config = load_config(path="nonexistent.yaml")
        assert config["search"]["searxng_url"] == "http://localhost:9999"
    finally:
        del os.environ["SEARXNG_URL"]


def test_config_override_via_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("server:\n  port: 9999\n")
        tmp = f.name
    try:
        config = load_config(path=tmp)
        assert config["server"]["port"] == 9999
        assert config["search"]["provider"] == "searxng"  # default remains
    finally:
        os.unlink(tmp)


def test_deep_merge():
    base = {"a": 1, "b": {"c": 2, "d": 3}}
    override = {"b": {"c": 99}, "e": 4}
    _deep_merge(base, override)
    assert base["a"] == 1
    assert base["b"]["c"] == 99  # overridden
    assert base["b"]["d"] == 3   # kept
    assert base["e"] == 4        # added
