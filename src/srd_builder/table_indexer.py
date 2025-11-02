#!/usr/bin/env python3
"""PDF table metadata discovery for SRD 5.1.

Scans entire PDF to generate comprehensive table metadata for validation
and extraction. Provides baseline for "did we extract all expected tables?"
and prevents per-table debugging cycles.

This is the infrastructure piece originally planned for v0.5.5, now merged
into v0.7.0 alongside reference table extraction.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF

from .constants import EXTRACTOR_VERSION

logger = logging.getLogger(__name__)


@dataclass
class TableMetadata:
    """Metadata for a discovered table."""

    page: int
    table_index: int  # Index on page (0-based)
    row_count: int
    column_count: int
    bbox: tuple[float, float, float, float]  # x0, y0, x1, y1
    headers: list[str] = field(default_factory=list)
    section_context: str | None = None
    estimated_id: str | None = None  # Best-guess ID based on content

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "page": self.page,
            "table_index": self.table_index,
            "row_count": self.row_count,
            "column_count": self.column_count,
            "bbox": list(self.bbox),
            "headers": self.headers,
            "section_context": self.section_context,
            "estimated_id": self.estimated_id,
        }


class TableIndexer:
    """Discover and catalog all tables in a PDF document."""

    def __init__(self, pdf_path: Path):
        """Initialize indexer.

        Args:
            pdf_path: Path to PDF file
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        self.pdf_path = pdf_path
        self.tables: list[TableMetadata] = []

    def discover_all_tables(
        self,
        start_page: int | None = None,
        end_page: int | None = None,
        include_equipment: bool = True,
        use_auto_detection: bool = True,
    ) -> list[TableMetadata]:
        """Scan PDF and catalog all tables.

        Args:
            start_page: Starting page (1-indexed), None = start of document
            end_page: Ending page (1-indexed), None = end of document
            include_equipment: Whether to include equipment tables (pages 62-73)
            use_auto_detection: Use PyMuPDF auto-detection (may miss simple tables)

        Returns:
            List of table metadata entries

        Note:
            PyMuPDF's find_tables() works well for grid-based tables but often
            misses simple two-column reference tables. This method reports what
            auto-detection finds. For extraction, we'll need manual patterns for
            missed tables.
        """
        logger.info(f"Discovering tables in {self.pdf_path}")

        doc = fitz.open(self.pdf_path)
        self.tables = []

        try:
            # Determine page range
            start = (start_page - 1) if start_page else 0
            end = end_page if end_page else len(doc)

            logger.info(f"Scanning pages {start + 1} to {end}")

            for page_num in range(start, end):
                page = doc[page_num]

                if use_auto_detection:
                    page_tables = self._discover_page_tables(page, page_num + 1)
                else:
                    page_tables = []

                # Filter equipment tables if requested
                if not include_equipment:
                    equipment_pages = set(range(62, 74))  # Pages 62-73 (1-indexed)
                    page_tables = [t for t in page_tables if t.page not in equipment_pages]

                self.tables.extend(page_tables)

            logger.info(
                f"Discovered {len(self.tables)} tables "
                f"(auto-detection={'enabled' if use_auto_detection else 'disabled'})"
            )

        finally:
            doc.close()

        return self.tables

    def _discover_page_tables(self, page: fitz.Page, page_num: int) -> list[TableMetadata]:
        """Discover all tables on a single page.

        Args:
            page: PyMuPDF page object
            page_num: Page number (1-indexed)

        Returns:
            List of table metadata for this page
        """
        page_tables = []

        try:
            table_finder = page.find_tables()

            # Get section context from page headers
            section_context = self._extract_section_context(page)

            for table_idx, table in enumerate(table_finder.tables):
                rows = table.extract()

                if not rows or len(rows) < 2:  # Need at least header + 1 data row
                    continue

                # Extract headers (first row)
                headers = [str(cell).strip() for cell in rows[0]]

                # Determine column count
                column_count = len(headers)

                # Create metadata entry
                metadata = TableMetadata(
                    page=page_num,
                    table_index=table_idx,
                    row_count=len(rows) - 1,  # Exclude header row
                    column_count=column_count,
                    bbox=table.bbox,
                    headers=headers,
                    section_context=section_context,
                    estimated_id=self._estimate_table_id(headers, section_context),
                )

                page_tables.append(metadata)

                logger.debug(
                    f"Page {page_num}, Table {table_idx}: "
                    f"{metadata.row_count} rows, {column_count} cols, "
                    f"headers={headers[:3]}..."
                )

        except Exception as e:
            logger.warning(f"Page {page_num}: Failed to discover tables - {e}")

        return page_tables

    def _extract_section_context(self, page: fitz.Page) -> str | None:
        """Extract section/chapter context from page.

        Looks for large headers (18pt+) that indicate section names.

        Args:
            page: PyMuPDF page object

        Returns:
            Section name or None
        """
        try:
            blocks = page.get_text("dict")["blocks"]

            for block in blocks:
                if block.get("type") != 0:  # Only text blocks
                    continue

                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        size = span.get("size", 0)
                        text = span.get("text", "").strip()

                        # Large headers (18pt+) are usually section markers
                        if size >= 18.0 and len(text) > 3:
                            return text

        except Exception as e:
            logger.debug(f"Failed to extract section context: {e}")

        return None

    def _estimate_table_id(self, headers: list[str], section_context: str | None) -> str | None:
        """Estimate table ID based on content heuristics.

        Args:
            headers: Table column headers
            section_context: Section/chapter name

        Returns:
            Estimated ID or None
        """
        if not headers:
            return None

        # Normalize headers for matching
        normalized = [h.lower().strip() for h in headers]
        header_text = " ".join(normalized)

        # Pattern matching for known tables
        patterns = {
            "experience_by_cr": ["challenge", "rating", "xp", "experience"],
            "proficiency_bonus": ["level", "proficiency", "bonus"],
            "ability_scores": ["ability", "score", "modifier"],
            "spell_slots": ["level", "slot", "1st", "2nd", "3rd"],
            "cantrip_damage": ["cantrip", "damage", "level"],
            "travel_pace": ["pace", "distance", "hour", "day"],
            "services": ["service", "cost", "pay"],
            "creature_size": ["size", "space", "category"],
            "armor": ["armor", "cost", "ac", "class"],
            "weapon": ["weapon", "damage", "properties"],
        }

        for table_id, keywords in patterns.items():
            # Check if multiple keywords appear in headers
            matches = sum(1 for kw in keywords if kw in header_text)
            if matches >= 2:  # At least 2 keywords match
                return table_id

        return None

    def generate_report(self) -> dict[str, Any]:
        """Generate summary report of discovered tables.

        Returns:
            Dictionary with statistics and table list
        """
        # Group tables by page
        by_page: dict[int, list[TableMetadata]] = {}
        for table in self.tables:
            by_page.setdefault(table.page, []).append(table)

        # Group by estimated ID
        by_id: dict[str, list[TableMetadata]] = {}
        for table in self.tables:
            table_id = table.estimated_id or "unknown"
            by_id.setdefault(table_id, []).append(table)

        return {
            "total_tables": len(self.tables),
            "pages_with_tables": len(by_page),
            "page_range": ((min(by_page.keys()), max(by_page.keys())) if by_page else (0, 0)),
            "tables_by_page": {page: len(tables) for page, tables in sorted(by_page.items())},
            "tables_by_id": {table_id: len(tables) for table_id, tables in sorted(by_id.items())},
            "tables": [t.to_dict() for t in self.tables],
        }

    def generate_page_index_for_meta(
        self, extracted_table_ids: list[str] | None = None
    ) -> dict[str, Any]:
        """Generate page index data for meta.json provenance tracking.

        This provides a comprehensive map of where all content types are
        located in the source PDF. Useful for:
        - Provenance: "Where did this data come from?"
        - Version comparison: "What changed between SRD 5.1 and 5.2.1?"
        - Quality assurance: "Did we extract from all expected pages?"

        Args:
            extracted_table_ids: List of table IDs that were successfully extracted.
                If provided, only these tables will be included in reference_tables.
                If None, all TARGET_TABLES will be included.

        Returns:
            Dictionary suitable for meta.json page_index field
        """
        # Known page ranges from extraction modules
        page_index = {
            "monsters": {
                "start": 261,
                "end": 394,
                "description": "Monster stat blocks (A-Z)",
            },
            "equipment": {
                "start": 62,
                "end": 73,
                "description": "Equipment tables (armor, weapons, gear, mounts)",
            },
            "spells_list": {
                "start": 105,
                "end": 113,
                "description": "Spell lists by class",
            },
            "spells_descriptions": {
                "start": 114,
                "end": 194,
                "description": "Spell descriptions (A-Z)",
            },
        }

        # Add reference tables from target list
        reference_tables = []
        try:
            try:
                from scripts.table_targets import TARGET_TABLES
            except ModuleNotFoundError:
                import sys
                from pathlib import Path

                sys.path.insert(0, str(Path(__file__).parent.parent.parent))
                from scripts.table_targets import TARGET_TABLES

            for target in TARGET_TABLES:
                # Skip tables that weren't successfully extracted
                if extracted_table_ids is not None and target["id"] not in extracted_table_ids:
                    continue

                page = target["page"]
                if isinstance(page, list):
                    page_str = f"{page[0]}-{page[-1]}"
                else:
                    page_str = str(page)

                reference_tables.append(
                    {
                        "id": target["id"],
                        "name": target["name"],
                        "page": page_str,
                        "category": target["category"],
                    }
                )
        except ImportError:
            logger.warning("Could not import TARGET_TABLES for page index")

        if reference_tables:
            page_index["reference_tables"] = reference_tables

        return page_index

    def check_target_coverage(self, target_pages: list[int]) -> dict[str, list[int]]:
        """Check which target pages have discovered tables.

        Args:
            target_pages: List of page numbers to check

        Returns:
            Dict with 'found' and 'missing' page lists
        """
        discovered_pages = {t.page for t in self.tables}

        found = [p for p in target_pages if p in discovered_pages]
        missing = [p for p in target_pages if p not in discovered_pages]

        return {
            "found": sorted(found),
            "missing": sorted(missing),
            "coverage_percent": (len(found) / len(target_pages) * 100) if target_pages else 0,
        }

    def save_metadata(self, output_path: Path) -> None:
        """Save table metadata to JSON file.

        Args:
            output_path: Path for output JSON file
        """
        import json

        report = self.generate_report()

        # Add metadata
        report["_meta"] = {
            "indexer_version": EXTRACTOR_VERSION,
            "source_pdf": str(self.pdf_path),
        }

        output_path.write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )

        logger.info(f"Saved table metadata to {output_path}")


def discover_tables(
    pdf_path: Path,
    start_page: int | None = None,
    end_page: int | None = None,
    include_equipment: bool = True,
) -> dict[str, Any]:
    """Convenience function to discover tables and return report.

    Args:
        pdf_path: Path to PDF file
        start_page: Starting page (1-indexed)
        end_page: Ending page (1-indexed)
        include_equipment: Whether to include equipment tables

    Returns:
        Report dictionary with table metadata
    """
    indexer = TableIndexer(pdf_path)
    indexer.discover_all_tables(start_page, end_page, include_equipment)
    return indexer.generate_report()


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)

    pdf_path = Path("rulesets/srd_5_1/raw/SRD_CC_v5.1.pdf")

    if not pdf_path.exists():
        print(f"Error: PDF not found at {pdf_path}")
        sys.exit(1)

    print("=" * 80)
    print("SRD 5.1 Table Discovery (Auto-Detection Baseline)")
    print("=" * 80)
    print()
    print("NOTE: PyMuPDF's find_tables() works well for grid-based tables")
    print("but often misses simple two-column reference tables.")
    print("This report shows what auto-detection finds.")
    print()

    # Discover all tables
    indexer = TableIndexer(pdf_path)
    indexer.discover_all_tables()

    # Generate report
    report = indexer.generate_report()

    print(f"Total tables discovered: {report['total_tables']}")
    print(f"Pages with tables: {report['pages_with_tables']}")
    print(f"Page range: {report['page_range'][0]}-{report['page_range'][1]}")
    print()

    # Check target coverage
    target_pages = [7, 15, 57, 201, 242, 158, 159, 191, 176, 157]
    coverage = indexer.check_target_coverage(target_pages)

    print("Target Table Coverage:")
    print(f"  Found: {len(coverage['found'])}/{len(target_pages)} pages")
    print(f"  Coverage: {coverage['coverage_percent']:.1f}%")
    print(f"  Missing pages: {coverage['missing']}")
    print()
    print("✓ This validates why we need manual patterns for simple tables!")
    print()

    print("Tables by estimated ID:")
    for table_id, count in sorted(report["tables_by_id"].items()):
        print(f"  {table_id}: {count} table(s)")

    print()
    print("Sample discovered tables:")
    for table in report["tables"][:10]:
        print(f"  Page {table['page']}, Table {table['table_index']}:")
        print(f"    Rows: {table['row_count']}, Cols: {table['column_count']}")
        print(f"    Headers: {table['headers'][:4]}...")
        print(f"    Estimated ID: {table['estimated_id']}")
        print()

    # Save full report
    output_path = Path("table_metadata.json")
    indexer.save_metadata(output_path)
    print(f"\nFull metadata saved to {output_path}")
