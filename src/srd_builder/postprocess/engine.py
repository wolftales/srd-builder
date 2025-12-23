"""
Configuration-driven record normalization engine.

This module provides a generic engine for normalizing dataset records
using declarative configuration instead of imperative per-dataset functions.

Usage:
    from srd_builder.postprocess.engine import clean_record
    from srd_builder.postprocess.configs import DATASET_CONFIGS

    processed = clean_record(raw_record, DATASET_CONFIGS["monster"])
"""

from __future__ import annotations

from typing import Any

from .configs import RecordConfig
from .ids import normalize_id
from .text import polish_text


def clean_record(
    record: dict[str, Any],
    config: RecordConfig,
) -> dict[str, Any]:
    """
    Normalize a record using configuration-driven approach.

    Steps:
    1. Generate simple_name if missing (from name_field)
    2. Generate id if missing (using id_prefix)
    3. Polish text fields
    4. Polish text arrays (lists of strings)
    5. Polish nested structures (lists of dicts with text fields)
    6. Apply custom transformation if provided

    Args:
        record: Raw record to normalize
        config: Configuration specifying how to normalize

    Returns:
        Normalized record (mutates in place, also returns for chaining)
    """
    # 1. Ensure simple_name
    if "simple_name" not in record:
        if config.name_field in record:
            record["simple_name"] = normalize_id(record[config.name_field])

    # 2. Ensure id
    if "id" not in record:
        if "simple_name" in record:
            record["id"] = f"{config.id_prefix}:{record['simple_name']}"

    # 3. Polish top-level text fields
    for field in config.text_fields:
        if field in record and isinstance(record[field], str):
            record[field] = polish_text(record[field])

    # 4. Polish text arrays (lists of strings)
    for field in config.text_arrays:
        if field in record and isinstance(record[field], list):
            record[field] = [
                polish_text(item) if isinstance(item, str) else item for item in record[field]
            ]

    # 5. Polish nested structures (lists of dicts)
    for field, subfields in config.nested_structures.items():
        if field in record and isinstance(record[field], list):
            for item in record[field]:
                if isinstance(item, dict):
                    for subfield in subfields:
                        if subfield in item and isinstance(item[subfield], str):
                            item[subfield] = polish_text(item[subfield])

    # 6. Apply custom transformation (escape hatch)
    if config.custom_transform:
        record = config.custom_transform(record)

    return record


def clean_records(
    records: list[dict[str, Any]],
    dataset_name: str,
) -> list[dict[str, Any]]:
    """
    Batch process records using dataset-specific configuration.

    Args:
        records: List of raw records
        dataset_name: Key in DATASET_CONFIGS

    Returns:
        List of normalized records
    """
    from .configs import DATASET_CONFIGS

    if dataset_name not in DATASET_CONFIGS:
        raise ValueError(
            f"Unknown dataset: {dataset_name}. Available: {list(DATASET_CONFIGS.keys())}"
        )

    config = DATASET_CONFIGS[dataset_name]
    return [clean_record(r, config) for r in records]
