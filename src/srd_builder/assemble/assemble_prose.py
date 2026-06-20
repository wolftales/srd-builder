"""Generic prose dataset extraction using configuration-driven approach.

Instead of build_conditions.py, build_diseases.py, etc., this single module
extracts and parses all prose datasets using metadata from
extraction/extraction_metadata.py.

Prose datasets are configured as pattern_type='prose_section' entries in the
unified TABLES dictionary.

v0.30.0 phase 4: this module now returns `(records, warnings)` only.
Wrapping records in the `_meta` envelope is the sole responsibility of
`build._write_datasets`, so conditions/diseases flow through the same
write path as every other dataset.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

from ..extract.extraction_metadata import TABLES
from ..postprocess.engine import clean_records
from ..utils.prose import ProseExtractor


def extract_prose_records(
    dataset_name: str,
    pdf_path: Path,
    parser_func: Callable[[list, str], list[dict[str, Any]]],
    ruleset: str,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Extract and parse a prose dataset from the PDF.

    Args:
        dataset_name: Name from extraction_metadata TABLES (e.g., "conditions", "diseases")
        pdf_path: Path to SRD PDF
        parser_func: Function to parse raw sections into structured records.
                     Signature: (list[dict], ruleset) -> list[dict]
        ruleset: Ruleset identifier for source_id stamping and metadata.

    Returns:
        Tuple of (parsed records sorted by name, extraction warnings).

    Raises:
        FileNotFoundError: If PDF not found
        KeyError: If dataset_name not in TABLES or config missing required keys
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    if dataset_name not in TABLES:
        raise KeyError(f"Dataset '{dataset_name}' not found in TABLES")

    config = TABLES[dataset_name]

    if config.get("pattern_type") != "prose_section":
        raise ValueError(
            f"Dataset '{dataset_name}' has pattern_type '{config.get('pattern_type')}', "
            "expected 'prose_section'"
        )

    raw_data = _extract_raw_sections(pdf_path, config)

    parsed_records = parser_func(raw_data["sections"], ruleset)

    # Postprocess: normalize IDs and polish text via config-driven engine.
    if dataset_name in {"conditions", "diseases"}:
        # Dataset name is plural; engine config key is singular.
        config_key = dataset_name[:-1]
        parsed_records = clean_records(parsed_records, config_key)

    parsed_records.sort(key=lambda r: r.get("name", ""))

    return parsed_records, raw_data["warnings"]


def _extract_raw_sections(pdf_path: Path, config: dict[str, Any]) -> dict[str, Any]:
    """Extract raw sections from PDF using configuration.

    Args:
        pdf_path: Path to PDF
        config: Dataset configuration

    Returns:
        Dict with sections list and extraction warnings.
    """
    pages = config["pages"]
    start_page = pages[0]
    end_page = pages[-1]

    extractor = ProseExtractor(
        section_name=config["entity_type"],
        known_headers=config.get("known_headers", []),
        start_page=start_page,
        end_page=end_page,
        start_marker=config.get("start_marker"),
    )

    sections, warnings = extractor.extract_from_pdf(pdf_path)

    return {
        "sections": sections,
        "warnings": warnings,
    }
