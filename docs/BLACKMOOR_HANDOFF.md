# 📦 SRD v0.8.5 - Blackmoor Integration

**Version:** 0.8.5
**Schema:** 1.4.0
**Date:** November 3, 2025
**Status:** Ready for integration testing

**📖 See `dist/srd_5_1/README.md` for package contents and usage examples**

---

## 🎯 What Changed Since v0.5.2

v0.5.2 → Infrastructure (no data changes)
v0.5.3 → Package structure (breaking path change)
v0.6.2 → Spells dataset (NEW)
v0.6.4 → Spell quality improvements
v0.7.0 → Tables dataset (NEW)
v0.8.0 → Lineages dataset (NEW)
v0.8.1 → Alias system, PDF metadata
v0.8.2 → Classes dataset (NEW)
**v0.8.4 → Character creation blockers (BREAKING)** ⚠️
**v0.8.5 → Spell enhancements (ADDITIVE)** ✅

### New Datasets (Schema 1.2.0 → 1.4.0)
- **Spells:** 319 spells (v0.6.2)
- **Tables:** 23 reference tables (v0.7.0)
- **Lineages:** 13 races/lineages (v0.8.0)
- **Classes:** 12 character classes (v0.8.2)

### Critical Fixes in v0.8.4 ⚠️ BREAKING
**These were blocking character creation:**
- **Lineages:** Added `ability_modifiers` field (was `ability_increases`)
- **Lineages:** Added `parent_lineage` field for subraces
- **Classes:** Renamed `saves` → `saving_throw_proficiencies`
- **Spells:** Added complete range structure in `casting.range`

### Improvements in v0.8.5 ✅ ADDITIVE
**Spell mechanics now complete:**
- **Healing:** 0% → 100% (10 spells with dice/fixed/conditional patterns)
- **Area of Effect:** 17.2% → 24.8% (+43%, 79 spells)
- **Range:** 100% complete (verified from v0.8.4)

### Features You Requested ✅
All implemented in v0.5.1:
- Ability modifiers: `monster["ability_scores"]["strength_modifier"]`
- Structured actions: `action["attack_type"]`, `action["to_hit"]`, `action["damage"]`
- CR indexes: `index["monsters"]["by_cr"]["5"]`
- Type indexes: `index["monsters"]["by_type"]["dragon"]`

### Data Quality
- Equipment: 106 items (proficiency field added v0.8.3)
- Alias system: Entity-level aliases + automatic index expansion (v0.8.1)
- PDF metadata: Extracted from source PDF, not hardcoded (v0.8.1)
- All 114 tests passing, CI green

---

## 🚀 Integration Steps

1. **Copy package:** `dist/srd_5_1/` → `vendor/srd-builder-v0.8.5/`
2. **Update schema check:** `assert _meta["schema_version"] == "1.4.0"`
3. **Update field access (v0.8.4 breaking changes):**
   - Lineages: `ability_increases` → `ability_modifiers`
   - Classes: `saves` → `saving_throw_proficiencies`
   - Spells: Access range at `spell["casting"]["range"]`
4. **Test character creation:** Verify ability modifiers, parent lineage links work
5. **Test spellcasting:** Verify healing, area, range data work

---

## ⚠️ Breaking Changes in v0.8.4

**You MUST update these fields:**

### Lineages
```python
# OLD (v0.8.3 and earlier)
lineage["ability_increases"]  # ❌ Field renamed

# NEW (v0.8.4+)
lineage["ability_modifiers"]  # ✅ Use this
# Example: {"strength": 1, "dexterity": 1, ...}  # Human
# Example: {"constitution": 2}  # Dwarf

# NEW: Parent lineage for subraces
if "parent_lineage" in lineage:
    parent_id = lineage["parent_lineage"]  # "lineage:dwarf"
    # Inherit traits from parent
```

### Classes
```python
# OLD (v0.8.3 and earlier)
character_class["saves"]  # ❌ Field renamed
# Values were: ["Str", "Dex"]  # ❌ Capitalized

# NEW (v0.8.4+)
character_class["saving_throw_proficiencies"]  # ✅ Use this
# Values are: ["strength", "dexterity"]  # ✅ Lowercase
```

### Spells
```python
# OLD (v0.8.3 and earlier)
spell["range"]  # ❌ This never existed

# NEW (v0.8.4+)
spell["casting"]["range"]  # ✅ Correct location
# Structure: {type: "ranged", distance: {value: 120, unit: "feet"}}
# Or: {type: "self", area: {shape: "cone", size: {value: 15, unit: "feet"}}}

# Design note: Range grouped with other casting mechanics
# spell["casting"] = {time, range, duration, concentration, ritual}
```

## ✅ Additive Features in v0.8.5

**These are safe to use immediately (no breaking changes):**

### Healing
```python
# Check if spell heals
if "healing" in spell["effects"]:
    healing = spell["effects"]["healing"]

    if "dice" in healing:
        # Dice-based: Cure Wounds, Regenerate
        formula = healing["dice"]  # "1d8" or "4d8+15"

    elif "amount" in healing:
        # Fixed amount: Heal, Mass Heal
        hp = healing["amount"]  # 70 or 700

    elif "condition" in healing:
        # Conditional: Vampiric Touch, Wish
        desc = healing["condition"]
        # "half the amount of necrotic damage dealt"
```

### Area of Effect
```python
# Check if spell has area
if "area" in spell["effects"]:
    area = spell["effects"]["area"]
    shape = area["shape"]  # "sphere", "cone", "cube", "cylinder", "line"
    size = area["size"]    # 20
    unit = area["unit"]    # "feet"

    # Render VTT area template
    render_area(shape, size, unit)
```

## 🔧 Known Issues

**None currently.** All datasets production-ready, 114 tests passing, CI green.

---

## 🔮 What's Next

**v0.9.0** - Table Extraction Expansion
- Infrastructure improvements for better table handling
- Equipment tables (armor, weapons) for quick reference
- Improved multi-page table support

**v0.10.0** - Conditions Dataset
- ~15-20 status conditions (poisoned, stunned, charmed, frightened, etc.)
- Benefits from v0.9.0 table improvements
- See `docs/CONDITIONS_NOTES.md` for condition-like spell effects

**Future v0.8.x/v0.9.x/v0.10.x changes will be additive** (no more breaking changes planned)

---

## 📋 New Fields & Features

**Test these to verify integration:**

```python
# Ability modifiers (v0.5.1)
monster["ability_scores"]["strength_modifier"]  # 5
monster["ability_scores"]["dexterity_modifier"]  # 0

# Structured actions (v0.5.1)
action["attack_type"]  # "melee_weapon", "ranged_weapon", "melee_spell", "ranged_spell"
action["to_hit"]  # 9
action["reach"]  # 10
action["damage"]["average"]  # 22
action["damage"]["dice"]  # "3d10+6"
action["damage"]["type"]  # "piercing"

# CR and type indexes (always existed)
index["monsters"]["by_cr"]["5"]  # ["aboleth", "air_elemental", ...]
index["monsters"]["by_type"]["dragon"]  # ["adult_black_dragon", ...]

# Spell structure (v0.6.2)
spell["level"]  # 3
spell["school"]  # "evocation"
spell["components"]["verbal"]  # true
spell["damage"]["dice"]  # "8d6"

# Tables (v0.7.0)
table["columns"]  # [{"name": "CR", "type": "string"}, ...]
table["rows"]  # [["0", 10], ["1/8", 25], ...]

# Lineages (v0.8.0, updated v0.8.4)
lineage["ability_modifiers"]  # {"strength": 2}  # ✅ RENAMED from ability_increases
lineage["parent_lineage"]  # "lineage:dwarf"  # ✅ NEW in v0.8.4 (subraces only)
lineage["traits"]  # [{name, text}, ...]

# Classes (v0.8.2, updated v0.8.4)
class_data["hit_die"]  # "d10"
class_data["proficiencies"]["armor"]  # ["light", "medium", "shields"]
class_data["saving_throw_proficiencies"]  # ["strength", "constitution"]  # ✅ RENAMED from saves
class_data["primary_abilities"]  # ["strength", "dexterity"]  # ✅ NEW in v0.8.4

# Spell healing (v0.8.5)
spell["effects"]["healing"]["dice"]  # "1d8"  # ✅ NEW
spell["effects"]["healing"]["amount"]  # 70  # ✅ NEW
spell["effects"]["healing"]["condition"]  # "half the amount dealt"  # ✅ NEW

# Spell area (v0.8.5 improved)
spell["effects"]["area"]["shape"]  # "sphere", "cylinder", etc.
spell["effects"]["area"]["size"]  # 20  # ✅ More spells have this now (79 vs 55)
```

---

## ✅ Integration Checklist

**v0.8.4 Breaking Changes:**
- [ ] Updated lineage field: `ability_increases` → `ability_modifiers`
- [ ] Updated class field: `saves` → `saving_throw_proficiencies`
- [ ] Updated spell range access: `spell["casting"]["range"]`
- [ ] Test character creation with new ability modifiers
- [ ] Test multiclassing with new saving throw proficiencies
- [ ] Test subrace parent lineage inheritance

**v0.8.5 Additive Features:**
- [ ] Test healing spells (Cure Wounds, Heal, Vampiric Touch)
- [ ] Test area spells (Fireball, Flame Strike, Burning Hands)
- [ ] Test spell range data (Fire Bolt, Sending)
- [ ] Verify VTT area rendering with expanded AOE coverage

**General:**
- [ ] All 6 datasets load without errors
- [ ] Schema version assertion passes (1.4.0)
- [ ] CR/Type indexes return expected monster lists
- [ ] Ability modifiers accessible on all monsters
- [ ] Structured actions have attack_type, to_hit, damage fields
- [ ] Full integration test suite passes
