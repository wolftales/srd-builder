"""Schema validation tests for spell dataset."""

from __future__ import annotations

import json
from itertools import islice
from pathlib import Path

import pytest

try:
    from jsonschema import Draft202012Validator
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    Draft202012Validator = None

SPELL_DATA = Path("dist/srd_5_1/spells.json")
SCHEMA_PATH = Path("schemas/spell.schema.json")
SAMPLE_SIZE = 5


@pytest.mark.package
@pytest.mark.skipif(Draft202012Validator is None, reason="jsonschema not installed")
@pytest.mark.skipif(not SPELL_DATA.exists(), reason="No SRD spell data present")
def test_spells_validate_against_schema() -> None:
    """Validate that spell dataset conforms to spell.schema.json.

    This test loads the built spell dataset and validates a sample
    against the JSON Schema to ensure structural correctness.
    """
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    document = json.loads(SPELL_DATA.read_text(encoding="utf-8"))
    spells = document.get("items", []) if isinstance(document, dict) else []

    validator = Draft202012Validator(schema)

    for spell in islice(spells, SAMPLE_SIZE):
        validator.validate(spell)
