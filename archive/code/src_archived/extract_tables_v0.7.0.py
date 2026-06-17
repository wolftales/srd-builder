#!/usr/bin/env python3
"""ARCHIVED: Original monolithic table extraction (v0.7.0).

This file has been replaced by the table_extraction/ module (v0.9.0+).

The refactor reduced code from 1508 lines to ~850 lines total by:
- Extracting 26 duplicate extraction methods into unified extract_by_config() engine
- Moving hardcoded table data to reference_data.py (690 lines, organized by type)
- Creating patterns.py with single universal extraction function
- Building extractor.py with routing logic (~230 lines)

New structure:
  src/srd_builder/table_extraction/
    __init__.py       - Public API
    extractor.py      - TableExtractor class with PyMuPDF integration
    patterns.py       - Unified extract_by_config() engine
    reference_data.py - All table configs (23 tables)

Key improvements:
- 96% reduction in extraction methods (26 → 1)
- 50% reduction in total code (1508 → ~850 lines)
- Data-driven: Adding new tables requires config only, no new code
- Better separation: extraction logic vs. table data

Extract reference tables from SRD 5.1 PDF.

This module extracts consumer-facing reference tables using a hybrid approach:
1. Auto-detected tables (via table_indexer) for grid-based tables
2. Manual text-based patterns for simple two-column tables

The extraction produces raw table data (headers + rows) that parse_tables.py
will normalize to the schema format.

Archived: 2025-11-04
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF

try:
    from scripts.table_targets import TARGET_TABLES, TableTarget
except ModuleNotFoundError:
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from scripts.table_targets import TARGET_TABLES, TableTarget

logger = logging.getLogger(__name__)


@dataclass
class RawTable:
    """Raw extracted table data before normalization."""

    table_id: str  # From TARGET_TABLES
    simple_name: str
    page: int | list[int]
    headers: list[str]
    rows: list[list[str | int | float]]
    extraction_method: str  # "auto" or "manual"
    section: str | None = None
    notes: str | None = None


# Table extraction constants
MIN_TABLE_ROWS = 2  # Minimum rows required (header + at least one data row)
MIN_CLI_ARGS = 2  # Minimum command-line arguments required (script name + pdf path)
CLI_OUTPUT_PATH_ARG_INDEX = 2  # Index of optional output path in sys.argv

# Proficiency bonus breakpoints by level
PROF_BONUS_LEVEL_4 = 4
PROF_BONUS_LEVEL_8 = 8
PROF_BONUS_LEVEL_12 = 12
PROF_BONUS_LEVEL_16 = 16


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
        page_num = target["page"] if isinstance(target["page"], int) else target["page"][0]

        # Try auto-detection first
        page = self.doc[page_num - 1]  # 0-indexed
        pymupdf_tables = page.find_tables()

        if pymupdf_tables.tables:
            logger.debug(f"  Found {len(pymupdf_tables.tables)} auto-detected tables")
            # Try to find the right table by matching expected headers
            best_table = self._select_best_table(pymupdf_tables.tables, target)
            if best_table:
                return self._extract_auto_detected(target, best_table, page_num)

        # Fall back to manual extraction
        logger.debug("  Auto-detection failed, using manual pattern")
        return self._extract_manual(target, page, page_num)

    def _select_best_table(self, tables: list, target: TableTarget) -> Any | None:
        """Select the best matching table from auto-detected tables.

        Args:
            tables: List of PyMuPDF table objects
            target: Target table metadata

        Returns:
            Best matching table or None
        """
        # Define expected header keywords for each table type
        header_hints = {
            "proficiency_bonus": ["level", "proficiency", "bonus"],
            "experience_by_cr": ["challenge", "rating", "cr", "xp", "experience"],
            "spell_slots_by_level": ["level", "slot", "spell", "1st", "2nd", "3rd"],
            "cantrip_damage": ["level", "cantrip", "damage", "dice"],
            "travel_pace": ["pace", "distance", "hour", "day", "fast", "normal", "slow"],
            # Class progression tables
            "barbarian_progression": ["level", "proficiency", "features", "rage", "damage"],
            "bard_progression": ["level", "proficiency", "features", "cantrips", "spells", "slots"],
            "cleric_progression": [
                "level",
                "proficiency",
                "features",
                "cantrips",
                "spell",
                "slots",
            ],
            "druid_progression": ["level", "proficiency", "features", "cantrips", "spell", "slots"],
            "fighter_progression": ["level", "proficiency", "features"],
            "monk_progression": [
                "level",
                "proficiency",
                "features",
                "martial",
                "arts",
                "ki",
                "movement",
            ],
            "paladin_progression": ["level", "proficiency", "features", "spell", "slots"],
            "ranger_progression": ["level", "proficiency", "features", "spells", "spell", "slots"],
            "rogue_progression": ["level", "proficiency", "features", "sneak", "attack"],
            "sorcerer_progression": [
                "level",
                "proficiency",
                "features",
                "cantrips",
                "spells",
                "spell",
                "slots",
                "sorcery",
            ],
            "warlock_progression": [
                "level",
                "proficiency",
                "features",
                "cantrips",
                "spells",
                "spell",
                "slots",
                "invocations",
            ],
            "wizard_progression": [
                "level",
                "proficiency",
                "features",
                "cantrips",
                "spell",
                "slots",
            ],
        }

        hints = header_hints.get(target["simple_name"], [])
        if not hints:
            # No hints, return first table with data
            for table in tables:
                extracted = table.extract()
                if len(extracted) > 1:  # Has header + at least one row
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

    def _extract_manual(self, target: TableTarget, page: fitz.Page, page_num: int) -> RawTable:  # noqa: C901
        """Extract table using manual text-based pattern.

        Args:
            target: Target table metadata
            page: PyMuPDF page object
            page_num: Page number (1-indexed)

        Returns:
            Raw table data
        """
        simple_name = target["simple_name"]

        # Route to specific extraction method
        if simple_name == "ability_scores_and_modifiers":
            return self._extract_ability_scores(target, page, page_num)
        elif simple_name == "proficiency_bonus":
            return self._extract_proficiency_bonus(target, page, page_num)
        elif simple_name == "experience_by_cr":
            return self._extract_experience_by_cr(target, page, page_num)
        elif simple_name == "spell_slots_by_level":
            return self._extract_spell_slots(target, page, page_num)
        elif simple_name == "cantrip_damage":
            return self._extract_cantrip_damage(target, page, page_num)
        elif simple_name == "travel_pace":
            return self._extract_travel_pace(target, page, page_num)
        elif simple_name == "food_drink_lodging":
            return self._extract_food_drink_lodging(target, page, page_num)
        elif simple_name == "services":
            return self._extract_services(target, page, page_num)
        elif simple_name == "creature_size":
            return self._extract_creature_size(target, page, page_num)
        elif simple_name == "carrying_capacity":
            return self._extract_carrying_capacity(target, page, page_num)
        elif simple_name == "lifestyle_expenses":
            return self._extract_lifestyle_expenses(target, page, page_num)
        elif simple_name == "barbarian_progression":
            return self._extract_barbarian_progression(target, page, page_num)
        elif simple_name == "bard_progression":
            return self._extract_bard_progression(target, page, page_num)
        elif simple_name == "cleric_progression":
            return self._extract_cleric_progression(target, page, page_num)
        elif simple_name == "druid_progression":
            return self._extract_druid_progression(target, page, page_num)
        elif simple_name == "fighter_progression":
            return self._extract_fighter_progression(target, page, page_num)
        elif simple_name == "monk_progression":
            return self._extract_monk_progression(target, page, page_num)
        elif simple_name == "paladin_progression":
            return self._extract_paladin_progression(target, page, page_num)
        elif simple_name == "ranger_progression":
            return self._extract_ranger_progression(target, page, page_num)
        elif simple_name == "rogue_progression":
            return self._extract_rogue_progression(target, page, page_num)
        elif simple_name == "sorcerer_progression":
            return self._extract_sorcerer_progression(target, page, page_num)
        elif simple_name == "warlock_progression":
            return self._extract_warlock_progression(target, page, page_num)
        elif simple_name == "wizard_progression":
            return self._extract_wizard_progression(target, page, page_num)
        else:
            raise ValueError(f"No manual extraction method for: {simple_name}")

    def _extract_ability_scores(
        self, target: TableTarget, page: fitz.Page, page_num: int
    ) -> RawTable:
        """Extract Ability Scores and Modifiers table (page 7).

        Due to PDF text extraction issues, use reference data.
        Formula: modifier = (score - 10) // 2
        """
        rows: list[list[str | int | float]] = []
        for score in range(1, 31):
            modifier = (score - 10) // 2
            modifier_str = f"+{modifier}" if modifier > 0 else str(modifier)
            rows.append([score, modifier_str])

        return RawTable(
            table_id=target["id"],
            simple_name=target["simple_name"],
            page=page_num,
            headers=["Score", "Modifier"],
            rows=rows,
            extraction_method="manual",
            section=target["section"],
            notes="Calculated from formula: (score - 10) // 2",
        )

    def _extract_proficiency_bonus(
        self, target: TableTarget, page: fitz.Page, page_num: int
    ) -> RawTable:
        """Extract Proficiency Bonus by Level table (page 15).

        Due to PDF text extraction issues, use reference data.
        """
        # Proficiency bonus by level (SRD 5.1 reference)
        rows: list[list[str | int | float]] = []
        for level in range(1, 21):
            if level <= PROF_BONUS_LEVEL_4:
                bonus = "+2"
            elif level <= PROF_BONUS_LEVEL_8:
                bonus = "+3"
            elif level <= PROF_BONUS_LEVEL_12:
                bonus = "+4"
            elif level <= PROF_BONUS_LEVEL_16:
                bonus = "+5"
            else:
                bonus = "+6"
            rows.append([level, bonus])

        return RawTable(
            table_id=target["id"],
            simple_name=target["simple_name"],
            page=page_num,
            headers=["Level", "Proficiency Bonus"],
            rows=rows,
            extraction_method="manual",
            section=target["section"],
            notes="Reference data from SRD 5.1",
        )

    def _extract_experience_by_cr(
        self, target: TableTarget, page: fitz.Page, page_num: int
    ) -> RawTable:
        """Extract Experience Points by Challenge Rating table (page 57).

        Due to PDF text extraction issues, use reference data.
        """
        # XP by CR (SRD 5.1 reference)
        rows: list[list[str | int | float]] = [
            ["0", 0],
            ["1/8", 25],
            ["1/4", 50],
            ["1/2", 100],
            ["1", 200],
            ["2", 450],
            ["3", 700],
            ["4", 1100],
            ["5", 1800],
            ["6", 2300],
            ["7", 2900],
            ["8", 3900],
            ["9", 5000],
            ["10", 5900],
            ["11", 7200],
            ["12", 8400],
            ["13", 10000],
            ["14", 11500],
            ["15", 13000],
            ["16", 15000],
            ["17", 18000],
            ["18", 20000],
            ["19", 22000],
            ["20", 25000],
            ["21", 33000],
            ["22", 41000],
            ["23", 50000],
            ["24", 62000],
            ["25", 75000],
            ["26", 90000],
            ["27", 105000],
            ["28", 120000],
            ["29", 135000],
            ["30", 155000],
        ]

        return RawTable(
            table_id=target["id"],
            simple_name=target["simple_name"],
            page=page_num,
            headers=["Challenge Rating", "XP"],
            rows=rows,
            extraction_method="manual",
            section=target["section"],
            notes="Reference data from SRD 5.1",
        )

    def _extract_spell_slots(self, target: TableTarget, page: fitz.Page, page_num: int) -> RawTable:
        """Extract Spell Slots by Character Level table (page 201).

        Due to PDF text extraction issues, use reference data.
        Full caster progression (Cleric, Druid, Wizard).
        """
        # Spell slots by level (full caster progression)
        rows: list[list[str | int | float]] = [
            [1, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [2, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [3, 4, 2, 0, 0, 0, 0, 0, 0, 0, 0],
            [4, 4, 3, 0, 0, 0, 0, 0, 0, 0, 0],
            [5, 4, 3, 2, 0, 0, 0, 0, 0, 0, 0],
            [6, 4, 3, 3, 0, 0, 0, 0, 0, 0, 0],
            [7, 4, 3, 3, 1, 0, 0, 0, 0, 0, 0],
            [8, 4, 3, 3, 2, 0, 0, 0, 0, 0, 0],
            [9, 4, 3, 3, 3, 1, 0, 0, 0, 0, 0],
            [10, 4, 3, 3, 3, 2, 0, 0, 0, 0, 0],
            [11, 4, 3, 3, 3, 2, 1, 0, 0, 0, 0],
            [12, 4, 3, 3, 3, 2, 1, 0, 0, 0, 0],
            [13, 4, 3, 3, 3, 2, 1, 1, 0, 0, 0],
            [14, 4, 3, 3, 3, 2, 1, 1, 0, 0, 0],
            [15, 4, 3, 3, 3, 2, 1, 1, 1, 0, 0],
            [16, 4, 3, 3, 3, 2, 1, 1, 1, 0, 0],
            [17, 4, 3, 3, 3, 2, 1, 1, 1, 1, 0],
            [18, 4, 3, 3, 3, 3, 1, 1, 1, 1, 0],
            [19, 4, 3, 3, 3, 3, 2, 1, 1, 1, 0],
            [20, 4, 3, 3, 3, 3, 2, 2, 1, 1, 0],
        ]

        return RawTable(
            table_id=target["id"],
            simple_name=target["simple_name"],
            page=page_num,
            headers=[
                "Level",
                "1st",
                "2nd",
                "3rd",
                "4th",
                "5th",
                "6th",
                "7th",
                "8th",
                "9th",
                "Cantrips Known",
            ],
            rows=rows,
            extraction_method="manual",
            section=target["section"],
            notes="Full caster progression (Cleric, Druid, Wizard). Reference data from SRD 5.1",
        )

    def _extract_cantrip_damage(
        self, target: TableTarget, page: fitz.Page, page_num: int
    ) -> RawTable:
        """Extract Cantrip Damage by Character Level table (page 201).

        Due to PDF text extraction issues, use reference data.
        """
        rows: list[list[str | int | float]] = [
            ["1st-4th", "1 die"],
            ["5th-10th", "2 dice"],
            ["11th-16th", "3 dice"],
            ["17th-20th", "4 dice"],
        ]

        return RawTable(
            table_id=target["id"],
            simple_name=target["simple_name"],
            page=page_num,
            headers=["Character Level", "Damage"],
            rows=rows,
            extraction_method="manual",
            section=target["section"],
            notes="Reference data from SRD 5.1",
        )

    def _extract_travel_pace(self, target: TableTarget, page: fitz.Page, page_num: int) -> RawTable:
        """Extract Travel Pace table (page 242).

        Due to PDF text extraction issues, use reference data.
        """
        rows: list[list[str | int | float]] = [
            ["Fast", "400 feet", "4 miles", "30 miles"],
            ["Normal", "300 feet", "3 miles", "24 miles"],
            ["Slow", "200 feet", "2 miles", "18 miles"],
        ]

        return RawTable(
            table_id=target["id"],
            simple_name=target["simple_name"],
            page=page_num,
            headers=["Pace", "Distance per Minute", "Distance per Hour", "Distance per Day"],
            rows=rows,
            extraction_method="manual",
            section=target["section"],
            notes="Reference data from SRD 5.1",
        )

    def _extract_food_drink_lodging(
        self, target: TableTarget, page: fitz.Page, page_num: int
    ) -> RawTable:
        """Extract Food, Drink, and Lodging table (page 158).

        Due to PDF text extraction issues, use reference data.
        """
        rows: list[list[str | int | float]] = [
            ["Ale (gallon)", "2 sp"],
            ["Ale (mug)", "4 cp"],
            ["Banquet (per person)", "10 gp"],
            ["Bread (loaf)", "2 cp"],
            ["Cheese (hunk)", "1 sp"],
            ["Inn stay per day (Squalid)", "7 cp"],
            ["Inn stay per day (Poor)", "1 sp"],
            ["Inn stay per day (Modest)", "5 sp"],
            ["Inn stay per day (Comfortable)", "8 sp"],
            ["Inn stay per day (Wealthy)", "2 gp"],
            ["Inn stay per day (Aristocratic)", "4 gp"],
            ["Meals per day (Squalid)", "3 cp"],
            ["Meals per day (Poor)", "6 cp"],
            ["Meals per day (Modest)", "3 sp"],
            ["Meals per day (Comfortable)", "5 sp"],
            ["Meals per day (Wealthy)", "8 sp"],
            ["Meals per day (Aristocratic)", "2 gp"],
            ["Wine (common, pitcher)", "2 sp"],
            ["Wine (fine, bottle)", "10 gp"],
        ]

        return RawTable(
            table_id=target["id"],
            simple_name=target["simple_name"],
            page=page_num,
            headers=["Item", "Cost"],
            rows=rows,
            extraction_method="manual",
            section=target["section"],
            notes="Reference data from SRD 5.1",
        )

    def _extract_services(self, target: TableTarget, page: fitz.Page, page_num: int) -> RawTable:
        """Extract Services table (page 159).

        Due to PDF text extraction issues, use reference data.
        """
        rows: list[list[str | int | float]] = [
            ["Coach cab (between towns)", "3 cp per mile"],
            ["Coach cab (within city)", "1 cp"],
            ["Hireling (skilled)", "2 gp per day"],
            ["Hireling (untrained)", "2 sp per day"],
            ["Messenger", "2 cp per mile"],
            ["Road or gate toll", "1 cp"],
            ["Ship's passage", "1 sp per mile"],
        ]

        return RawTable(
            table_id=target["id"],
            simple_name=target["simple_name"],
            page=page_num,
            headers=["Service", "Cost"],
            rows=rows,
            extraction_method="manual",
            section=target["section"],
            notes="Reference data from SRD 5.1",
        )

    def _extract_creature_size(
        self, target: TableTarget, page: fitz.Page, page_num: int
    ) -> RawTable:
        """Extract Size Categories table (page 191).

        Two columns: Size | Space
        """
        text = page.get_text()

        # Find size categories
        sizes = ["Tiny", "Small", "Medium", "Large", "Huge", "Gargantuan"]
        rows: list[list[str | int | float]] = []

        for size in sizes:
            # Pattern: "Size by Space" or "Size X by X ft."
            pattern = rf"{size}\s+(\d+\s+by\s+\d+\s+ft\.|2½\s+by\s+2½\s+ft\.)"
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                space = match.group(1)
                rows.append([size, space])

        if not rows:
            # Fallback with known values
            rows = [
                ["Tiny", "2½ by 2½ ft."],
                ["Small", "5 by 5 ft."],
                ["Medium", "5 by 5 ft."],
                ["Large", "10 by 10 ft."],
                ["Huge", "15 by 15 ft."],
                ["Gargantuan", "20 by 20 ft. or larger"],
            ]

        return RawTable(
            table_id=target["id"],
            simple_name=target["simple_name"],
            page=page_num,
            headers=["Size", "Space"],
            rows=rows,
            extraction_method="manual",
            section=target["section"],
            notes=target.get("notes"),
        )

    def _extract_carrying_capacity(
        self, target: TableTarget, page: fitz.Page, page_num: int
    ) -> RawTable:
        """Extract Carrying Capacity table (page 176).

        Two columns: Strength Score | Carrying Capacity (lbs)
        """
        # This might be a formula rather than a table
        # Pattern: Strength score × 15
        # Create formula-based table
        rows: list[list[str | int | float]] = []
        for strength in range(1, 31):  # Strength 1-30
            capacity = strength * 15
            rows.append([strength, capacity])

        return RawTable(
            table_id=target["id"],
            simple_name=target["simple_name"],
            page=page_num,
            headers=["Strength Score", "Carrying Capacity (lbs)"],
            rows=rows,
            extraction_method="manual",
            section=target["section"],
            notes="Calculated from formula: Strength × 15",
        )

    def _extract_lifestyle_expenses(
        self, target: TableTarget, page: fitz.Page, page_num: int
    ) -> RawTable:
        """Extract Lifestyle Expenses table (page 157).

        Due to PDF text extraction issues, use reference data.
        """
        rows: list[list[str | int | float]] = [
            ["Wretched", "—"],
            ["Squalid", "1 sp"],
            ["Poor", "2 sp"],
            ["Modest", "1 gp"],
            ["Comfortable", "2 gp"],
            ["Wealthy", "4 gp"],
            ["Aristocratic", "10 gp minimum"],
        ]

        return RawTable(
            table_id=target["id"],
            simple_name=target["simple_name"],
            page=page_num,
            headers=["Lifestyle", "Cost per Day"],
            rows=rows,
            extraction_method="manual",
            section=target["section"],
            notes="Reference data from SRD 5.1",
        )

    def _extract_barbarian_progression(
        self, target: TableTarget, page: fitz.Page, page_num: int
    ) -> RawTable:
        """Extract Barbarian progression table (page 8).

        Columns: Level, Proficiency Bonus, Features, Rages, Rage Damage
        """
        rows: list[list[str | int | float]] = [
            [1, "+2", "Rage, Unarmored Defense", 2, "+2"],
            [2, "+2", "Reckless Attack, Danger Sense", 2, "+2"],
            [3, "+2", "Primal Path", 3, "+2"],
            [4, "+2", "Ability Score Improvement", 3, "+2"],
            [5, "+3", "Extra Attack, Fast Movement", 3, "+2"],
            [6, "+3", "Path feature", 4, "+2"],
            [7, "+3", "Feral Instinct", 4, "+2"],
            [8, "+3", "Ability Score Improvement", 4, "+2"],
            [9, "+4", "Brutal Critical (1 die)", 4, "+3"],
            [10, "+4", "Path feature", 4, "+3"],
            [11, "+4", "Relentless Rage", 4, "+3"],
            [12, "+4", "Ability Score Improvement", 5, "+3"],
            [13, "+5", "Brutal Critical (2 dice)", 5, "+3"],
            [14, "+5", "Path feature", 5, "+3"],
            [15, "+5", "Persistent Rage", 5, "+3"],
            [16, "+5", "Ability Score Improvement", 5, "+4"],
            [17, "+6", "Brutal Critical (3 dice)", 6, "+4"],
            [18, "+6", "Indomitable Might", 6, "+4"],
            [19, "+6", "Ability Score Improvement", 6, "+4"],
            [20, "+6", "Primal Champion", "Unlimited", "+4"],
        ]

        return RawTable(
            table_id=target["id"],
            simple_name=target["simple_name"],
            page=page_num,
            headers=["Level", "Proficiency Bonus", "Features", "Rages", "Rage Damage"],
            rows=rows,
            extraction_method="manual",
            section=target["section"],
            notes="Reference data from SRD 5.1",
        )

    def _extract_bard_progression(
        self, target: TableTarget, page: fitz.Page, page_num: int
    ) -> RawTable:
        """Extract Bard progression table (page 11).

        Columns: Level, Proficiency Bonus, Features, Cantrips Known, Spells Known,
                 Spell Slots (1st-9th)
        """
        rows: list[list[str | int | float]] = [
            [1, "+2", "Spellcasting, Bardic Inspiration (d6)", 2, 4, 2, 0, 0, 0, 0, 0, 0, 0, 0],
            [2, "+2", "Jack of All Trades, Song of Rest (d6)", 2, 5, 3, 0, 0, 0, 0, 0, 0, 0, 0],
            [3, "+2", "Bard College, Expertise", 2, 6, 4, 2, 0, 0, 0, 0, 0, 0, 0],
            [4, "+2", "Ability Score Improvement", 3, 7, 4, 3, 0, 0, 0, 0, 0, 0, 0],
            [
                5,
                "+3",
                "Bardic Inspiration (d8), Font of Inspiration",
                3,
                8,
                4,
                3,
                2,
                0,
                0,
                0,
                0,
                0,
                0,
            ],
            [6, "+3", "Countercharm, Bard College feature", 3, 9, 4, 3, 3, 0, 0, 0, 0, 0, 0],
            [7, "+3", "—", 3, 10, 4, 3, 3, 1, 0, 0, 0, 0, 0],
            [8, "+3", "Ability Score Improvement", 3, 11, 4, 3, 3, 2, 0, 0, 0, 0, 0],
            [9, "+4", "Song of Rest (d8)", 3, 12, 4, 3, 3, 3, 1, 0, 0, 0, 0],
            [
                10,
                "+4",
                "Bardic Inspiration (d10), Expertise, Magical Secrets",
                4,
                14,
                4,
                3,
                3,
                3,
                2,
                0,
                0,
                0,
                0,
            ],
            [11, "+4", "—", 4, 15, 4, 3, 3, 3, 2, 1, 0, 0, 0],
            [12, "+4", "Ability Score Improvement", 4, 15, 4, 3, 3, 3, 2, 1, 0, 0, 0],
            [13, "+5", "Song of Rest (d10)", 4, 16, 4, 3, 3, 3, 2, 1, 1, 0, 0],
            [14, "+5", "Magical Secrets, Bard College feature", 4, 18, 4, 3, 3, 3, 2, 1, 1, 0, 0],
            [15, "+5", "Bardic Inspiration (d12)", 4, 19, 4, 3, 3, 3, 2, 1, 1, 1, 0],
            [16, "+5", "Ability Score Improvement", 4, 19, 4, 3, 3, 3, 2, 1, 1, 1, 0],
            [17, "+6", "Song of Rest (d12)", 4, 20, 4, 3, 3, 3, 2, 1, 1, 1, 1],
            [18, "+6", "Magical Secrets", 4, 22, 4, 3, 3, 3, 3, 1, 1, 1, 1],
            [19, "+6", "Ability Score Improvement", 4, 22, 4, 3, 3, 3, 3, 2, 1, 1, 1],
            [20, "+6", "Superior Inspiration", 4, 22, 4, 3, 3, 3, 3, 2, 2, 1, 1],
        ]

        return RawTable(
            table_id=target["id"],
            simple_name=target["simple_name"],
            page=page_num,
            headers=[
                "Level",
                "Proficiency Bonus",
                "Features",
                "Cantrips Known",
                "Spells Known",
                "1st",
                "2nd",
                "3rd",
                "4th",
                "5th",
                "6th",
                "7th",
                "8th",
                "9th",
            ],
            rows=rows,
            extraction_method="manual",
            section=target["section"],
            notes="Reference data from SRD 5.1",
        )

    def _extract_cleric_progression(
        self, target: TableTarget, page: fitz.Page, page_num: int
    ) -> RawTable:
        """Extract Cleric progression table (page 16).

        Columns: Level, Proficiency Bonus, Features, Cantrips Known, Spell Slots (1st-9th)
        """
        rows: list[list[str | int | float]] = [
            [1, "+2", "Spellcasting, Divine Domain", 3, 2, 0, 0, 0, 0, 0, 0, 0, 0],
            [
                2,
                "+2",
                "Channel Divinity (1/rest), Divine Domain feature",
                3,
                3,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
            ],
            [3, "+2", "—", 3, 4, 2, 0, 0, 0, 0, 0, 0, 0],
            [4, "+2", "Ability Score Improvement", 4, 4, 3, 0, 0, 0, 0, 0, 0, 0],
            [5, "+3", "Destroy Undead (CR 1/2)", 4, 4, 3, 2, 0, 0, 0, 0, 0, 0],
            [
                6,
                "+3",
                "Channel Divinity (2/rest), Divine Domain feature",
                4,
                4,
                3,
                3,
                0,
                0,
                0,
                0,
                0,
                0,
            ],
            [7, "+3", "—", 4, 4, 3, 3, 1, 0, 0, 0, 0, 0],
            [
                8,
                "+3",
                "Ability Score Improvement, Destroy Undead (CR 1), Divine Domain feature",
                4,
                4,
                3,
                3,
                2,
                0,
                0,
                0,
                0,
                0,
            ],
            [9, "+4", "—", 4, 4, 3, 3, 3, 1, 0, 0, 0, 0],
            [10, "+4", "Divine Intervention", 5, 4, 3, 3, 3, 2, 0, 0, 0, 0],
            [11, "+4", "Destroy Undead (CR 2)", 5, 4, 3, 3, 3, 2, 1, 0, 0, 0],
            [12, "+4", "Ability Score Improvement", 5, 4, 3, 3, 3, 2, 1, 0, 0, 0],
            [13, "+5", "—", 5, 4, 3, 3, 3, 2, 1, 1, 0, 0],
            [14, "+5", "Destroy Undead (CR 3)", 5, 4, 3, 3, 3, 2, 1, 1, 0, 0],
            [15, "+5", "—", 5, 4, 3, 3, 3, 2, 1, 1, 1, 0],
            [16, "+5", "Ability Score Improvement", 5, 4, 3, 3, 3, 2, 1, 1, 1, 0],
            [
                17,
                "+6",
                "Destroy Undead (CR 4), Divine Domain feature",
                5,
                4,
                3,
                3,
                3,
                2,
                1,
                1,
                1,
                1,
            ],
            [18, "+6", "Channel Divinity (3/rest)", 5, 4, 3, 3, 3, 3, 1, 1, 1, 1],
            [19, "+6", "Ability Score Improvement", 5, 4, 3, 3, 3, 3, 2, 1, 1, 1],
            [20, "+6", "Divine Intervention improvement", 5, 4, 3, 3, 3, 3, 2, 2, 1, 1],
        ]

        return RawTable(
            table_id=target["id"],
            simple_name=target["simple_name"],
            page=page_num,
            headers=[
                "Level",
                "Proficiency Bonus",
                "Features",
                "Cantrips Known",
                "1st",
                "2nd",
                "3rd",
                "4th",
                "5th",
                "6th",
                "7th",
                "8th",
                "9th",
            ],
            rows=rows,
            extraction_method="manual",
            section=target["section"],
            notes="Reference data from SRD 5.1",
        )

    def _extract_druid_progression(
        self, target: TableTarget, page: fitz.Page, page_num: int
    ) -> RawTable:
        """Extract Druid progression table (page 25).

        Columns: Level, Proficiency Bonus, Features, Cantrips Known, Spell Slots (1st-9th)
        """
        rows: list[list[str | int | float]] = [
            [1, "+2", "Druidic, Spellcasting", 2, 2, 0, 0, 0, 0, 0, 0, 0, 0],
            [2, "+2", "Wild Shape, Druid Circle", 2, 3, 0, 0, 0, 0, 0, 0, 0, 0],
            [3, "+2", "—", 2, 4, 2, 0, 0, 0, 0, 0, 0, 0],
            [
                4,
                "+2",
                "Wild Shape improvement, Ability Score Improvement",
                3,
                4,
                3,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
            ],
            [5, "+3", "—", 3, 4, 3, 2, 0, 0, 0, 0, 0, 0],
            [6, "+3", "Druid Circle feature", 3, 4, 3, 3, 0, 0, 0, 0, 0, 0],
            [7, "+3", "—", 3, 4, 3, 3, 1, 0, 0, 0, 0, 0],
            [
                8,
                "+3",
                "Wild Shape improvement, Ability Score Improvement",
                3,
                4,
                3,
                3,
                2,
                0,
                0,
                0,
                0,
                0,
            ],
            [9, "+4", "—", 3, 4, 3, 3, 3, 1, 0, 0, 0, 0],
            [10, "+4", "Druid Circle feature", 4, 4, 3, 3, 3, 2, 0, 0, 0, 0],
            [11, "+4", "—", 4, 4, 3, 3, 3, 2, 1, 0, 0, 0],
            [12, "+4", "Ability Score Improvement", 4, 4, 3, 3, 3, 2, 1, 0, 0, 0],
            [13, "+5", "—", 4, 4, 3, 3, 3, 2, 1, 1, 0, 0],
            [14, "+5", "Druid Circle feature", 4, 4, 3, 3, 3, 2, 1, 1, 0, 0],
            [15, "+5", "—", 4, 4, 3, 3, 3, 2, 1, 1, 1, 0],
            [16, "+5", "Ability Score Improvement", 4, 4, 3, 3, 3, 2, 1, 1, 1, 0],
            [17, "+6", "—", 4, 4, 3, 3, 3, 2, 1, 1, 1, 1],
            [18, "+6", "Timeless Body, Beast Spells", 4, 4, 3, 3, 3, 3, 1, 1, 1, 1],
            [19, "+6", "Ability Score Improvement", 4, 4, 3, 3, 3, 3, 2, 1, 1, 1],
            [20, "+6", "Archdruid", 4, 4, 3, 3, 3, 3, 2, 2, 1, 1],
        ]

        return RawTable(
            table_id=target["id"],
            simple_name=target["simple_name"],
            page=page_num,
            headers=[
                "Level",
                "Proficiency Bonus",
                "Features",
                "Cantrips Known",
                "1st",
                "2nd",
                "3rd",
                "4th",
                "5th",
                "6th",
                "7th",
                "8th",
                "9th",
            ],
            rows=rows,
            extraction_method="manual",
            section=target["section"],
            notes="Reference data from SRD 5.1",
        )

    def _extract_fighter_progression(
        self, target: TableTarget, page: fitz.Page, page_num: int
    ) -> RawTable:
        """Extract Fighter progression table (page 26).

        Columns: Level, Proficiency Bonus, Features
        """
        rows: list[list[str | int | float]] = [
            [1, "+2", "Fighting Style, Second Wind"],
            [2, "+2", "Action Surge (one use)"],
            [3, "+2", "Martial Archetype"],
            [4, "+2", "Ability Score Improvement"],
            [5, "+3", "Extra Attack"],
            [6, "+3", "Ability Score Improvement"],
            [7, "+3", "Martial Archetype feature"],
            [8, "+3", "Ability Score Improvement"],
            [9, "+4", "Indomitable (one use)"],
            [10, "+4", "Martial Archetype feature"],
            [11, "+4", "Extra Attack (2)"],
            [12, "+4", "Ability Score Improvement"],
            [13, "+5", "Indomitable (two uses)"],
            [14, "+5", "Ability Score Improvement"],
            [15, "+5", "Martial Archetype feature"],
            [16, "+5", "Ability Score Improvement"],
            [17, "+6", "Action Surge (two uses), Indomitable (three uses)"],
            [18, "+6", "Martial Archetype feature"],
            [19, "+6", "Ability Score Improvement"],
            [20, "+6", "Extra Attack (3)"],
        ]

        return RawTable(
            table_id=target["id"],
            simple_name=target["simple_name"],
            page=page_num,
            headers=["Level", "Proficiency Bonus", "Features"],
            rows=rows,
            extraction_method="manual",
            section=target["section"],
            notes="Reference data from SRD 5.1",
        )

    def _extract_monk_progression(
        self, target: TableTarget, page: fitz.Page, page_num: int
    ) -> RawTable:
        """Extract Monk progression table (page 28).

        Columns: Level, Proficiency Bonus, Features, Martial Arts, Ki Points, Unarmored Movement
        """
        rows: list[list[str | int | float]] = [
            [1, "+2", "Unarmored Defense, Martial Arts", "1d4", "—", "—"],
            [2, "+2", "Ki, Unarmored Movement", "1d4", 2, "+10 ft."],
            [3, "+2", "Monastic Tradition, Deflect Missiles", "1d4", 3, "+10 ft."],
            [4, "+2", "Ability Score Improvement, Slow Fall", "1d4", 4, "+10 ft."],
            [5, "+3", "Extra Attack, Stunning Strike", "1d6", 5, "+10 ft."],
            [6, "+3", "Ki-Empowered Strikes, Monastic Tradition feature", "1d6", 6, "+15 ft."],
            [7, "+3", "Evasion, Stillness of Mind", "1d6", 7, "+15 ft."],
            [8, "+3", "Ability Score Improvement", "1d6", 8, "+15 ft."],
            [9, "+4", "Unarmored Movement improvement", "1d6", 9, "+15 ft."],
            [10, "+4", "Purity of Body", "1d6", 10, "+20 ft."],
            [11, "+4", "Monastic Tradition feature", "1d8", 11, "+20 ft."],
            [12, "+4", "Ability Score Improvement", "1d8", 12, "+20 ft."],
            [13, "+5", "Tongue of the Sun and Moon", "1d8", 13, "+20 ft."],
            [14, "+5", "Diamond Soul", "1d8", 14, "+25 ft."],
            [15, "+5", "Timeless Body", "1d8", 15, "+25 ft."],
            [16, "+5", "Ability Score Improvement", "1d8", 16, "+25 ft."],
            [17, "+6", "Monastic Tradition feature", "1d10", 17, "+25 ft."],
            [18, "+6", "Empty Body", "1d10", 18, "+30 ft."],
            [19, "+6", "Ability Score Improvement", "1d10", 19, "+30 ft."],
            [20, "+6", "Perfect Self", "1d10", 20, "+30 ft."],
        ]

        return RawTable(
            table_id=target["id"],
            simple_name=target["simple_name"],
            page=page_num,
            headers=[
                "Level",
                "Proficiency Bonus",
                "Features",
                "Martial Arts",
                "Ki Points",
                "Unarmored Movement",
            ],
            rows=rows,
            extraction_method="manual",
            section=target["section"],
            notes="Reference data from SRD 5.1",
        )

    def _extract_paladin_progression(
        self, target: TableTarget, page: fitz.Page, page_num: int
    ) -> RawTable:
        """Extract Paladin progression table (page 31).

        Columns: Level, Proficiency Bonus, Features, Spell Slots (1st-5th)
        Half caster progression.
        """
        rows: list[list[str | int | float]] = [
            [1, "+2", "Divine Sense, Lay on Hands", 0, 0, 0, 0, 0],
            [2, "+2", "Fighting Style, Spellcasting, Divine Smite", 2, 0, 0, 0, 0],
            [3, "+2", "Divine Health, Sacred Oath", 3, 0, 0, 0, 0],
            [4, "+2", "Ability Score Improvement", 3, 0, 0, 0, 0],
            [5, "+3", "Extra Attack", 4, 2, 0, 0, 0],
            [6, "+3", "Aura of Protection", 4, 2, 0, 0, 0],
            [7, "+3", "Sacred Oath feature", 4, 3, 0, 0, 0],
            [8, "+3", "Ability Score Improvement", 4, 3, 0, 0, 0],
            [9, "+4", "—", 4, 3, 2, 0, 0],
            [10, "+4", "Aura of Courage", 4, 3, 2, 0, 0],
            [11, "+4", "Improved Divine Smite", 4, 3, 3, 0, 0],
            [12, "+4", "Ability Score Improvement", 4, 3, 3, 0, 0],
            [13, "+5", "—", 4, 3, 3, 1, 0],
            [14, "+5", "Cleansing Touch", 4, 3, 3, 1, 0],
            [15, "+5", "Sacred Oath feature", 4, 3, 3, 2, 0],
            [16, "+5", "Ability Score Improvement", 4, 3, 3, 2, 0],
            [17, "+6", "—", 4, 3, 3, 3, 1],
            [18, "+6", "Aura improvements", 4, 3, 3, 3, 1],
            [19, "+6", "Ability Score Improvement", 4, 3, 3, 3, 2],
            [20, "+6", "Sacred Oath feature", 4, 3, 3, 3, 2],
        ]

        return RawTable(
            table_id=target["id"],
            simple_name=target["simple_name"],
            page=page_num,
            headers=["Level", "Proficiency Bonus", "Features", "1st", "2nd", "3rd", "4th", "5th"],
            rows=rows,
            extraction_method="manual",
            section=target["section"],
            notes="Half caster progression. Reference data from SRD 5.1",
        )

    def _extract_ranger_progression(
        self, target: TableTarget, page: fitz.Page, page_num: int
    ) -> RawTable:
        """Extract Ranger progression table (page 37).

        Columns: Level, Proficiency Bonus, Features, Spells Known, Spell Slots (1st-5th)
        Half caster progression.
        """
        rows: list[list[str | int | float]] = [
            [1, "+2", "Favored Enemy, Natural Explorer", 0, 0, 0, 0, 0, 0],
            [2, "+2", "Fighting Style, Spellcasting", 2, 2, 0, 0, 0, 0],
            [3, "+2", "Ranger Archetype, Primeval Awareness", 3, 3, 0, 0, 0, 0],
            [4, "+2", "Ability Score Improvement", 3, 3, 0, 0, 0, 0],
            [5, "+3", "Extra Attack", 4, 4, 2, 0, 0, 0],
            [6, "+3", "Favored Enemy and Natural Explorer improvements", 4, 4, 2, 0, 0, 0],
            [7, "+3", "Ranger Archetype feature", 5, 4, 3, 0, 0, 0],
            [8, "+3", "Ability Score Improvement, Land's Stride", 5, 4, 3, 0, 0, 0],
            [9, "+4", "—", 6, 4, 3, 2, 0, 0],
            [10, "+4", "Natural Explorer improvement, Hide in Plain Sight", 6, 4, 3, 2, 0, 0],
            [11, "+4", "Ranger Archetype feature", 7, 4, 3, 3, 0, 0],
            [12, "+4", "Ability Score Improvement", 7, 4, 3, 3, 0, 0],
            [13, "+5", "—", 8, 4, 3, 3, 1, 0],
            [14, "+5", "Favored Enemy improvement, Vanish", 8, 4, 3, 3, 1, 0],
            [15, "+5", "Ranger Archetype feature", 9, 4, 3, 3, 2, 0],
            [16, "+5", "Ability Score Improvement", 9, 4, 3, 3, 2, 0],
            [17, "+6", "—", 10, 4, 3, 3, 3, 1],
            [18, "+6", "Feral Senses", 10, 4, 3, 3, 3, 1],
            [19, "+6", "Ability Score Improvement", 11, 4, 3, 3, 3, 2],
            [20, "+6", "Foe Slayer", 11, 4, 3, 3, 3, 2],
        ]

        return RawTable(
            table_id=target["id"],
            simple_name=target["simple_name"],
            page=page_num,
            headers=[
                "Level",
                "Proficiency Bonus",
                "Features",
                "Spells Known",
                "1st",
                "2nd",
                "3rd",
                "4th",
                "5th",
            ],
            rows=rows,
            extraction_method="manual",
            section=target["section"],
            notes="Half caster progression. Reference data from SRD 5.1",
        )

    def _extract_rogue_progression(
        self, target: TableTarget, page: fitz.Page, page_num: int
    ) -> RawTable:
        """Extract Rogue progression table (page 39).

        Columns: Level, Proficiency Bonus, Features, Sneak Attack
        """
        rows: list[list[str | int | float]] = [
            [1, "+2", "Expertise, Sneak Attack, Thieves' Cant", "1d6"],
            [2, "+2", "Cunning Action", "1d6"],
            [3, "+2", "Roguish Archetype", "2d6"],
            [4, "+2", "Ability Score Improvement", "2d6"],
            [5, "+3", "Uncanny Dodge", "3d6"],
            [6, "+3", "Expertise", "3d6"],
            [7, "+3", "Evasion", "4d6"],
            [8, "+3", "Ability Score Improvement", "4d6"],
            [9, "+4", "Roguish Archetype feature", "5d6"],
            [10, "+4", "Ability Score Improvement", "5d6"],
            [11, "+4", "Reliable Talent", "6d6"],
            [12, "+4", "Ability Score Improvement", "6d6"],
            [13, "+5", "Roguish Archetype feature", "7d6"],
            [14, "+5", "Blindsense", "7d6"],
            [15, "+5", "Slippery Mind", "8d6"],
            [16, "+5", "Ability Score Improvement", "8d6"],
            [17, "+6", "Roguish Archetype feature", "9d6"],
            [18, "+6", "Elusive", "9d6"],
            [19, "+6", "Ability Score Improvement", "10d6"],
            [20, "+6", "Stroke of Luck", "10d6"],
        ]

        return RawTable(
            table_id=target["id"],
            simple_name=target["simple_name"],
            page=page_num,
            headers=["Level", "Proficiency Bonus", "Features", "Sneak Attack"],
            rows=rows,
            extraction_method="manual",
            section=target["section"],
            notes="Reference data from SRD 5.1",
        )

    def _extract_sorcerer_progression(
        self, target: TableTarget, page: fitz.Page, page_num: int
    ) -> RawTable:
        """Extract Sorcerer progression table (page 42).

        Columns: Level, Proficiency Bonus, Features, Cantrips Known, Spells Known,
                 Spell Slots (1st-9th), Sorcery Points
        """
        rows: list[list[str | int | float]] = [
            [1, "+2", "Spellcasting, Sorcerous Origin", 4, 2, 2, 0, 0, 0, 0, 0, 0, 0, 0, "—"],
            [2, "+2", "Font of Magic", 4, 3, 3, 0, 0, 0, 0, 0, 0, 0, 0, 2],
            [3, "+2", "Metamagic", 4, 4, 4, 2, 0, 0, 0, 0, 0, 0, 0, 3],
            [4, "+2", "Ability Score Improvement", 5, 5, 4, 3, 0, 0, 0, 0, 0, 0, 0, 4],
            [5, "+3", "—", 5, 6, 4, 3, 2, 0, 0, 0, 0, 0, 0, 5],
            [6, "+3", "Sorcerous Origin feature", 5, 7, 4, 3, 3, 0, 0, 0, 0, 0, 0, 6],
            [7, "+3", "—", 5, 8, 4, 3, 3, 1, 0, 0, 0, 0, 0, 7],
            [8, "+3", "Ability Score Improvement", 5, 9, 4, 3, 3, 2, 0, 0, 0, 0, 0, 8],
            [9, "+4", "—", 5, 10, 4, 3, 3, 3, 1, 0, 0, 0, 0, 9],
            [10, "+4", "Metamagic", 6, 11, 4, 3, 3, 3, 2, 0, 0, 0, 0, 10],
            [11, "+4", "—", 6, 12, 4, 3, 3, 3, 2, 1, 0, 0, 0, 11],
            [12, "+4", "Ability Score Improvement", 6, 12, 4, 3, 3, 3, 2, 1, 0, 0, 0, 12],
            [13, "+5", "—", 6, 13, 4, 3, 3, 3, 2, 1, 1, 0, 0, 13],
            [14, "+5", "Sorcerous Origin feature", 6, 13, 4, 3, 3, 3, 2, 1, 1, 0, 0, 14],
            [15, "+5", "—", 6, 14, 4, 3, 3, 3, 2, 1, 1, 1, 0, 15],
            [16, "+5", "Ability Score Improvement", 6, 14, 4, 3, 3, 3, 2, 1, 1, 1, 0, 16],
            [17, "+6", "Metamagic", 6, 15, 4, 3, 3, 3, 2, 1, 1, 1, 1, 17],
            [18, "+6", "Sorcerous Origin feature", 6, 15, 4, 3, 3, 3, 3, 1, 1, 1, 1, 18],
            [19, "+6", "Ability Score Improvement", 6, 15, 4, 3, 3, 3, 3, 2, 1, 1, 1, 19],
            [20, "+6", "Sorcerous Restoration", 6, 15, 4, 3, 3, 3, 3, 2, 2, 1, 1, 20],
        ]

        return RawTable(
            table_id=target["id"],
            simple_name=target["simple_name"],
            page=page_num,
            headers=[
                "Level",
                "Proficiency Bonus",
                "Features",
                "Cantrips Known",
                "Spells Known",
                "1st",
                "2nd",
                "3rd",
                "4th",
                "5th",
                "6th",
                "7th",
                "8th",
                "9th",
                "Sorcery Points",
            ],
            rows=rows,
            extraction_method="manual",
            section=target["section"],
            notes="Reference data from SRD 5.1",
        )

    def _extract_warlock_progression(
        self, target: TableTarget, page: fitz.Page, page_num: int
    ) -> RawTable:
        """Extract Warlock progression table (page 44).

        Columns: Level, Proficiency Bonus, Features, Cantrips Known, Spells Known,
                 Spell Slots, Slot Level, Invocations Known
        Pact magic has different slot progression than full/half casters.
        """
        rows: list[list[str | int | float]] = [
            [1, "+2", "Otherworldly Patron, Pact Magic", 2, 2, 1, "1st", 0],
            [2, "+2", "Eldritch Invocations", 2, 3, 2, "1st", 2],
            [3, "+2", "Pact Boon", 2, 4, 2, "2nd", 2],
            [4, "+2", "Ability Score Improvement", 3, 5, 2, "2nd", 2],
            [5, "+3", "—", 3, 6, 2, "3rd", 3],
            [6, "+3", "Otherworldly Patron feature", 3, 7, 2, "3rd", 3],
            [7, "+3", "—", 3, 8, 2, "4th", 4],
            [8, "+3", "Ability Score Improvement", 3, 9, 2, "4th", 4],
            [9, "+4", "—", 3, 10, 2, "5th", 5],
            [10, "+4", "Otherworldly Patron feature", 4, 10, 2, "5th", 5],
            [11, "+4", "Mystic Arcanum (6th level)", 4, 11, 3, "5th", 5],
            [12, "+4", "Ability Score Improvement", 4, 11, 3, "5th", 6],
            [13, "+5", "Mystic Arcanum (7th level)", 4, 12, 3, "5th", 6],
            [14, "+5", "Otherworldly Patron feature", 4, 12, 3, "5th", 6],
            [15, "+5", "Mystic Arcanum (8th level)", 4, 13, 3, "5th", 7],
            [16, "+5", "Ability Score Improvement", 4, 13, 3, "5th", 7],
            [17, "+6", "Mystic Arcanum (9th level)", 4, 14, 4, "5th", 7],
            [18, "+6", "—", 4, 14, 4, "5th", 8],
            [19, "+6", "Ability Score Improvement", 4, 15, 4, "5th", 8],
            [20, "+6", "Eldritch Master", 4, 15, 4, "5th", 8],
        ]

        return RawTable(
            table_id=target["id"],
            simple_name=target["simple_name"],
            page=page_num,
            headers=[
                "Level",
                "Proficiency Bonus",
                "Features",
                "Cantrips Known",
                "Spells Known",
                "Spell Slots",
                "Slot Level",
                "Invocations Known",
            ],
            rows=rows,
            extraction_method="manual",
            section=target["section"],
            notes="Pact magic progression (different from full/half casters). Reference data from SRD 5.1",
        )

    def _extract_wizard_progression(
        self, target: TableTarget, page: fitz.Page, page_num: int
    ) -> RawTable:
        """Extract Wizard progression table (page 46).

        Columns: Level, Proficiency Bonus, Features, Cantrips Known, Spell Slots (1st-9th)
        Full caster progression.
        """
        rows: list[list[str | int | float]] = [
            [1, "+2", "Spellcasting, Arcane Recovery", 3, 2, 0, 0, 0, 0, 0, 0, 0, 0],
            [2, "+2", "Arcane Tradition", 3, 3, 0, 0, 0, 0, 0, 0, 0, 0],
            [3, "+2", "—", 3, 4, 2, 0, 0, 0, 0, 0, 0, 0],
            [4, "+2", "Ability Score Improvement", 4, 4, 3, 0, 0, 0, 0, 0, 0, 0],
            [5, "+3", "—", 4, 4, 3, 2, 0, 0, 0, 0, 0, 0],
            [6, "+3", "Arcane Tradition feature", 4, 4, 3, 3, 0, 0, 0, 0, 0, 0],
            [7, "+3", "—", 4, 4, 3, 3, 1, 0, 0, 0, 0, 0],
            [8, "+3", "Ability Score Improvement", 4, 4, 3, 3, 2, 0, 0, 0, 0, 0],
            [9, "+4", "—", 4, 4, 3, 3, 3, 1, 0, 0, 0, 0],
            [10, "+4", "Arcane Tradition feature", 5, 4, 3, 3, 3, 2, 0, 0, 0, 0],
            [11, "+4", "—", 5, 4, 3, 3, 3, 2, 1, 0, 0, 0],
            [12, "+4", "Ability Score Improvement", 5, 4, 3, 3, 3, 2, 1, 0, 0, 0],
            [13, "+5", "—", 5, 4, 3, 3, 3, 2, 1, 1, 0, 0],
            [14, "+5", "Arcane Tradition feature", 5, 4, 3, 3, 3, 2, 1, 1, 0, 0],
            [15, "+5", "—", 5, 4, 3, 3, 3, 2, 1, 1, 1, 0],
            [16, "+5", "Ability Score Improvement", 5, 4, 3, 3, 3, 2, 1, 1, 1, 0],
            [17, "+6", "—", 5, 4, 3, 3, 3, 2, 1, 1, 1, 1],
            [18, "+6", "Spell Mastery", 5, 4, 3, 3, 3, 3, 1, 1, 1, 1],
            [19, "+6", "Ability Score Improvement", 5, 4, 3, 3, 3, 3, 2, 1, 1, 1],
            [20, "+6", "Signature Spell", 5, 4, 3, 3, 3, 3, 2, 2, 1, 1],
        ]

        return RawTable(
            table_id=target["id"],
            simple_name=target["simple_name"],
            page=page_num,
            headers=[
                "Level",
                "Proficiency Bonus",
                "Features",
                "Cantrips Known",
                "1st",
                "2nd",
                "3rd",
                "4th",
                "5th",
                "6th",
                "7th",
                "8th",
                "9th",
            ],
            rows=rows,
            extraction_method="manual",
            section=target["section"],
            notes="Full caster progression. Reference data from SRD 5.1",
        )

    def close(self):
        """Close PDF document."""
        if self.doc:
            self.doc.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
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
            }
            for t in tables
        ]
    }

    output_path = Path(output_path)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(tables_dict, f, indent=2, ensure_ascii=False)

    logger.info(f"\nSaved {len(tables)} tables to {output_path}")


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    if len(sys.argv) < MIN_CLI_ARGS:
        print("Usage: python -m srd_builder.extract_tables <pdf_path> [output_path]")
        sys.exit(1)

    pdf_path = sys.argv[1]
    output_path = (
        sys.argv[CLI_OUTPUT_PATH_ARG_INDEX]
        if len(sys.argv) > CLI_OUTPUT_PATH_ARG_INDEX
        else "tables_raw.json"
    )

    extract_tables_to_json(pdf_path, output_path)
    print(f"\n✓ Extraction complete: {output_path}")
