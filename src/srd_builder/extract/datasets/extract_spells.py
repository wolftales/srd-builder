#!/usr/bin/env python3
"""PDF spell extraction for SRD 5.1.

Bound to the `font_stateful_walk` engine pattern. Spells are the
schema-generalization test for that pattern type: a record with both
flat sub-fields (`level_and_school`) and bucketed span lists
(`header_blocks` / `description_blocks`), where the bucket selection
depends on an intra-record state machine driven by the text
`"Duration:"` appearing in the header.

See docs/BACKLOG.md "Remaining shapes" for context.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

try:
    from ...constants import EXTRACTOR_VERSION
    from ..patterns import extract_records_by_config
except ImportError:
    import sys

    sys.path.insert(0, str(Path(__file__).parents[2]))
    from srd_builder.constants import EXTRACTOR_VERSION
    from srd_builder.extract.patterns import extract_records_by_config

# Spell section pages (descriptions, not spell lists)
SPELL_START_PAGE = 114
SPELL_END_PAGE = 194

EXPECTED_SPELL_COUNT_MIN = 300
MIN_CLI_ARGS = 2


DATASET_CONFIG: dict[str, Any] = {
    "pattern_type": "font_stateful_walk",
    "header_fingerprint": {
        "font_substring": "GillSans-SemiBold",
        "size_min": 11.5,
        "size_max": 12.5,
        "min_text_len": 1,
    },
    "subfields": ["level_and_school"],
    "buckets": ["header_blocks", "description_blocks"],
    "initial_state": "header",
    "span_rules": [
        # First Cambria-Italic after the name captures the level/school line.
        # Subsequent Cambria-Italic spans fall through to the default rule.
        {
            "match": {"font_substring": "Cambria-Italic"},
            "guard": {"subfield_empty": "level_and_school"},
            "action": {
                "type": "set_subfield",
                "name": "level_and_school",
                "also_append_to": "header_blocks",
                "attach": {"is_italic": True},
            },
        },
        # Cambria-BoldItalic — "At Higher Levels." marker. MUST precede the
        # Cambria-Bold rule because "Cambria-Bold" is a substring of
        # "Cambria-BoldItalic".
        {
            "match": {"font_substring": "Cambria-BoldItalic"},
            "guard": {"require_current_record": True},
            "action": {
                "type": "append_to_bucket",
                "bucket": "description_blocks",
                "attach": {
                    "section": "higher_levels",
                    "is_bold": "$bold_from_font",
                    "is_italic": "$italic_from_font",
                },
            },
        },
        # Cambria-Bold — field labels ("Casting Time:", "Range:", etc).
        # Route to whichever bucket matches the current state.
        {
            "match": {"font_substring": "Cambria-Bold"},
            "if_no_record": "create_nameless",
            "action": {
                "type": "append_to_state_bucket",
                "state_buckets": {
                    "header": "header_blocks",
                    "description": "description_blocks",
                },
                "attach": {
                    "is_bold": True,
                    "is_field_label": True,
                },
            },
        },
        # Default — any remaining span. Computed bold/italic flags.
        # This is the only rule that checks state transitions after its append:
        # the original code wires the "Duration:" trigger inline in its regular-
        # text branch only, not its field-label branch.
        {
            "match": {},
            "if_no_record": "create_nameless",
            "action": {
                "type": "append_to_state_bucket",
                "state_buckets": {
                    "header": "header_blocks",
                    "description": "description_blocks",
                },
                "attach": {
                    "is_bold": "$bold_from_font",
                    "is_italic": "$italic_from_font",
                },
            },
            "check_state_transitions_after": True,
        },
    ],
    "state_transitions": [
        {
            "when_state": "header",
            "trigger": {
                "bucket_text_contains": {
                    "bucket": "header_blocks",
                    "text": "Duration:",
                },
            },
            "to_state": "description",
        },
    ],
    # End-of-page carry: keep a header-only record alive into the next page
    # rather than committing it incomplete.
    "carry_if": {
        "name_nonempty": True,
        "bucket_empty": "description_blocks",
    },
    "post_pass": "merge_nameless_into_previous",
    "keep_if": {"name_nonempty": True},
    "track_pages_list": True,
}


def extract_spells(pdf_path: Path) -> dict[str, Any]:
    """Extract spells from SRD PDF.

    Args:
        pdf_path: Path to SRD PDF file

    Returns:
        Dictionary with:
            - spells: list of raw spell dicts
            - _meta: extraction metadata
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    pdf_bytes = pdf_path.read_bytes()
    pdf_hash = hashlib.sha256(pdf_bytes).hexdigest()

    pages = list(range(SPELL_START_PAGE, SPELL_END_PAGE + 1))
    spells = extract_records_by_config(str(pdf_path), pages, DATASET_CONFIG)

    warnings: list[str] = []
    if len(spells) < EXPECTED_SPELL_COUNT_MIN:
        warnings.append(
            f"Only extracted {len(spells)} spells, expected at least {EXPECTED_SPELL_COUNT_MIN}"
        )

    return {
        "spells": spells,
        "_meta": {
            "pdf_filename": pdf_path.name,
            "extractor_version": EXTRACTOR_VERSION,
            "pdf_sha256": pdf_hash,
            "pages_processed": SPELL_END_PAGE - SPELL_START_PAGE + 1,
            "spell_count": len(spells),
            "total_warnings": len(warnings),
            "extraction_warnings": warnings,
        },
    }


def main() -> None:  # pragma: no cover
    """CLI entry point for spell extraction."""
    import sys

    if len(sys.argv) != MIN_CLI_ARGS:
        print(f"Usage: {sys.argv[0]} <pdf_path>")
        sys.exit(1)

    pdf_path = Path(sys.argv[1])
    if not pdf_path.exists():
        print(f"Error: PDF not found: {pdf_path}")
        sys.exit(1)

    result = extract_spells(pdf_path)

    print(f"Extracted {result['_meta']['spell_count']} spells")
    print(f"Warnings: {result['_meta']['total_warnings']}")

    for spell in result["spells"][:3]:
        print(f"\n{spell['name']}")
        print(f"  {spell['level_and_school']}")
        header_text = " ".join(b["text"] for b in spell.get("header_blocks", []))
        desc_text = " ".join(b["text"] for b in spell.get("description_blocks", []))
        print(f"  Header blocks: {len(spell.get('header_blocks', []))}")
        print(f"  Header: {header_text[:80]}...")
        print(f"  Desc blocks: {len(spell.get('description_blocks', []))}")
        print(f"  Desc: {desc_text[:80]}...")


if __name__ == "__main__":  # pragma: no cover
    main()
