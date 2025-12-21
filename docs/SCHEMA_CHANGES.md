# Schema Changes Log

## v0.14.0+ Schema Updates

### Monster ID Pattern (December 2025)

**Change:** Updated `monster.schema.json` ID pattern to accept three-tier ID system.

**Before:**
```json
"pattern": "^monster:[a-z0-9_]+$"
```

**After:**
```json
"pattern": "^(monster|creature|npc):[a-z0-9_]+$"
```

**Reason:**
V0.13.0 (November 2025) introduced a three-tier ID system for monsters to distinguish:
- `monster:` - Main bestiary creatures (pages 261-365)
- `creature:` - Appendix MM-A misc creatures (pages 366-394)
- `npc:` - Appendix MM-B NPCs (pages 395-403)

The schema was never updated to reflect this change, causing validation failures when running `make release-check`. This fix brings the schema in sync with the actual data structure.

**Impact:**
- **srd-builder:** Schema now validates all 317 creatures correctly
- **Blackmoor consumers:** Any code that assumed only `monster:` prefix will need updating
  - Check for `id.startsWith('monster:')` → should check all three prefixes
  - Or use the `simple_name` field which doesn't have prefixes

**Migration:**
If you're consuming the SRD data and filtering by ID prefix:

```python
# Old (v0.12.x and earlier)
monsters = [m for m in data['items'] if m['id'].startswith('monster:')]

# New (v0.13.0+)
all_creatures = data['items']  # All 317 creatures
just_monsters = [m for m in data['items'] if m['id'].startswith('monster:')]  # 201
just_creatures = [m for m in data['items'] if m['id'].startswith('creature:')]  # 95
just_npcs = [m for m in data['items'] if m['id'].startswith('npc:')]  # 21
```

**Commit:** e051e48 (verification scripts) + 138321c (schema fix)

**See Also:**
- Commit 39c2263: v0.13.0 - Grand Slam (NPCs + Misc Creatures + Three-Tier ID System)
- docs/CHANGELOG_v0.8.3_to_v0.13.0.md for full v0.13.0 details
