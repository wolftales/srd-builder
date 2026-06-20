"""Shared constants for srd-builder.

Centralized constants used across multiple modules to avoid circular imports.
"""

from typing import Any, Final

# Package version: defined in __init__.py, imported from there
# from . import __version__

# Extractor version: Raw extraction format for *_raw.json files
# Tracks PDF extraction structure across all entity types (monsters, equipment, spells, etc.)
# Bump when raw extraction format changes (new metadata, structural changes)
# v0.4.0: Added font metadata blocks (header_blocks/description_blocks) for spells
EXTRACTOR_VERSION: Final = "0.4.0"

# Per-ruleset identity registry.
#
# A ruleset has multiple identifiers serving different consumers:
# - id              — programmatic slug. Used as the --ruleset CLI arg
#                     and filesystem dir name (rulesets/<id>/, dist/<id>/).
# - source_id       — canonical upstream identifier. Stamped on every
#                     record's "source" field. Matches the official
#                     download filename root (e.g. SRD_CC_v5.1).
# - display_name    — user/UI long form ("D&D 5e (2014 SRD)").
# - edition_short   — user/UI short alias ("5e", "2014").
# - ruleset_version — semver-ish ruleset version string ("5.1").
# - pdf_filename    — expected raw PDF filename in rulesets/<id>/.
# - game_system     — game-system identifier (v0.29.3 Phase 5.1). Distinct
#                     from `source_id` (which is "which printing") and from
#                     `id` (which is "which slug"). Two rulesets can share a
#                     game system (e.g. srd_5_1 and srd_5_2_1 are both
#                     "dnd5e"). Future Pathfinder/Cypher/etc. rulesets
#                     would set their own (e.g. "pf2e", "cypher").
# - id_prefix       — optional per-ruleset namespace prefix on record IDs
#                     (v0.29.3 Phase 5.2). Default None preserves current
#                     IDs (`spell:fireball` stays `spell:fireball`). A
#                     future ruleset can set e.g. "pf2e" to emit
#                     `pf2e:spell:fireball` and avoid collisions in
#                     multi-system bundles.
#
# To add a ruleset (e.g. SRD 5.2.1):
#   1. Add an entry below.
#   2. Create rulesets/<id>/ holding the PDF.
#   3. Run: python -m srd_builder.build --ruleset <id> ...
RULESETS: Final[dict[str, dict[str, Any]]] = {
    "srd_5_1": {
        "id": "srd_5_1",
        "source_id": "SRD_CC_v5.1",
        "display_name": "D&D 5e (2014 SRD)",
        "edition_short": "5e",
        "ruleset_version": "5.1",
        "pdf_filename": "SRD_CC_v5.1.pdf",
        "game_system": "dnd5e",
        "id_prefix": None,
    },
}

# Directory names
RULESETS_DIRNAME: Final = "rulesets"
DIST_DIRNAME: Final = "dist"
SCHEMAS_DIRNAME: Final = "schemas"
EXEMPLARS_DIRNAME: Final = "exemplars"
