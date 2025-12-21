#!/usr/bin/env python3
"""Generic prose section extractor for SRD PDF.

This script helps discover and extract prose sections (conditions, diseases,
madness, etc.) that follow similar patterns:
- Named sections with headers
- Bullet-pointed effects/rules
- Optional tables or structured data
- Cross-references between sections

Use this to accelerate new dataset extraction by generating starter code.
"""

import argparse
import json
import re
from pathlib import Path
from typing import Any

import fitz


def clean_pdf_text(text: str) -> str:
    """Clean up common PDF encoding issues.

    Args:
        text: Raw text from PDF

    Returns:
        Cleaned text
    """
    # Fix common PDF encoding issues
    text = text.replace("­‐‑", "-")  # Replace garbled dashes
    text = text.replace("­‐", "-")
    text = text.replace("‑", "-")
    text = text.replace("\n", " ")  # Normalize newlines
    text = re.sub(r"\s+", " ", text)  # Collapse whitespace
    return text.strip()


def extract_bullet_points(text: str) -> list[str]:
    """Extract bullet points from text.

    Args:
        text: Text containing bullet points

    Returns:
        List of bullet point strings
    """
    # Look for bullet points marked with •
    bullets = re.findall(r"•\s*([^•]+)", text)
    if bullets:
        return [bullet.strip() for bullet in bullets if bullet.strip()]

    # Alternative: look for numbered lists
    numbered = re.findall(r"^\d+\.\s+([^\d]+?)(?=\d+\.|$)", text, re.MULTILINE)
    if numbered:
        return [item.strip() for item in numbered if item.strip()]

    return []


def extract_table_rows(text: str, column_count: int = 2) -> list[dict[str, str]]:
    """Attempt to extract table data from text.

    Args:
        text: Text potentially containing a table
        column_count: Expected number of columns

    Returns:
        List of row dictionaries (best effort)
    """
    rows = []

    # Look for "Level Effect" style tables
    if "Level" in text and "Effect" in text:
        # Extract level/effect pairs
        pattern = r"(\d+)\s+([A-Z][^0-9]+?)(?=\d+\s+[A-Z]|$)"
        matches = re.findall(pattern, text)
        for level, effect in matches:
            rows.append({"level": level.strip(), "effect": effect.strip()})

    return rows


def discover_sections(
    pdf_path: Path,
    start_page: int,
    end_page: int,
    known_headers: list[str] | None = None,
    header_pattern: str | None = None,
) -> list[dict[str, Any]]:
    """Discover and extract prose sections from PDF pages.

    Args:
        pdf_path: Path to PDF file
        start_page: First page to scan (1-indexed)
        end_page: Last page to scan (1-indexed)
        known_headers: List of known section headers to look for
        header_pattern: Regex pattern for detecting headers (alternative to known_headers)

    Returns:
        List of discovered sections with metadata
    """
    doc = fitz.open(pdf_path)
    sections = []

    # Extract full text from page range
    full_text = ""
    for page_num in range(start_page - 1, end_page):
        page = doc[page_num]
        full_text += page.get_text()

    doc.close()

    # Clean text
    full_text = clean_pdf_text(full_text)

    # If known headers provided, use boundary detection
    if known_headers:
        for i, header in enumerate(known_headers):
            # Find this header
            pattern = rf"\b{re.escape(header)}\b"
            match = re.search(pattern, full_text, re.IGNORECASE)

            if not match:
                continue

            start_pos = match.start()

            # Find next header (or end of text)
            end_pos = len(full_text)
            if i + 1 < len(known_headers):
                next_header = known_headers[i + 1]
                next_match = re.search(
                    rf"\b{re.escape(next_header)}\b",
                    full_text[start_pos + len(header) :],
                    re.IGNORECASE,
                )
                if next_match:
                    end_pos = start_pos + len(header) + next_match.start()

            # Extract section text
            section_text = full_text[start_pos:end_pos].strip()

            # Analyze section structure
            bullets = extract_bullet_points(section_text)
            tables = extract_table_rows(section_text)

            sections.append(
                {
                    "name": header,
                    "raw_text": (
                        section_text[:500] + "..." if len(section_text) > 500 else section_text
                    ),
                    "text_length": len(section_text),
                    "has_bullets": len(bullets) > 0,
                    "bullet_count": len(bullets),
                    "has_table": len(tables) > 0,
                    "table_rows": len(tables),
                    "sample_bullets": bullets[:3] if bullets else None,
                    "sample_table": tables[:2] if tables else None,
                }
            )

    # If header pattern provided, discover headers dynamically
    elif header_pattern:
        matches = re.finditer(header_pattern, full_text)
        for match in matches:
            header = match.group(0)
            sections.append(
                {
                    "name": header,
                    "position": match.start(),
                    "context": full_text[max(0, match.start() - 50) : match.end() + 100],
                }
            )

    return sections


def generate_extraction_template(
    sections: list[dict[str, Any]],
    dataset_name: str,
    pages: tuple[int, int],
) -> str:
    """Generate Python code template for extraction module.

    Args:
        sections: Discovered sections from discover_sections()
        dataset_name: Name of dataset (e.g., "conditions", "diseases")
        pages: Page range tuple (start, end)

    Returns:
        Python code as string
    """
    section_names = [s["name"] for s in sections]

    template = f'''#!/usr/bin/env python3
"""PDF {dataset_name} extraction for SRD 5.1.

Extracts raw {dataset_name} entries from pages {pages[0]}-{pages[1]}.
Outputs verbatim text with metadata for downstream parsing.

Auto-generated template from extract_prose_sections.py
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import fitz

from .constants import EXTRACTOR_VERSION

# {dataset_name.title()} pages
{dataset_name.upper()}_START_PAGE = {pages[0]}
{dataset_name.upper()}_END_PAGE = {pages[1]}

# Known {dataset_name} names from SRD 5.1
{dataset_name.upper()}_NAMES = {json.dumps(section_names, indent=4)}


@dataclass
class ExtractionConfig:
    """Configuration for PDF {dataset_name} extraction."""

    page_start: int = {dataset_name.upper()}_START_PAGE
    page_end: int = {dataset_name.upper()}_END_PAGE
    expected_count: int = {len(sections)}


def extract_{dataset_name}(pdf_path: Path) -> dict[str, Any]:
    """Extract {dataset_name} from SRD PDF.

    Args:
        pdf_path: Path to SRD PDF file

    Returns:
        Dictionary with:
            - {dataset_name}: list of raw {dataset_name} dicts
            - _meta: extraction metadata
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {{pdf_path}}")

    config = ExtractionConfig()

    # Calculate PDF hash for provenance
    pdf_bytes = pdf_path.read_bytes()
    pdf_hash = hashlib.sha256(pdf_bytes).hexdigest()

    doc = fitz.open(pdf_path)
    {dataset_name}_list: list[dict[str, Any]] = []
    warnings: list[str] = []

    try:
        # Extract raw text from pages
        full_text = ""
        for page_num in range(config.page_start - 1, config.page_end):
            page = doc[page_num]
            full_text += page.get_text()

        # Extract individual {dataset_name}
        {dataset_name}_list = _extract_from_text(full_text, config, warnings)

        if len({dataset_name}_list) < config.expected_count:
            warnings.append(
                f"Only extracted {{len({dataset_name}_list)}} {dataset_name}, expected {{config.expected_count}}"
            )

    finally:
        doc.close()

    return {{
        "{dataset_name}": {dataset_name}_list,
        "_meta": {{
            "pdf_filename": pdf_path.name,
            "extractor_version": EXTRACTOR_VERSION,
            "pdf_sha256": pdf_hash,
            "pages_processed": config.page_end - config.page_start + 1,
            "{dataset_name}_count": len({dataset_name}_list),
            "total_warnings": len(warnings),
            "warnings": warnings,
        }},
    }}


def _extract_from_text(
    text: str, config: ExtractionConfig, warnings: list[str]
) -> list[dict[str, Any]]:
    """Extract entries from raw PDF text.

    Args:
        text: Raw text from PDF pages
        config: Extraction configuration
        warnings: List to append warnings to

    Returns:
        List of raw dictionaries
    """
    items = []

    # Clean up text
    text = re.sub(r"\\s+", " ", text)

    # Split by known names to find boundaries
    for i, name in enumerate({dataset_name.upper()}_NAMES):
        pattern = rf"\\b{{name}}\\b"
        match = re.search(pattern, text, re.IGNORECASE)

        if not match:
            warnings.append(f"Could not find: {{name}}")
            continue

        start_pos = match.start()

        # Find next entry (or end of text)
        end_pos = len(text)
        if i + 1 < len({dataset_name.upper()}_NAMES):
            next_name = {dataset_name.upper()}_NAMES[i + 1]
            next_match = re.search(rf"\\b{{next_name}}\\b", text[start_pos + len(name):])
            if next_match:
                end_pos = start_pos + len(name) + next_match.start()

        # Extract text
        item_text = text[start_pos:end_pos].strip()

        items.append({{
            "name": name,
            "raw_text": item_text,
            "pages": [config.page_start, config.page_end],
        }})

    return items


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m srd_builder.extract_{dataset_name} <pdf_path>")
        sys.exit(1)

    pdf_path = Path(sys.argv[1])
    result = extract_{dataset_name}(pdf_path)
    print(json.dumps(result, indent=2, ensure_ascii=False))
'''

    return template


def main():
    """Command-line interface."""
    parser = argparse.ArgumentParser(
        description="Discover prose sections in SRD PDF and generate extraction templates"
    )
    parser.add_argument("pdf", type=Path, help="Path to SRD PDF")
    parser.add_argument("start_page", type=int, help="Starting page (1-indexed)")
    parser.add_argument("end_page", type=int, help="Ending page (1-indexed)")
    parser.add_argument(
        "--headers",
        nargs="+",
        help="Known section headers (e.g., 'Blinded' 'Charmed')",
    )
    parser.add_argument(
        "--pattern",
        help="Regex pattern to discover headers (alternative to --headers)",
    )
    parser.add_argument(
        "--dataset",
        required=True,
        help="Dataset name (e.g., 'conditions', 'diseases')",
    )
    parser.add_argument(
        "--generate-template",
        action="store_true",
        help="Generate extraction module template",
    )

    args = parser.parse_args()

    # Discover sections
    sections = discover_sections(
        args.pdf,
        args.start_page,
        args.end_page,
        known_headers=args.headers,
        header_pattern=args.pattern,
    )

    print(f"Discovered {len(sections)} sections:")
    print(json.dumps(sections, indent=2))

    # Generate template if requested
    if args.generate_template and sections:
        print("\n" + "=" * 80)
        print("GENERATED EXTRACTION TEMPLATE:")
        print("=" * 80 + "\n")
        template = generate_extraction_template(
            sections,
            args.dataset,
            (args.start_page, args.end_page),
        )
        print(template)

        # Optionally save to file
        output_path = Path(f"src/srd_builder/extract_{args.dataset}.py")
        if not output_path.exists():
            output_path.write_text(template, encoding="utf-8")
            print(f"\n✅ Template saved to: {output_path}")


if __name__ == "__main__":
    main()
