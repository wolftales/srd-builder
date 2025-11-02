# Comprehensive Alias System Implementation

## Summary

Implemented a three-level alias system for the SRD dataset to enable flexible terminology and entity lookups.

## Implementation Date

November 2, 2025 (v0.8.0 enhancement)

## Problem Statement

After implementing lineages in v0.8.0, we needed a way for consumers to:
1. Search using historical terminology ("race" → "lineage")
2. Search using partial names for compound items ("tankard" → "flask_or_tankard")
3. Discover these mappings programmatically

Initial implementation only added aliases to `meta.json` as documentation, which didn't help with actual searches since consumers use `index.json` for lookups.

## Solution: Three-Level Alias Pattern

### Level 1: Index-level (Terminology Aliases)

**Location**: `index.json` (functional) and `meta.json` (documentation)

**Purpose**: Map historical or alternative category names to canonical names

**Implementation**:
```json
// index.json
{
  "aliases": {
    "races": "lineages",
    "race": "lineage"
  },
  "lineages": { ... }
}

// meta.json
{
  "terminology": {
    "aliases": {
      "races": "lineages",
      "race": "lineage"
    }
  }
}
```

**Consumer Usage**:
```javascript
const canonical = index.aliases[searchTerm] || searchTerm;
const data = index[canonical];
```

### Level 2: Entity-level (Search Term Aliases)

**Location**: Individual entity objects (optional field)

**Purpose**: Enable searching for items using alternative names or partial terms

**Schema Definition**: Added to all entity schemas (equipment, lineage, spell, monster, table)
```json
{
  "aliases": {
    "type": "array",
    "items": {"type": "string"},
    "uniqueItems": true,
    "description": "Alternative names or search terms"
  }
}
```

**Example Usage** (future):
```json
{
  "id": "item:flask_or_tankard",
  "simple_name": "flask_or_tankard",
  "name": "Flask or tankard",
  "aliases": ["flask", "tankard"]
}
```

### Level 3: Indexer-level (Automatic Expansion)

**Location**: `src/srd_builder/indexer.py`

**Purpose**: Automatically expand `by_name` lookups to include entity aliases

**Implementation**: Modified `_build_by_name_map()` to:
1. Index entity's display name (existing behavior)
2. Check for optional `aliases` field
3. Add each alias as additional lookup key pointing to same entity ID

**Result**:
```json
{
  "equipment": {
    "by_name": {
      "flask or tankard": "item:flask_or_tankard",
      "flask": "item:flask_or_tankard",    // From aliases array
      "tankard": "item:flask_or_tankard"   // From aliases array
    }
  }
}
```

## Files Modified

### Schemas (Added optional `aliases` field)
- `schemas/equipment.schema.json`
- `schemas/lineage.schema.json`
- `schemas/spell.schema.json`
- `schemas/monster.schema.json`
- `schemas/table.schema.json`

### Core Logic
- `src/srd_builder/indexer.py`:
  - Modified `_build_by_name_map()` to expand entity aliases
  - Modified `build_indexes()` to add top-level `aliases` section

### Build Configuration
- `src/srd_builder/build.py`:
  - Updated `_generate_meta_json()` to include both singular and plural forms

### Documentation
- `docs/ALIAS_USAGE.md`: Complete usage guide with examples

## Testing

- All 113 tests passing
- Validation passing for all schemas
- Linting (ruff + black) clean

## Current Status

### ✅ Complete
- Index-level terminology aliases in `index.json`
- Entity-level schema support (all entities can have aliases)
- Automatic indexer expansion in `by_name` maps
- Documentation in `meta.json` and usage guide
- Both singular and plural forms ("race"/"races" → "lineage"/"lineages")

### ⏳ Pending (Future Work)
- Add actual alias data to compound equipment items:
  - `flask_or_tankard`: `aliases: ["flask", "tankard"]`
  - `jug_or_pitcher`: `aliases: ["jug", "pitcher"]`
- Update parse_equipment.py to populate aliases for specific items
- Add test cases to verify alias lookups work correctly

## Use Cases Enabled

1. **Legacy API Compatibility**: Consumers can use "race" terminology while dataset uses "lineage"
2. **Natural Search**: Search for "tankard" finds "Flask or tankard"
3. **Discoverable Mappings**: Aliases are programmatically accessible in index.json
4. **Flexible Lookups**: One entity can be found via multiple search terms

## Design Principles

1. **Opt-in**: Aliases are optional - only add when needed
2. **Non-breaking**: Doesn't affect existing lookups (additive only)
3. **Discoverable**: Aliases visible in index.json for consumers
4. **Consistent**: Same pattern across all entity types
5. **Documented**: Both functional (index.json) and descriptive (meta.json)

## Future Considerations

- Consider adding more entity-level aliases as needed
- Monitor for alias conflicts (already tracked in index.conflicts)
- Could extend to support alias chains if needed (current: single-level only)
- Could add reverse lookups (canonical → aliases) if useful

## References

- PARKING_LOT.md lines 92-172: Terminology aliases discussion
- PARKING_LOT.md lines 579-679: Equipment aliases discussion
- docs/ALIAS_USAGE.md: Complete usage guide
