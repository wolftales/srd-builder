# Prose Extraction Framework

## Overview

The `prose_extraction.py` module provides reusable components for extracting structured prose sections from the SRD PDF. Use these helpers when creating new `extract_*.py` modules for datasets like conditions, diseases, madness, etc.

## Core Components

### 1. Text Cleaning

```python
from srd_builder.prose_extraction import clean_pdf_text

text = clean_pdf_text(raw_pdf_text)
# Fixes: garbled dashes, smart quotes, whitespace, encoding issues
```

### 2. Bullet Point Extraction

```python
from srd_builder.prose_extraction import extract_bullet_points

effects = extract_bullet_points(text)
# Supports: •, numbered lists (1. 2. 3.), dashed lists (-)
```

### 3. Table Extraction

```python
from srd_builder.prose_extraction import extract_level_effect_table

# For "Level Effect" style tables (conditions, diseases)
levels = extract_level_effect_table(text)
# Returns: [{"level": "1", "effect": "..."},  ...]

# Or use custom pattern:
from srd_builder.prose_extraction import extract_table_by_pattern

pattern = r"(\d+)\s+([A-Z][^0-9]+?)(?=\d+|$)"
rows = extract_table_by_pattern(text, pattern, ["level", "effect"])
```

### 4. Section Splitting

```python
from srd_builder.prose_extraction import split_by_known_headers

# When you know the section names:
headers = ["Blinded", "Charmed", "Deafened"]
sections = split_by_known_headers(full_text, headers)
# Returns: [{"name": "...", "raw_text": "...", "start_pos": ..., "end_pos": ...}, ...]
```

### 5. ProseExtractor Class (Recommended)

The easiest way to extract prose sections with known headers:

```python
from srd_builder.prose_extraction import ProseExtractor

# Configure extractor
extractor = ProseExtractor(
    section_name="disease",  # For error messages
    known_headers=["Cackle Fever", "Sewer Plague", "Sight Rot"],
    start_page=199,
    end_page=200,
)

# Extract from PDF
sections, warnings = extractor.extract_from_pdf(pdf_path)

# Each section has:
# - name: Header text
# - raw_text: Full section text
# - start_pos, end_pos: Position in original text
```

## Quick Start: New Dataset Extraction

### Step 1: Identify the Pattern

1. **Pages**: Which pages contain the data? (e.g., 199-200)
2. **Headers**: Are section names known? (e.g., disease names)
3. **Structure**: Bullet points? Tables? Prose?

### Step 2: Create `extract_<dataset>.py`

```python
#!/usr/bin/env python3
"""PDF disease extraction for SRD 5.1."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from .constants import EXTRACTOR_VERSION
from .prose_extraction import ProseExtractor

# Dataset configuration
DISEASE_START_PAGE = 199
DISEASE_END_PAGE = 200
DISEASE_NAMES = ["Cackle Fever", "Sewer Plague", "Sight Rot"]


def extract_diseases(pdf_path: Path) -> dict[str, Any]:
    """Extract diseases from SRD PDF."""
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    # Calculate PDF hash
    pdf_hash = hashlib.sha256(pdf_path.read_bytes()).hexdigest()

    # Use ProseExtractor framework
    extractor = ProseExtractor(
        section_name="disease",
        known_headers=DISEASE_NAMES,
        start_page=DISEASE_START_PAGE,
        end_page=DISEASE_END_PAGE,
    )

    sections, warnings = extractor.extract_from_pdf(pdf_path)

    # Convert to output format
    diseases = [
        {
            "name": section["name"],
            "raw_text": section["raw_text"],
            "pages": [DISEASE_START_PAGE, DISEASE_END_PAGE],
        }
        for section in sections
    ]

    return {
        "diseases": diseases,
        "_meta": {
            "pdf_filename": pdf_path.name,
            "extractor_version": EXTRACTOR_VERSION,
            "pdf_sha256": pdf_hash,
            "disease_count": len(diseases),
            "total_warnings": len(warnings),
            "warnings": warnings,
        },
    }
```

### Step 3: Create `parse_<dataset>.py`

Use the cleaning helpers:

```python
from srd_builder.prose_extraction import (
    clean_pdf_text,
    extract_bullet_points,
    generate_summary,
)

def parse_disease_records(raw_diseases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Parse raw disease extractions into structured records."""
    parsed = []

    for raw in raw_diseases:
        name = raw["name"]
        text = clean_pdf_text(raw["raw_text"])

        # Extract structure
        effects = extract_bullet_points(text)
        summary = generate_summary(text)

        parsed.append({
            "id": f"disease:{name.lower().replace(' ', '_')}",
            "name": name,
            "summary": summary,
            "effects": effects,
            "page": raw["pages"][0],
            "source": "SRD 5.1",
        })

    return parsed
```

## Real Example: Conditions

See `src/srd_builder/extract_conditions.py` for a complete working example showing:
- ProseExtractor usage
- PDF hash calculation
- Metadata generation
- Integration with build pipeline

## Advanced: Font-Based Header Discovery

When you don't know section names but can identify them by font:

```python
from srd_builder.prose_extraction import discover_headers_by_font

doc = fitz.open(pdf_path)
page = doc[page_num]

# Find all text in 12pt Calibri-Bold (typical monster names)
headers = discover_headers_by_font(
    page,
    font_name="Calibri-Bold",
    font_size=12.0,
    tolerance=0.5,
)

# Returns: [("Monster Name", y_position), ...]
```

## Benefits

1. **Consistency**: All prose extractions follow the same pattern
2. **Reusability**: Common operations are centralized
3. **Maintainability**: Fix PDF encoding issues in one place
4. **Speed**: New extractions take 5-10 minutes instead of hours
5. **Quality**: Battle-tested patterns from conditions, monsters, spells

## Related Files

- `src/srd_builder/prose_extraction.py` - Framework implementation
- `src/srd_builder/extract_conditions.py` - Reference implementation
- `src/srd_builder/parse_conditions.py` - Parsing example
- `scripts/extract_prose_sections.py` - Discovery/prototyping tool
