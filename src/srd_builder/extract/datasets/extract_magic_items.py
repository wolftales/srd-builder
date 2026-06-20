#!/usr/bin/env python3
"""PDF magic item extraction for SRD 5.1.

Bound to the `font_fingerprint_walk` engine pattern (line-mode). Schema
contributions tested by this binding (vs the simpler extract_features
binding): line-level header scope with first-span match, multi-line
header continuation, font-split span buckets (`metadata_blocks` vs
`description_blocks`), and the `merge_short_records` post-pass that
joins cross-page item fragments.

See docs/BACKLOG.md "Design-pass finding" for context.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

try:
    from ...constants import EXTRACTOR_VERSION
    from ..patterns import extract_records_by_config
except ImportError:
    # Running as script
    import sys

    sys.path.insert(0, str(Path(__file__).parents[2]))
    from srd_builder.constants import EXTRACTOR_VERSION
    from srd_builder.extract.patterns import extract_records_by_config

# Magic Items section pages (from PAGE_INDEX - see src/srd_builder/utils/page_index.py)
MAGIC_ITEMS_START_PAGE = 206
MAGIC_ITEMS_END_PAGE = 253

# Conservative quality floor; warn if drift falls below.
EXPECTED_ITEM_COUNT_MIN = 150

# CLI
MIN_CLI_ARGS = 2


DATASET_CONFIG: dict[str, Any] = {
    "pattern_type": "font_fingerprint_walk",
    "header_scope": "line",
    "header_match_mode": "first_span",
    "header_fingerprints": [
        {
            # 12pt GillSans-SemiBold item name. Match via font name substring
            # (the original code checked "GillSans-SemiBold" in font with no
            # flag inspection, so we mirror that rather than requiring the
            # bold bit).
            "font_substring": "GillSans-SemiBold",
            "size_min": 11.5,
            "size_max": 12.5,
            "min_text_len": 1,
        },
    ],
    # Item names sometimes wrap, e.g. "Ioun Stone" + " of Mastery" — defer
    # the record commit until a non-continuation line lands.
    "header_continuation_words": ["and", "or", "of", "the", "a", "an"],
    "body_grouping": "font_split_spans",
    "body_buckets": [
        {
            "name": "metadata_blocks",
            "match_any_span": {"font_substring": "Cambria-Italic"},
        },
        {"name": "description_blocks", "default": True},
    ],
    "post_pass": "merge_short_records",
    "merge_threshold": 20,
    "merge_check_bucket": "description_blocks",
    "merge_skip_if_bucket_nonempty": "metadata_blocks",
}


def extract_magic_items(pdf_path: Path) -> dict[str, Any]:
    """Extract magic items from SRD PDF.

    Args:
        pdf_path: Path to SRD PDF file

    Returns:
        Dictionary with:
            - items: list of raw magic item dicts
            - _meta: extraction metadata
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    pdf_bytes = pdf_path.read_bytes()
    pdf_hash = hashlib.sha256(pdf_bytes).hexdigest()

    pages = list(range(MAGIC_ITEMS_START_PAGE, MAGIC_ITEMS_END_PAGE + 1))
    items = extract_records_by_config(str(pdf_path), pages, DATASET_CONFIG)

    warnings: list[str] = []
    if len(items) < EXPECTED_ITEM_COUNT_MIN:
        warnings.append(
            f"Only extracted {len(items)} items, expected at least {EXPECTED_ITEM_COUNT_MIN}"
        )

    return {
        "items": items,
        "_meta": {
            "pdf_filename": pdf_path.name,
            "extractor_version": EXTRACTOR_VERSION,
            "pdf_sha256": pdf_hash,
            "pages_processed": MAGIC_ITEMS_END_PAGE - MAGIC_ITEMS_START_PAGE + 1,
            "item_count": len(items),
            "total_warnings": len(warnings),
            "extraction_warnings": warnings,
        },
    }


def main() -> None:
    """CLI entry point for testing extraction."""
    import sys

    if len(sys.argv) < MIN_CLI_ARGS:
        print(f"Usage: {sys.argv[0]} <pdf_path>")
        sys.exit(1)

    pdf_path = Path(sys.argv[1])
    result = extract_magic_items(pdf_path)

    print(f"Extracted {result['_meta']['item_count']} magic items")
    print(f"Warnings: {result['_meta']['total_warnings']}")

    for item in result["items"][:5]:
        print(f"\n{item['name']} (page {item['page']})")
        metadata_text = "".join(s.get("text", "") for s in item.get("metadata_blocks", []))
        if metadata_text:
            print(f"  Metadata: {metadata_text[:100]}")
        desc_text = "".join(s.get("text", "") for s in item.get("description_blocks", []))
        print(f"  Description: {desc_text[:200]}...")


if __name__ == "__main__":
    main()
