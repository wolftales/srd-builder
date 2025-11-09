"""Build conditions dataset from PDF extraction.

This module orchestrates the condition extraction and parsing pipeline,
transforming raw PDF text into structured JSON according to schema v1.0.0.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .extract_conditions import extract_conditions
from .parse_conditions import parse_condition_records


def build_conditions(pdf_path: Path | None = None) -> dict[str, Any]:
    """Build the conditions dataset from PDF extraction.

    Args:
        pdf_path: Path to SRD PDF (if None, uses default location)

    Returns:
        Complete conditions dataset with metadata
    """
    # Default PDF location
    if pdf_path is None:
        pdf_path = Path("rulesets/srd_5_1/raw/SRD_CC_v5.1.pdf")

    # Extract raw conditions from PDF
    raw_data = extract_conditions(pdf_path)
    raw_conditions = raw_data["conditions"]

    # Parse into structured records
    conditions_list = parse_condition_records(raw_conditions)

    # Sort by name
    conditions_list.sort(key=lambda c: c["name"])

    # Build complete document
    doc = {
        "_meta": {
            "schema_version": "1.0.0",
            "dataset": "conditions",
            "source": "SRD 5.1",
            "source_pages": "358-359",
            "description": "Standard game conditions from Appendix PH-A",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "pdf_sha256": raw_data["_meta"]["pdf_sha256"],
            "extractor_version": raw_data["_meta"]["extractor_version"],
            "condition_count": len(conditions_list),
            "conditions_with_levels": sum(1 for c in conditions_list if "levels" in c),
            "extraction_warnings": raw_data["_meta"]["total_warnings"],
            "notes": [
                "Conditions are special status effects that modify creature capabilities",
                "Most conditions are binary (present or absent)",
                "Exhaustion has 6 severity levels",
                "Multiple conditions can affect a creature simultaneously",
            ],
        },
        "conditions": conditions_list,
    }

    return doc


if __name__ == "__main__":
    import json
    from pathlib import Path

    # Build and save for testing
    doc = build_conditions()
    output_path = Path("dist/srd_5_1/conditions.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)

    print(f"✅ Built {len(doc['conditions'])} conditions")
    print(f"   Output: {output_path}")
