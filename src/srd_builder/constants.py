"""Shared constants for srd-builder.

Centralized constants used across multiple modules to avoid circular imports.
"""

from typing import Final

# Package version: defined in __init__.py, imported from there
# from . import __version__

# Extractor version: Raw extraction format for *_raw.json files
# Tracks PDF extraction structure across all entity types (monsters, equipment, spells, etc.)
# Bump when raw extraction format changes (new metadata, structural changes)
EXTRACTOR_VERSION: Final = "0.3.0"

# Schema version: JSON Schema validation rules
# Bump when output data structure changes
SCHEMA_VERSION: Final = "1.4.0"

# Data source identifier
DATA_SOURCE: Final = "SRD_CC_v5.1"

# Directory names
RULESETS_DIRNAME: Final = "rulesets"
