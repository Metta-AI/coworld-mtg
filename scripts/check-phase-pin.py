#!/usr/bin/env python3
"""Verify that every Phase build surface uses the canonical source pin."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SOURCE = json.loads((ROOT / "phase-source.json").read_text())
REPOSITORY = SOURCE["repository"]
REVISION = SOURCE["revision"]


def require(path: str, pattern: str, expected: str) -> None:
    text = (ROOT / path).read_text()
    match = re.search(pattern, text, re.MULTILINE)
    actual = match.group(1) if match else None
    if actual != expected:
        raise ValueError(f"{path}: expected {expected!r}, found {actual!r}")


def require_all(path: str, pattern: str, expected: str) -> None:
    values = re.findall(pattern, (ROOT / path).read_text(), re.MULTILINE)
    if not values or set(values) != {expected}:
        raise ValueError(f"{path}: expected only {expected!r}, found {values!r}")


def main() -> None:
    if not re.fullmatch(r"[0-9a-f]{40}", REVISION):
        raise ValueError("phase-source.json revision must be a full lowercase Git SHA")
    if REPOSITORY not in {
        "https://github.com/nishu-builder/phase.git",
        "https://github.com/phase-rs/phase.git",
    }:
        raise ValueError(f"unsupported Phase repository: {REPOSITORY}")

    require(
        "crates/phase-bridge/Cargo.toml",
        r'phase-engine\s*=\s*\{[^\n]*git\s*=\s*"([^"]+)"',
        REPOSITORY,
    )
    require(
        "crates/phase-bridge/Cargo.toml",
        r'phase-engine\s*=\s*\{[^\n]*rev\s*=\s*"([0-9a-f]+)"',
        REVISION,
    )
    require(
        "crates/phase-bridge/src/lib.rs",
        r'pub const PHASE_REVISION: &str = "([0-9a-f]+)";',
        REVISION,
    )
    require("Dockerfile.coworld", r"^ARG PHASE_REVISION=([0-9a-f]+)$", REVISION)
    require_all(
        "Dockerfile.coworld",
        r"remote add origin (https://github\.com/[^\s]+/phase\.git)",
        REPOSITORY,
    )
    require(
        "scripts/build-phase-client.sh",
        r"remote add origin (https://github\.com/[^\s]+/phase\.git)",
        REPOSITORY,
    )
    require(
        "scripts/build-corpus-artifact.py",
        r'^PHASE_REVISION = "([0-9a-f]+)"$',
        REVISION,
    )
    print(f"Phase pin is consistent: {REPOSITORY}@{REVISION}")


if __name__ == "__main__":
    try:
        main()
    except (KeyError, ValueError) as error:
        print(f"Phase pin check failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error
