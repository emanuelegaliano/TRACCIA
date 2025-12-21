# tests/run_all.py
from __future__ import annotations

import sys
from pathlib import Path

import pytest


def main() -> int:
    tests_dir = Path(__file__).resolve().parent  # .../tests
    repo_root = tests_dir.parent                 # project root

    # Ensure project root is on sys.path so "import traccia" works
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    args = [
        str(tests_dir),
        "-rA",
        "--strict-markers",
    ]

    return pytest.main(args)


if __name__ == "__main__":
    raise SystemExit(main())
