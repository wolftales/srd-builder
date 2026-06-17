"""Extract authoritative metadata from SRD PDF first page.

The first page of the SRD PDF contains all the official metadata:
- Document title and version
- License information
- Attribution requirements
- Official URLs

This module extracts that metadata to populate meta.json accurately.
"""

import re
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF


def extract_pdf_metadata(pdf_path: Path) -> dict[str, Any]:
    """Extract metadata from PDF first page and document properties.

    Args:
        pdf_path: Path to SRD PDF

    Returns:
        Dictionary with:
        - title: Document title (e.g., "System Reference Document 5.1")
        - version: Version string (e.g., "5.1")
        - license_type: License identifier (e.g., "CC-BY-4.0")
        - license_url: Full license URL
        - official_url: Official document URL
        - attribution: Required attribution text
        - filename: PDF filename
    """
    with fitz.open(pdf_path) as doc:
        # Extract text from first page
        first_page = doc[0]
        page_text = first_page.get_text()

        # Normalize whitespace for easier regex matching
        normalized_text = re.sub(r"\s+", " ", page_text)

        # Extract title and version from "System Reference Document 5.1"
        title_match = re.search(r"System Reference Document\s+([\d.]+)", normalized_text)
        title = title_match.group(0) if title_match else None
        version = title_match.group(1) if title_match else None

        # Extract license type
        license_match = re.search(
            r'Creative Commons\s+Attribution\s+([\d.]+)\s+International License\s*\("([^"]+)"\)',
            page_text,
        )
        license_type = license_match.group(2) if license_match else "CC-BY-4.0"

        # Extract license URL
        license_url_match = re.search(
            r"https://creativecommons\.org/licenses/by/[\d.]+/legalcode", page_text
        )
        license_url = license_url_match.group(0) if license_url_match else None

        # Extract official URL
        official_url_match = re.search(
            r"https://dnd\.wizards\.com/resources/systems-reference-document", page_text
        )
        official_url = official_url_match.group(0) if official_url_match else None

        # Extract attribution text (the paragraph starting with "This work includes")
        attribution_match = re.search(
            r"(This work includes material taken from.*?https://creativecommons\.org/licenses/by/[\d.]+/legalcode\.)",
            page_text,
            re.DOTALL,
        )
        attribution = None
        if attribution_match:
            # Clean up the attribution text (remove line breaks, extra spaces)
            attribution = re.sub(r"\s+", " ", attribution_match.group(1)).strip()

        # Get PDF document properties
        pdf_metadata = doc.metadata

        return {
            "title": title,
            "version": version,
            "license_type": license_type,
            "license_url": license_url,
            "official_url": official_url,
            "attribution": attribution,
            "filename": pdf_path.name,
            # Additional PDF properties
            "pdf_title": pdf_metadata.get("title"),
            "pdf_author": pdf_metadata.get("author"),
            "pdf_subject": pdf_metadata.get("subject"),
            "pdf_creator": pdf_metadata.get("creator"),
            "pdf_producer": pdf_metadata.get("producer"),
            "pdf_creation_date": pdf_metadata.get("creationDate"),
            "pdf_mod_date": pdf_metadata.get("modDate"),
        }


def main() -> None:
    """CLI entry point for testing."""
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Extract metadata from SRD PDF")
    parser.add_argument("pdf", type=Path, help="Path to SRD PDF")

    args = parser.parse_args()

    metadata = extract_pdf_metadata(args.pdf)
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
