# SPDX-License-Identifier: MIT
"""SearXNG subprocess manager — starts/stops a local SearXNG-core instance.

The SearXNG-core source is bundled inside the wheel at ``src/searxng_core/``.
At runtime this module locates that directory, spawns a Python subprocess
running ``python -m searx.webapp``, monitors its health, and shuts it down
on engine exit.
"""

from __future__ import annotations

import logging
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import IO

import httpx

logger = logging.getLogger(__name__)

DEFAULT_PORT = 8888
DEFAULT_BIND_ADDRESS = "127.0.0.1"
DEFAULT_STARTUP_TIMEOUT = 120.0  # seconds to wait for SearXNG to respond
HEALTH_CHECK_INTERVAL = 0.5
POLL_TIMEOUT = 5.0


def _find_searxng_core_path(custom_path: str | None = None) -> Path | None:
    """Locate the searxng-core directory.

    Resolution order:
    1. Custom path from config (if provided)
    2. Bundled path (``src/searxng_core/`` inside the installed package)
    3. Development path (``../searxng-core/`` relative to this file)
    """
    # 1. User-configured path
    if custom_path:
        p = Path(custom_path).resolve()
        if (p / "searx" / "webapp.py").is_file():
            return p
        logger.warning("configured searxng_core_path=%s not valid — falling back", custom_path)

    # 2. Bundled in package
    try:
        import importlib.resources as ir
        # The `src` package contains searxng_core/ as data
        bundled = ir.files("src").joinpath("searxng_core")
        if bundled.is_dir() and (bundled / "searx" / "webapp.py").is_file():
            return bundled
    except (ImportError, ModuleNotFoundError, TypeError):
        pass

    # 3. Development path (git submodule)
    dev_path = Path(__file__).resolve().parent.parent / "searxng_core"
    if dev_path.is_dir() and (dev_path / "searx" / "webapp.py").is_file():
        return dev_path
    # Also check the sibling directory (monorepo root)
    dev_path2 = Path(__file__).resolve().parent.parent.parent / "searxng-core"
    if dev_path2.is_dir() and (dev_path2 / "searx" / "webapp.py").is_file():
        return dev_path2

    return None


class SearXNGManager:
    """Manages a local SearXNG subprocess instance."""

    def __init__(
        self,
        port: int = DEFAULT_PORT,
        bind_address: str = DEFAULT_BIND_ADDRESS,
        searxng_secret: str | None = None,
        settings_path: str | Path | None = None,
        core_path: str | Path | None = None,
        proxies: dict[str, str | list[str]] | None = None,
        startup_timeout: float = DEFAULT_STARTUP_TIMEOUT,
    ):
        self.port = port
        self.bind_address = bind_address
        self.searxng_secret = searxng_secret or os.environ.get("SEARXNG_SECRET", "dev-secret-key")
        self.settings_path = Path(settings_path) if settings_path else None
        self._core_path = _find_searxng_core_path(str(core_path) if core_path else None)
        self._proxies = proxies
        self.startup_timeout = startup_timeout

        self._process: subprocess.Popen | None = None
        self._stderr_buf: IO | None = None

    @property
    def searxng_url(self) -> str:
        return f"http://{self.bind_address}:{self.port}"

    @property
    def is_ready(self) -> bool:
        """Check if SearXNG health endpoint responds."""
        if not self._process or self._process.poll() is not None:
            return False
        try:
            r = httpx.get(f"{self.searxng_url}/search?q=healthcheck&format=json", timeout=POLL_TIMEOUT)
            return r.status_code < 500  # 4xx means it's alive, 5xx means issue
        except (httpx.ConnectError, httpx.TimeoutException, httpx.RemoteProtocolError):
            return False

    def start(self) -> None:
        """Launch SearXNG as a subprocess — returns quickly, does not block lifespan.

        The subprocess continues initializing in the background after this method
        returns.  Use :meth:`is_ready` to check readiness lazily.
        """
        if self._process is not None:
            logger.warning("SearXNG is already running (pid=%s)", self._process.pid)
            return

        if self._core_path is None:
            logger.error(
                "SearXNG-core not found. Ensure searxng-core is bundled or "
                "available at a configured path."
            )
            raise RuntimeError(
                "SearXNG-core not found. Install with `git submodule update --init --recursive` "
                "or set searxng_core_path in config."
            )

        core_path = self._core_path
        searx_pkg = core_path / "searx"
        if not (searx_pkg / "webapp.py").is_file():
            raise RuntimeError(f"Invalid searxng-core path: {core_path} (searx/webapp.py not found)")

        logger.info("Starting SearXNG from %s on %s:%s", core_path, self.bind_address, self.port)

        # Build environment
        env = os.environ.copy()
        env["SEARXNG_SECRET"] = self.searxng_secret
        env["PYTHONPATH"] = str(core_path) + os.pathsep + env.get("PYTHONPATH", "")
        # Point settings to our config
        env.setdefault("SEARXNG_SETTINGS_PATH", str(core_path / "searx" / "settings.yml"))

        # Override settings via env vars for binding
        env["SEARXNG_BIND_ADDRESS"] = self.bind_address
        env["SEARXNG_PORT"] = str(self.port)

        cmd = [sys.executable, "-m", "searx.webapp"]

        self._process = subprocess.Popen(
            cmd,
            cwd=str(core_path),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        logger.info("SearXNG subprocess started (pid=%s)", self._process.pid)

        # Quick check: did the process die immediately (e.g. missing dependency)?
        # Only wait 5s for this initial health — don't block the engine startup.
        quick_deadline = time.monotonic() + 5.0
        while time.monotonic() < quick_deadline:
            if self._process.poll() is not None:
                stdout, stderr = self._process.communicate(timeout=5)
                logger.error(
                    "SearXNG process exited prematurely (rc=%s)\nstdout:\n%s\nstderr:\n%s",
                    self._process.returncode,
                    stdout.decode(errors="replace")[:2000],
                    stderr.decode(errors="replace")[:2000],
                )
                self._process = None
                raise RuntimeError(
                    f"SearXNG exited with code {self._process.returncode}. "
                    "Check the logs above for details."
                )
            if self.is_ready:
                logger.info("SearXNG is ready at %s", self.searxng_url)
                return
            time.sleep(HEALTH_CHECK_INTERVAL)

        # Process is alive — return immediately.  It will finish initialising in the
        # background and is_ready will return True once it's fully up.
        logger.info(
            "SearXNG starting in background (pid=%s) — engine will check readiness lazily",
            self._process.pid,
        )

    def _log_stderr(self) -> None:
        """Log any accumulated stderr output."""
        if self._process and self._process.stderr:
            try:
                output = self._process.stderr.read1(4096).decode(errors="replace")
                if output:
                    logger.warning("SearXNG stderr: %s", output.strip())
            except Exception:
                pass

    def stop(self) -> None:
        """Gracefully shut down SearXNG subprocess."""
        if self._process is None:
            return

        pid = self._process.pid
        logger.info("Shutting down SearXNG (pid=%s)...", pid)

        try:
            if sys.platform == "win32":
                self._process.terminate()
            else:
                self._process.send_signal(signal.SIGTERM)

            try:
                self._process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                logger.warning("SearXNG did not exit in 10s — killing")
                self._process.kill()
                self._process.wait(timeout=5)
        except Exception as e:
            logger.warning("Error stopping SearXNG: %s", e)

        self._process = None
        logger.info("SearXNG stopped")

    def __del__(self):
        if self._process is not None:
            self.stop()
