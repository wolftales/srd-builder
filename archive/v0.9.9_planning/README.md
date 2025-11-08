# v0.9.9 Planning Archive

This directory contains planning documents created during v0.9.9 development that have been archived after completion.

## Contents

### EQUIPMENT_PLAN.md (Archived Nov 8, 2025)
**Original Purpose**: Pre-work planning document created Nov 7, 2025 to analyze equipment modernization requirements and unblock table migration work.

**Why Archived**:
- Part 1 (Table Migration) is complete - 30/30 tables migrated ✅
- Part 2 (Equipment Assembly) is well-defined in ROADMAP.md
- All deferred items captured in PARKING_LOT.md
- Document served its purpose as planning artifact

**Valuable Reference Content**:
- **Column Mapping Patterns**: Detailed examples for parsing armor AC, weapon properties, tool subcategories
- **Subcategory Inference Rules**: Logic for categorizing armor (Light/Medium/Heavy/Shield), weapons (Simple/Martial), tools (Artisan's/Gaming/etc.)
- **Architecture Diagram**: Visual representation of equipment assembly pipeline
- **Implementation Notes**: Edge cases, parsing patterns, technical considerations

**When to Reference**:
- During v0.9.9 Part 2 implementation (equipment assembly from tables)
- When debugging equipment parsing logic
- For understanding original design decisions

**Current State**: All goals from this plan are tracked in:
- **ROADMAP.md**: v0.9.9 Part 2 (Equipment Assembly)
- **PARKING_LOT.md**: Magic Items Architecture (deferred to v0.10.0+)

## Related Documents
- `../v0.9.9_legacy_parsers/README.md` - Legacy code archive from Part 1
- `../../docs/ROADMAP.md` - Current development roadmap
- `../../docs/PARKING_LOT.md` - Deferred features and technical debt
