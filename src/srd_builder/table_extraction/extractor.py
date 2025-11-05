"""Table extraction orchestrator using unified pattern engine.

This module provides the TableExtractor class that coordinates table extraction
using PyMuPDF auto-detection and reference data configuration.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF

from .patterns import RawTable, extract_by_config
from .reference_data import get_table_data

try:
    from scripts.table_targets import TARGET_TABLES, TableTarget
except ModuleNotFoundError:
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    from scripts.table_targets import TARGET_TABLES, TableTarget

logger = logging.getLogger(__name__)

# Extraction constants
MIN_TABLE_ROWS = 2  # Minimum rows required (header + at least one data row)


class TableExtractor:
    """Extract reference tables from SRD PDF using hybrid approach."""

    def __init__(self, pdf_path: str | Path):
        """Initialize extractor.

        Args:
            pdf_path: Path to SRD PDF file
        """
        self.pdf_path = Path(pdf_path)
        self.doc = fitz.open(self.pdf_path)
        logger.info(f"Opened PDF: {self.pdf_path} ({len(self.doc)} pages)")

    def extract_all_tables(self, skip_failures: bool = False) -> list[RawTable]:
        """Extract all target tables using hybrid approach.

        Args:
            skip_failures: If True, skip tables that fail to extract

        Returns:
            List of raw table data
        """
        tables = []
        failed = []

        for target in TARGET_TABLES:
            logger.info(f"Extracting: {target['name']} (page {target['page']})")
            try:
                raw_table = self._extract_single_table(target)
                tables.append(raw_table)
                logger.info(
                    f"  ✓ Extracted {len(raw_table.rows)} rows via {raw_table.extraction_method}"
                )
            except Exception as e:
                logger.error(f"  ✗ Failed to extract: {e}")
                failed.append((target["simple_name"], str(e)))
                if not skip_failures:
                    raise

        if failed:
            logger.warning(f"\nFailed to extract {len(failed)} tables:")
            for name, error in failed:
                logger.warning(f"  - {name}: {error}")

        return tables

    def _extract_single_table(self, target: TableTarget) -> RawTable:
        """Extract a single table using appropriate method.

        Args:
            target: Target table metadata

        Returns:
            Raw table data
        """
        simple_name = target["simple_name"]
        page_num = target["page"] if isinstance(target["page"], int) else target["page"][0]

        # Check if we have reference data config for this table
        config = get_table_data(simple_name)

        if config:
            # Check if this is a text-parsed table (requires PDF parsing)
            if isinstance(config, dict) and config.get("type") == "text_parsed":
                logger.debug(f"  Using text parser for {simple_name}")
                return self._extract_text_parsed(target, config["config"])

            # Use unified extraction engine with static/calculated config
            logger.debug(f"  Using reference data config for {simple_name}")
            return extract_by_config(
                table_id=target["id"],
                simple_name=simple_name,
                page=target["page"],
                config=config,
                section=target["section"],
            )

        # Fall back to PyMuPDF auto-detection for tables without config
        logger.debug(f"  No config found, trying auto-detection for {simple_name}")
        page = self.doc[page_num - 1]  # 0-indexed
        pymupdf_tables = page.find_tables()

        if pymupdf_tables.tables:
            logger.debug(f"  Found {len(pymupdf_tables.tables)} auto-detected tables")
            best_table = self._select_best_table(pymupdf_tables.tables, target)
            if best_table:
                return self._extract_auto_detected(target, best_table, page_num)

        # No config and auto-detection failed
        raise ValueError(f"No manual extraction method for: {simple_name}")

    def _select_best_table(self, tables: list, target: TableTarget) -> Any | None:
        """Select the best matching table from auto-detected tables.

        Args:
            tables: List of PyMuPDF table objects
            target: Target table metadata

        Returns:
            Best matching table or None
        """
        # Define expected header keywords for common table types
        header_hints: dict[str, list[str]] = {
            "experience_by_cr": ["challenge", "rating", "cr", "xp", "experience"],
            "spell_slots_by_level": ["level", "slot", "spell", "1st", "2nd", "3rd"],
        }

        hints = header_hints.get(target["simple_name"], [])
        if not hints:
            # No hints, return first table with data
            for table in tables:
                extracted = table.extract()
                if len(extracted) > MIN_TABLE_ROWS - 1:  # Has header + at least one row
                    return table
            return None

        # Score each table
        best_score = 0
        best_table = None

        for table in tables:
            extracted = table.extract()
            if len(extracted) < MIN_TABLE_ROWS:  # Need header + data
                continue

            # Check first row (headers) for matching keywords
            header_text = " ".join(str(cell).lower() for cell in extracted[0] if cell)
            score = sum(1 for hint in hints if hint in header_text)

            if score > best_score:
                best_score = score
                best_table = table

        return best_table if best_score > 0 else None

    def _extract_auto_detected(self, target: TableTarget, table: Any, page_num: int) -> RawTable:
        """Extract table using PyMuPDF auto-detection.

        Args:
            target: Target table metadata
            table: PyMuPDF table object
            page_num: Page number (1-indexed)

        Returns:
            Raw table data
        """
        # Extract all cells
        extracted = table.extract()

        # First row is headers
        headers = [str(cell).strip() for cell in extracted[0] if cell]

        # Remaining rows are data
        rows: list[list[str | int | float]] = []
        for row in extracted[1:]:
            # Skip empty rows
            if not any(cell for cell in row):
                continue

            # Clean cells
            clean_row: list[str | int | float] = []
            for cell in row:
                if cell is None or cell == "":
                    clean_row.append("")
                else:
                    cell_str = str(cell).strip()
                    # Try to convert to number if possible
                    try:
                        if "." in cell_str:
                            clean_row.append(float(cell_str))
                        else:
                            clean_row.append(int(cell_str))
                    except ValueError:
                        clean_row.append(cell_str)

            rows.append(clean_row)

        return RawTable(
            table_id=target["id"],
            simple_name=target["simple_name"],
            page=target["page"],
            headers=headers,
            rows=rows,
            extraction_method="auto",
            section=target["section"],
            notes=target.get("notes"),
        )

    def _extract_text_parsed(self, target: TableTarget, parser_config: dict[str, Any]) -> RawTable:
        """Extract table using text parsing (for tables without grid borders).

        Args:
            target: Target table metadata
            parser_config: Parser configuration with 'parser' function name and 'pages'

        Returns:
            RawTable with parsed data
        """
        from .text_table_parser import (
            parse_adventure_gear_table,
            parse_armor_table,
            parse_container_capacity_table,
            parse_donning_doffing_armor_table,
            parse_exchange_rates_table,
            parse_mounts_and_other_animals_table,
            parse_tack_harness_vehicles_table,
            parse_tools_table,
            parse_trade_goods_table,
            parse_waterborne_vehicles_table,
            parse_weapons_table,
        )

        # Map parser names to functions
        parsers = {
            "parse_adventure_gear_table": parse_adventure_gear_table,
            "parse_armor_table": parse_armor_table,
            "parse_container_capacity_table": parse_container_capacity_table,
            "parse_donning_doffing_armor_table": parse_donning_doffing_armor_table,
            "parse_exchange_rates_table": parse_exchange_rates_table,
            "parse_mounts_and_other_animals_table": parse_mounts_and_other_animals_table,
            "parse_tack_harness_vehicles_table": parse_tack_harness_vehicles_table,
            "parse_tools_table": parse_tools_table,
            "parse_trade_goods_table": parse_trade_goods_table,
            "parse_waterborne_vehicles_table": parse_waterborne_vehicles_table,
            "parse_weapons_table": parse_weapons_table,
        }

        parser_name = parser_config["parser"]
        pages = parser_config["pages"]

        if parser_name not in parsers:
            raise ValueError(f"Unknown text parser: {parser_name}")

        # Call the parser
        parser_func = parsers[parser_name]
        result = parser_func(str(self.pdf_path), pages)

        # Convert to RawTable format
        return RawTable(
            table_id=target["id"],
            simple_name=target["simple_name"],
            page=target["page"],
            headers=result["headers"],
            rows=result["rows"],
            extraction_method="text_parsed",
            section=target["section"],
            notes=f"Extracted via {parser_name} from PDF text",
            metadata=result.get("categories"),
        )

    def close(self) -> None:
        """Close the PDF document."""
        self.doc.close()

    def __enter__(self) -> TableExtractor:
        """Context manager entry."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        self.close()


def extract_tables_to_json(
    pdf_path: str | Path, output_path: str | Path, skip_failures: bool = True
) -> None:
    """Extract all target tables and save to JSON.

    Args:
        pdf_path: Path to SRD PDF
        output_path: Path to save tables_raw.json
        skip_failures: If True, skip tables that fail extraction
    """
    import json

    with TableExtractor(pdf_path) as extractor:
        tables = extractor.extract_all_tables(skip_failures=skip_failures)

    # Convert to dict for JSON serialization
    tables_dict = {
        "tables": [
            {
                "table_id": t.table_id,
                "simple_name": t.simple_name,
                "page": t.page,
                "headers": t.headers,
                "rows": t.rows,
                "extraction_method": t.extraction_method,
                "section": t.section,
                "notes": t.notes,
                "metadata": t.metadata,
            }
            for t in tables
        ]
    }

    output_path = Path(output_path)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(tables_dict, f, indent=2, ensure_ascii=False)

    logger.info(f"\nSaved {len(tables)} tables to {output_path}")
