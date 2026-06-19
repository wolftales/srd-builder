"""Schema round-trip smoke test.

Re-runs ``scripts/generate_exemplars.py --check`` so any schema change
that drifts from the committed exemplar in ``schemas/exemplars/`` fails
CI immediately rather than waiting for a human to regenerate by hand.

The script's ``main()`` is invoked in-process via its ``--check`` flag
(no subprocess needed); it returns 0 on success and non-zero on any
validation failure.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import generate_exemplars  # noqa: E402


def test_all_exemplars_validate_against_their_schemas() -> None:
    assert generate_exemplars.main(["--check"]) == 0


def test_every_schema_has_a_committed_exemplar() -> None:
    schemas = {
        p.name.replace(".schema.json", "")
        for p in generate_exemplars.SCHEMAS_DIR.glob("*.schema.json")
    }
    exemplars = {
        p.name.replace(".exemplar.json", "")
        for p in generate_exemplars.EXEMPLARS_DIR.glob("*.exemplar.json")
    }
    missing = schemas - exemplars
    assert not missing, (
        f"Schemas without a committed exemplar: {sorted(missing)}. "
        "Run `python scripts/generate_exemplars.py` to regenerate."
    )
