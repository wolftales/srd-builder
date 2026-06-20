"""Extract authoritative metadata from SRD PDF first page.

The first page of the SRD PDF contains all the official metadata:
- Document title and version
- License information
- Attribution requirements
- Official URLs

This module extracts that metadata to populate meta.json accurately.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from srd_builder.utils.pdf_probe import open_pdf, page_text

# Title + version: matches "System Reference Document 5.1". Run against
# whitespace-normalized text because the PDF wraps the title across lines.
_TITLE_RE = re.compile(r"System Reference Document\s+([\d.]+)")

# License clause: 'Creative Commons Attribution 4.0 International License
# ("CC-BY-4.0")'. Run against raw (un-normalized) page text — tolerant of
# the embedded newlines, and the quoted shortcode survives intact.
_LICENSE_RE = re.compile(
    r'Creative Commons\s+Attribution\s+([\d.]+)\s+International License\s*\("([^"]+)"\)',
)

_LICENSE_URL_RE = re.compile(r"https://creativecommons\.org/licenses/by/[\d.]+/legalcode")

_OFFICIAL_URL_RE = re.compile(r"https://dnd\.wizards\.com/resources/systems-reference-document")

# Attribution paragraph: "This work includes material taken from … legalcode."
# DOTALL because the paragraph spans multiple newlines in raw page text.
_ATTRIBUTION_RE = re.compile(
    r"(This work includes material taken from"
    r".*?https://creativecommons\.org/licenses/by/[\d.]+/legalcode\.)",
    re.DOTALL,
)

_WS_COLLAPSE = re.compile(r"\s+")


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
        - pdf_title / pdf_author / pdf_subject / pdf_creator /
          pdf_producer / pdf_creation_date / pdf_mod_date:
          Embedded XMP properties (empty strings for the shipped SRD,
          which carries no XMP metadata; kept in the contract so callers
          can rely on the keys being present).
    """
    with open_pdf(pdf_path) as doc:
        # Raw text preserves newlines for the DOTALL attribution match
        # and the line-tolerant license/URL regexes.
        raw_text = page_text(doc, 0, normalize=False)
        # Normalized text for the title regex (the SRD wraps the title
        # across lines, so a single-space form is what matches).
        normalized = _WS_COLLAPSE.sub(" ", raw_text)

        title_match = _TITLE_RE.search(normalized)
        title = title_match.group(0) if title_match else None
        version = title_match.group(1) if title_match else None

        license_match = _LICENSE_RE.search(raw_text)
        license_type = license_match.group(2) if license_match else "CC-BY-4.0"

        license_url_match = _LICENSE_URL_RE.search(raw_text)
        license_url = license_url_match.group(0) if license_url_match else None

        official_url_match = _OFFICIAL_URL_RE.search(raw_text)
        official_url = official_url_match.group(0) if official_url_match else None

        attribution: str | None = None
        attribution_match = _ATTRIBUTION_RE.search(raw_text)
        if attribution_match:
            attribution = _WS_COLLAPSE.sub(" ", attribution_match.group(1)).strip()

        pdf_doc_meta = doc.metadata

        return {
            "title": title,
            "version": version,
            "license_type": license_type,
            "license_url": license_url,
            "official_url": official_url,
            "attribution": attribution,
            "filename": pdf_path.name,
            "pdf_title": pdf_doc_meta.get("title"),
            "pdf_author": pdf_doc_meta.get("author"),
            "pdf_subject": pdf_doc_meta.get("subject"),
            "pdf_creator": pdf_doc_meta.get("creator"),
            "pdf_producer": pdf_doc_meta.get("producer"),
            "pdf_creation_date": pdf_doc_meta.get("creationDate"),
            "pdf_mod_date": pdf_doc_meta.get("modDate"),
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
