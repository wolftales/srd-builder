"""Smoke test: every shipped schema validates its own generated exemplar.

Pure round-trip — runs `scripts/generate_exemplars.py --check` which
generates an instance for each schema in-memory and validates it. Fails
loudly if a schema acquires a constraint the generator does not yet know
how to satisfy (forcing us to update the generator) or if a schema
becomes internally inconsistent.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_all_schemas_have_a_valid_exemplar() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/generate_exemplars.py", "--check"],
        check=False,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"generate_exemplars.py --check failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
