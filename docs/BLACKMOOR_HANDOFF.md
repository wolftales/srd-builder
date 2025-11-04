# 📦 SRD v0.8.2 - Blackmoor Integration

**Version:** 0.8.2 (was v0.5.2)
**Schema:** 1.3.0 (was 1.2.0)
**Date:** November 3, 2025

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

### New Datasets (Schema 1.2.0 → 1.3.0)
- **Spells:** 319 spells (v0.6.2)
- **Tables:** 23 reference tables (v0.7.0)
- **Lineages:** 13 races/lineages (v0.8.0)
- **Classes:** 12 character classes (v0.8.2)

### Features You Requested ✅
All implemented in v0.5.1:
- Ability modifiers: `monster["ability_scores"]["strength_modifier"]`
- Structured actions: `action["attack_type"]`, `action["to_hit"]`, `action["damage"]`
- CR indexes: `index["monsters"]["by_cr"]["5"]`
- Type indexes: `index["monsters"]["by_type"]["dragon"]`

### Data Quality
- Equipment: 106 items (was 111, removed duplicates)
- Alias system: Entity-level aliases + automatic index expansion (v0.8.1)
- PDF metadata: Extracted from source PDF, not hardcoded (v0.8.1)

---

## 🚀 Integration Steps

1. **Copy package:** `dist/srd_5_1/` → `vendor/srd-builder-v0.8.2/`
2. **Update loaders:** Add loaders for spells, tables, lineages, classes
3. **Update schema check:** `assert _meta["schema_version"] == "1.3.0"`
4. **Test:** Verify CR/type indexes, ability modifiers, structured actions work

---

## ⚠️ Known Issues (Can Work Around)

**Critical for your use case:**
- Equipment properties have embedded data: `"versatile (1d10)"` instead of clean `"versatile"` + `versatile_damage` field
- Weapon subcategories missing: Can't filter by simple/martial proficiency level
- Spell effects at 52% coverage (area 17%, healing 2%)
- Ranged spell range not extracted (use spell dataset for range)

**Workarounds:**
- Parse parentheses from properties or use `versatile_damage` field directly
- Use text field for incomplete spell effects
- Cross-reference spell dataset for spell attack ranges

**See `docs/TODO.md` for full list and priorities**

---

## 🔮 What We're Working On

**v0.8.3** (2-3 weeks) - Equipment Polish
- Clean properties: `"versatile"` not `"versatile (1d10)"`
- Add weapon subcategories: simple_melee, martial_ranged, etc.
- Extract spell range field for ranged spell attacks

**v0.8.4** (2-3 weeks) - Spell Effects
- Area of effect: 17% → >50%
- Healing: 2% → all healing spells
- Complete spell effects coverage

**v0.9.0** (1-2 weeks) - Conditions
- ~15-20 status conditions (poisoned, stunned, charmed, etc.)

**All v0.8.x-v0.9.x changes will be additive** (no breaking changes)

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

# Lineages (v0.8.0)
lineage["ability_score_increases"]  # [{"strength": 2}]
lineage["traits"]  # [{name, text}, ...]

# Classes (v0.8.2)
class_data["hit_die"]  # "d10"
class_data["proficiencies"]["armor"]  # ["light", "medium", "shields"]
```

---

## ✅ Integration Checklist

**When done:**
- [ ] All 6 datasets load without errors
- [ ] Schema version assertion passes (1.3.0)
- [ ] CR/Type indexes return expected monster lists
- [ ] Ability modifiers accessible on all monsters
- [ ] Structured actions have attack_type, to_hit, damage fields
- [ ] Spells, tables, lineages, classes integrate into your systems
