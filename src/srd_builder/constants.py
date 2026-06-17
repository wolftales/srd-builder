"""Shared constants for srd-builder.

Centralized constants used across multiple modules to avoid circular imports.
"""

from typing import Final

# Package version: defined in __init__.py, imported from there
# from . import __version__

# Extractor version: Raw extraction format for *_raw.json files
# Tracks PDF extraction structure across all entity types (monsters, equipment, spells, etc.)
# Bump when raw extraction format changes (new metadata, structural changes)
# v0.4.0: Added font metadata blocks (header_blocks/description_blocks) for spells
EXTRACTOR_VERSION: Final = "0.4.0"

# Data source identifier
#
# TODO(v0.27+): graduate to per-ruleset config under
# rulesets/<ruleset>/config.py once a second ruleset (e.g. SRD 5.2) is
# actually available to test against. Doing it now would require
# threading a ruleset id through every parser/postprocessor purely
# for a single string, with no second ruleset to validate the
# abstraction against — premature abstraction.
DATA_SOURCE: Final = "SRD_CC_v5.1"

# Directory names
RULESETS_DIRNAME: Final = "rulesets"
DIST_DIRNAME: Final = "dist"
SCHEMAS_DIRNAME: Final = "schemas"
EXEMPLARS_DIRNAME: Final = "exemplars"
