"""Utilities for building metadata documents (meta.json and _meta blocks)."""

from __future__ import annotations

from collections import OrderedDict
from typing import Any

from . import __version__
from .constants import DATA_SOURCE, SCHEMA_VERSION
from .page_index import PAGE_INDEX

__all__ = ["meta_block", "wrap_with_meta", "build_page_index", "generate_meta_json"]


def meta_block(ruleset: str, ruleset_version: str = "5.1") -> dict[str, str]:
    """Generate standardized _meta block with consistent field order."""

    return {
        "source": DATA_SOURCE,
        "ruleset_version": ruleset_version,
        "schema_version": SCHEMA_VERSION,
        "generated_by": f"srd-builder v{__version__}",
        "build_report": "./build_report.json",
    }


def wrap_with_meta(
    payload: dict[str, Any], *, ruleset: str, ruleset_version: str = "5.1"
) -> dict[str, Any]:
    document: OrderedDict[str, Any] = OrderedDict()
    document["_meta"] = meta_block(ruleset, ruleset_version)
    for key, value in payload.items():
        document[key] = value
    return document


def build_page_index(
    *,
    monsters_page_range: tuple[int, int] | None,
    equipment_page_range: tuple[int, int] | None,
    spells_page_range: tuple[int, int] | None,
    table_page_index: dict[str, Any] | None,
) -> dict[str, Any]:
    """Build page_index section for meta.json."""

    page_index: dict[str, dict[str, int | str]] = {}

    for section_name, section in PAGE_INDEX.items():
        section_data: dict[str, int | str] = {
            "start": section["pages"]["start"],
            "end": section["pages"]["end"],
            "description": section["description"],
        }
        dataset = section.get("dataset")
        if dataset is not None:
            section_data["dataset"] = dataset
        page_index[section_name] = section_data

    if table_page_index and "reference_tables" in table_page_index:
        page_index["reference_tables"] = table_page_index["reference_tables"]

    return page_index


def generate_meta_json(  # noqa: PLR0913
    *,
    pdf_hash: str | None,
    pdf_metadata: dict[str, Any] | None = None,
    monsters_complete: bool,
    monsters_page_range: tuple[int, int] | None = None,
    equipment_complete: bool = False,
    equipment_page_range: tuple[int, int] | None = None,
    spells_complete: bool = False,
    spells_page_range: tuple[int, int] | None = None,
    table_page_index: dict[str, Any] | None = None,
    classes_complete: bool = False,
    build_timestamp: str | None = None,
) -> dict[str, Any]:
    """Generate rich metadata for dist/meta.json with provenance."""

    version = pdf_metadata.get("version", "5.1") if pdf_metadata else "5.1"
    license_type = pdf_metadata.get("license_type", "CC-BY-4.0") if pdf_metadata else "CC-BY-4.0"
    license_url = (
        pdf_metadata.get("license_url", "https://creativecommons.org/licenses/by/4.0/legalcode")
        if pdf_metadata
        else "https://creativecommons.org/licenses/by/4.0/legalcode"
    )
    attribution = (
        pdf_metadata.get(
            "attribution",
            (
                "This work includes material taken from the System Reference Document 5.1 "
                '("SRD 5.1") by Wizards of the Coast LLC and available at '
                "https://dnd.wizards.com/resources/systems-reference-document. "
                "The SRD 5.1 is licensed under the Creative Commons Attribution 4.0 "
                "International License available at https://creativecommons.org/licenses/by/4.0/legalcode."
            ),
        )
        if pdf_metadata
        else (
            "This work includes material taken from the System Reference Document 5.1 "
            '("SRD 5.1") by Wizards of the Coast LLC and available at '
            "https://dnd.wizards.com/resources/systems-reference-document. "
            "The SRD 5.1 is licensed under the Creative Commons Attribution 4.0 "
            "International License available at https://creativecommons.org/licenses/by/4.0/legalcode."
        )
    )

    build_info: dict[str, str | None] = {
        "builder_version": __version__,
        "pdf_hash": f"sha256:{pdf_hash}" if pdf_hash else None,
    }
    if build_timestamp is not None:
        build_info["extracted_at"] = build_timestamp

    return {
        "source": DATA_SOURCE,
        "ruleset_version": version,
        "license": {
            "type": license_type,
            "url": license_url,
            "attribution": attribution,
            "conversion_note": (
                "Converted from the original PDF by srd-builder "
                f"(https://github.com/wolftales/srd-builder) version {__version__}"
            ),
        },
        "build": build_info,
        "page_index": build_page_index(
            monsters_page_range=monsters_page_range,
            equipment_page_range=equipment_page_range,
            spells_page_range=spells_page_range,
            table_page_index=table_page_index,
        ),
        "files": {
            "meta": "meta.json",
            "build_report": "build_report.json",
            "index": "index.json",
            "monsters": "monsters.json",
            "equipment": "equipment.json",
            "spells": "spells.json",
            "tables": "tables.json",
            "lineages": "lineages.json",
            "classes": "classes.json",
            "conditions": "conditions.json",
            "diseases": "diseases.json",
            "madness": "madness.json",
            "poisons": "poisons.json",
            "features": "features.json",
        },
        "terminology": {"aliases": {"race": "lineage", "races": "lineages"}},
        "extraction_status": {
            "monsters": "complete" if monsters_complete else "in_progress",
            "equipment": "complete" if equipment_complete else "in_progress",
            "spells": "complete" if spells_complete else "in_progress",
            "tables": "complete",
            "lineages": "complete",
            "classes": "complete" if classes_complete else "in_progress",
            "conditions": "complete",
            "diseases": "complete",
            "madness": "complete",
            "poisons": "complete",
            "features": "complete",
        },
    }
