#!/usr/bin/env python3
"""Pre-commit guard against accidentally staging client/game content."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ALLOWED_PREFIXES = (
    "python/",
    "vendor/",
)

BLOCKED_DIRS = {
    "__installer",
    "core",
    "data",
    "support",
    "x64",
}

BLOCKED_EXTENSIONS = {
    ".big",
    ".bin",
    ".bundle",
    ".cas",
    ".chunk",
    ".dat",
    ".dll",
    ".exe",
    ".pak",
    ".rdata",
    ".res",
    ".sb",
    ".toc",
    ".ucas",
    ".utoc",
}

BLOCKED_NAMES = {
    "activation.dll",
    "activation64.dll",
    "chunkmanifest",
    "initfs_win32",
    "layout.toc",
}

MAX_NON_RUNTIME_BYTES = 20 * 1024 * 1024


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True)


def staged_paths() -> list[str]:
    output = git("diff", "--cached", "--name-only", "--diff-filter=ACMR")
    return [line.strip() for line in output.splitlines() if line.strip()]


def is_allowed_runtime(path: str) -> bool:
    lowered = path.replace("\\", "/").lower()
    return lowered.startswith(ALLOWED_PREFIXES)


def should_block(path: str, repo_root: Path) -> str | None:
    normalized = path.replace("\\", "/")
    lowered = normalized.lower()

    if is_allowed_runtime(lowered):
        return None

    parts = [part.lower() for part in normalized.split("/") if part]
    suffix = Path(lowered).suffix
    name = Path(lowered).name

    if any(part in BLOCKED_DIRS for part in parts):
        return "matches a client/game directory name"

    if suffix in BLOCKED_EXTENSIONS:
        return f"has blocked extension {suffix}"

    if name in BLOCKED_NAMES:
        return "matches a known client/game file name"

    full_path = repo_root / normalized
    if full_path.exists() and full_path.is_file():
        size = full_path.stat().st_size
        if size > MAX_NON_RUNTIME_BYTES:
            return f"is unusually large for source control ({size:,} bytes)"

    return None


def main() -> int:
    repo_root = Path(git("rev-parse", "--show-toplevel").strip())
    blocked: list[tuple[str, str]] = []

    for path in staged_paths():
        reason = should_block(path, repo_root)
        if reason:
            blocked.append((path, reason))

    if not blocked:
        return 0

    print("Commit blocked: staged files look like original client/game content.")
    print("Keep the vanilla install as a sibling of this repo, not inside Git.")
    print()
    for path, reason in blocked:
        print(f"  - {path}: {reason}")
    print()
    print("If this is a false positive, move the file outside the repo or adjust")
    print("scripts/check_no_game_content.py with a narrow allow-list.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
