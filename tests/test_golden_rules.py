from __future__ import annotations

import json
from pathlib import Path

from srd_builder.postprocess import clean_rule_record
from srd_builder.utils.metadata import meta_block, read_schema_version


def test_rule_dataset_matches_normalized_fixture() -> None:
    raw_path = Path("tests/fixtures/srd_5_1/raw/rules.json")
    expected_path = Path("tests/fixtures/srd_5_1/normalized/rules.json")

    rules_raw = json.loads(raw_path.read_text(encoding="utf-8"))

    # Raw fixture contains pre-parsed rules (output of parse_rules)
    parsed = rules_raw["parsed_rules"]

    # Apply postprocessing
    processed = [clean_rule_record(rule) for rule in parsed]

    document = {"_meta": meta_block("srd_5_1", read_schema_version("rule")), "items": processed}

    rendered = json.dumps(document, indent=2, ensure_ascii=False) + "\n"
    expected = expected_path.read_text(encoding="utf-8")
    assert rendered == expected
