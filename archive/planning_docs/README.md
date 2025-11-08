# Planning Docs Archive

Historical planning and investigation documents that served their purpose during development.

## Contents

### Table Investigation & Discovery (v0.9.x)

**REFERENCE_TABLES_INVESTIGATION.md** (Nov 5, 2025)
- Investigated which reference tables exist in SRD PDF vs convenience tables
- Findings: travel_pace/creature_size exist, cantrip_damage/spell_slots don't
- Status: Complete - extracted tables now in system

**table_discovery_60-75.md** (Nov 4, 2025)
- Manual discovery of 15 equipment tables (pages 60-75)
- PyMuPDF auto-detection: 6.7% success rate
- Status: Complete - all 10 equipment tables now extracted with modern patterns (v0.9.9 Part 1)

### Table Migration Documentation (v0.9.x)

**TABLE_MIGRATION_GUIDE.md** (Nov 5, 2025)
- Guide for migrating table extraction to new SRD versions
- Parser complexity tiers, coordinate update steps
- Status: Superseded by pattern-based extraction system (self-documenting)

**TABLE_MIGRATION_QUICK_REF.md** (Nov 5, 2025)
- Quick reference for table migration commands
- Status: Superseded by pattern-based system

### Equipment Planning (v0.8.3)

**v0.8.3_equipment_plan.md** (Nov 3, 2025)
- Plan for equipment properties normalization and subcategory cleanup
- Schema 1.3.0 → 1.3.1 changes
- Status: Complete - work finished in v0.8.3, superseded by v0.9.9 equipment modernization

## Why Archived

All documents served their purpose during development phases. Current state is captured in:
- **ROADMAP.md** - Active development priorities
- **PARKING_LOT.md** - Deferred features and technical debt
- **Live code** - table_metadata.py, patterns.py, test fixtures
- **v0.9.9 archives** - Equipment modernization plan (also archived after completion)

No unique information remains that isn't already captured in active documentation or code.

## Related Archives

- `../v0.9.9_legacy_parsers/` - Legacy table parser code (1313 lines)
- `../v0.9.9_planning/` - v0.9.9 equipment modernization plan
- `../TODO.md` - Historical TODO list (pre-ROADMAP structure)
