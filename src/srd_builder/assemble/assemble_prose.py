"""Generic prose dataset assembly using configuration-driven approach.

Instead of build_conditions.py, build_diseases.py, etc., this single module
assembles all prose datasets using metadata from extraction/extraction_metadata.py.

Prose datasets are configured as pattern_type='prose_section' entries in the
unified TABLES dictionary.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

from .. import __version__
from ..extract.prose_extraction import ProseExtractor
from ..extraction.extraction_metadata import TABLES


def assemble_prose_dataset(
    dataset_name: str,
    pdf_path: Path,
    parser_func: Callable[[list], list[dict[str, Any]]],
) -> dict[str, Any]:
    """Assemble any prose dataset using configuration.

    Args:
        dataset_name: Name from extraction_metadata TABLES (e.g., "conditions", "diseases")
        pdf_path: Path to SRD PDF
        parser_func: Function to parse raw sections into structured records
                     Signature: (list[dict]) -> list[dict]

    Returns:
        Complete dataset document with metadata

    Raises:
        FileNotFoundError: If PDF not found
        KeyError: If dataset_name not in TABLES or config missing required keys
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    # Get configuration from unified metadata
    if dataset_name not in TABLES:
        raise KeyError(f"Dataset '{dataset_name}' not found in TABLES")

    config = TABLES[dataset_name]

    # Validate it's a prose dataset
    if config.get("pattern_type") != "prose_section":
        raise ValueError(
            f"Dataset '{dataset_name}' has pattern_type '{config.get('pattern_type')}', "
            "expected 'prose_section'"
        )

    # Extract raw sections using existing ProseExtractor
    raw_data = _extract_raw_sections(pdf_path, config)

    # Parse into structured records using provided parser
    parsed_records = parser_func(raw_data["sections"])

    # Sort by name
    parsed_records.sort(key=lambda r: r.get("name", ""))

    # Build complete document
    pages = config["pages"]
    start_page = pages[0]
    end_page = pages[-1]
    output_key = config["output_key"]

    # Standard _meta fields (ordered)
    doc = {
        "_meta": {
            "source": "SRD 5.1",
            "ruleset_version": "5.1",
            "schema_version": config["schema_version"],
            "generated_by": f"srd-builder v{__version__}",
            "build_report": "./build_report.json",
            # Dataset-specific metadata
            "dataset": dataset_name,
            "source_pages": f"{start_page}-{end_page}",
            "description": config["description"],
            "pdf_sha256": raw_data["_meta"]["pdf_sha256"],
            # Note: No timestamps per AGENTS.md determinism requirement
            f"{output_key}_count": len(parsed_records),
            "extraction_warnings": raw_data["_meta"]["warnings"],
        },
        output_key: parsed_records,
    }

    return doc


def _extract_raw_sections(pdf_path: Path, config: dict[str, Any]) -> dict[str, Any]:
    """Extract raw sections from PDF using configuration.

    Args:
        pdf_path: Path to PDF
        config: Dataset configuration

    Returns:
        Dict with sections list and metadata
    """
    # Calculate PDF hash
    pdf_bytes = pdf_path.read_bytes()
    pdf_hash = hashlib.sha256(pdf_bytes).hexdigest()

    # Use existing ProseExtractor
    # pages is a list [start, end] in extraction_metadata format
    pages = config["pages"]
    start_page = pages[0]
    end_page = pages[-1]

    extractor = ProseExtractor(
        section_name=config["entity_type"],
        known_headers=config.get("known_headers", []),
        start_page=start_page,
        end_page=end_page,
    )

    # Extract sections (already returns list of dicts)
    sections, warnings = extractor.extract_from_pdf(pdf_path)

    return {
        "sections": sections,
        "_meta": {
            "pdf_sha256": pdf_hash,
            "warnings": warnings,
        },
    }
