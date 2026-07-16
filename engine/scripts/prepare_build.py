#!/usr/bin/env python
"""Prepare engine package for build: copy searxng-core into src/searxng_core/.

This script is run before `python -m build` to bundle the searxng-core
submodule into the wheel. The bundled files are then included as package
data, so `pip install agent-web-search-engine` ships with SearXNG embedded.
"""

import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent  # AgentWebSearchingTool/
SEARXNG_CORE_SRC = REPO_ROOT / "searxng-core"
SEARXNG_CORE_DST = REPO_ROOT / "engine" / "src" / "searxng_core"

# Files/directories to exclude from the bundle (venv, git, caches)
EXCLUDE_PATTERNS = {
    ".venv",
    ".git",
    "__pycache__",
    "*.pyc",
    ".gitignore",
}

def should_exclude(name: str) -> bool:
    for pat in EXCLUDE_PATTERNS:
        if pat.startswith("*") and name.endswith(pat[1:]):
            return True
        if name == pat:
            return True
    return False


def main():
    if not SEARXNG_CORE_SRC.is_dir():
        print(f"ERROR: searxng-core not found at {SEARXNG_CORE_SRC}", file=sys.stderr)
        print("Did you run `git submodule update --init --recursive`?", file=sys.stderr)
        sys.exit(1)

    # Remove stale copy if any
    if SEARXNG_CORE_DST.is_dir() or SEARXNG_CORE_DST.is_symlink():
        shutil.rmtree(SEARXNG_CORE_DST)

    # Copy all files
    print(f"Copying {SEARXNG_CORE_SRC} → {SEARXNG_CORE_DST} ...")
    shutil.copytree(
        SEARXNG_CORE_SRC,
        SEARXNG_CORE_DST,
        ignore=lambda dir_, names: [n for n in names if should_exclude(n)],
        symlinks=False,
    )

    # Verify critical files exist
    critical = [
        SEARXNG_CORE_DST / "searx" / "webapp.py",
        SEARXNG_CORE_DST / "requirements.txt",
        SEARXNG_CORE_DST / "searx" / "settings.yml",
        SEARXNG_CORE_DST / "LICENSE",  # AGPL-3.0
    ]
    for f in critical:
        if not f.is_file():
            print(f"WARNING: critical file missing: {f}", file=sys.stderr)

    # Count copied files
    n_files = sum(1 for _ in SEARXNG_CORE_DST.rglob("*") if _.is_file())
    size = sum(_.stat().st_size for _ in SEARXNG_CORE_DST.rglob("*") if _.is_file())
    print(f"Done — {n_files} files ({size / 1024:.0f} KB) copied.")


if __name__ == "__main__":
    main()
