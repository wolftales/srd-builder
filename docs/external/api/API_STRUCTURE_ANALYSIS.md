# API Structure Analysis: dnd5eapi.co vs Open5e

## Executive Summary

Analysis of two major D&D 5e APIs reveals **consistent structural patterns** that differ significantly from srd-builder's flat inheritance from Blackmoor. Both APIs favor nested object structures, rich cross-references, and clear separation between list and detail views.

**Key Finding:** Both APIs keep ability scores **flat at root level** (strength/dexterity/etc as direct properties), but **group everything else** into logical clusters. This hybrid approach balances queryability with organization.

---

## 1. List vs Detail Structures

### dnd5eapi.co
**List endpoint** (`/api/2014/monsters`):
```json
{
  "count": 334,
  "results": [
    {
      "index": "aboleth",
      "name": "Aboleth",
      "url": "/api/2014/monsters/aboleth"
    }
  ]
}
```

**Detail endpoint** (`/api/2014/monsters/aboleth`):
- Full stat block with ~30 properties
- Nested objects for complex data
- Cross-references as objects with `{index, name, url}`

### Open5e
**List endpoint** (`/monsters/?limit=10`):
```json
{
  "count": 3207,
  "next": "https://api.open5e.com/monsters/?limit=10&page=2",
  "previous": null,
  "results": [
    {
      "slug": "aboleth",
      "name": "Aboleth",
      "size": "Large",
      "type": "Aberration",
      "challenge_rating": "10",
      "armor_class": 17,
      "hit_points": 135
      // ... ~15 summary fields
    }
  ]
}
```

**Verdict:** Open5e provides **richer list views** (useful summary data), dnd5eapi.co provides **minimal list views** (index+name only). Both require detail fetch for full data.

**Recommendation for srd-builder:**
- Current single-file approach (complete data) is simpler than maintaining two views
- If adding FastAPI: minimal list view + full detail endpoints
- Priority: optimize single-file structure first

---

## 2. Ability Scores: Flat vs Nested

### Both APIs: **FLAT at root level** ✅

**dnd5eapi.co:**
```json
{
  "strength": 21,
  "dexterity": 9,
  "constitution": 15,
  "intelligence": 18,
  "wisdom": 15,
  "charisma": 18
}
```

**Open5e:**
```json
{
  "strength": 21,
  "dexterity": 9,
  "constitution": 15,
  "intelligence": 18,
  "wisdom": 15,
  "charisma": 18
}
```

**Current srd-builder:** ✅ Already matches this pattern!

**Verdict:** Keep ability scores flat. This is the proven pattern.

---

## 3. Proficiencies: Object Array vs Simple Keys

### dnd5eapi.co: Rich nested objects
```json
{
  "proficiencies": [
    {
      "value": 6,
      "proficiency": {
        "index": "saving-throw-con",
        "name": "Saving Throw: CON",
        "url": "/api/2014/proficiencies/saving-throw-con"
      }
    },
    {
      "value": 12,
      "proficiency": {
        "index": "skill-history",
        "name": "Skill: History",
        "url": "/api/2014/proficiencies/skill-history"
      }
    }
  ]
}
```

### Open5e: Split into separate fields
```json
{
  "constitution_save": 6,
  "intelligence_save": 8,
  "wisdom_save": 6,
  "perception": 10,
  "skills": {
    "history": 12,
    "perception": 10
  }
}
```

### Current srd-builder:
```json
{
  "strength_save": 6,
  "dexterity_save": 3,
  "skills": {
    "perception": 4,
    "stealth": 6
  }
}
```

**Verdict:**
- **dnd5eapi.co** = unified but verbose
- **Open5e/srd-builder** = practical, queryable, less redundant
- Current approach is closer to Open5e (the simpler, more popular API)

**Recommendation:** Keep current structure. It's already following the proven pattern.

---

## 4. Cross-References: String vs Object

### dnd5eapi.co: Always rich objects
```json
{
  "damage": [
    {
      "damage_type": {
        "index": "bludgeoning",
        "name": "Bludgeoning",
        "url": "/api/2014/damage-types/bludgeoning"
      },
      "damage_dice": "2d6+5"
    }
  ]
}
```

### Open5e: Mostly strings
```json
{
  "damage_vulnerabilities": "",
  "damage_resistances": "acid; bludgeoning, piercing, and slashing from nonmagical attacks",
  "damage_immunities": "cold"
}
```

### Current srd-builder: Strings
```json
{
  "damage_resistances": ["cold", "fire"],
  "damage_immunities": ["poison"]
}
```

**Verdict:**
- **dnd5eapi.co** = best for API consumers (type-safe, rich metadata)
- **Open5e** = pragmatic, human-readable strings
- **srd-builder** = middle ground (structured arrays)

**Recommendation for v2.0:**
Add optional `type_id` fields while keeping human-readable strings:
```json
{
  "damage_resistances": [
    {
      "type": "cold",
      "type_id": "cold",
      "conditions": null
    },
    {
      "type": "bludgeoning, piercing, and slashing from nonmagical attacks",
      "type_id": "bludgeoning",
      "conditions": "nonmagical"
    }
  ]
}
```

---

## 5. Speed: Nested Object vs Flat

### Both APIs: **Nested object** ✅

**dnd5eapi.co:**
```json
{
  "speed": {
    "walk": "10 ft.",
    "swim": "40 ft."
  }
}
```

**Open5e:**
```json
{
  "speed": {
    "walk": 30,
    "swim": 40,
    "burrow": 20
  }
}
```

**Current srd-builder:**
```json
{
  "speed": "30 ft., swim 60 ft."
}
```

**Verdict:** srd-builder's flat string is **least queryable**. Both APIs use nested objects.

**Recommendation:**
```json
{
  "speed": {
    "walk": 30,
    "swim": 60,
    "fly": 0,
    "burrow": 0,
    "climb": 0,
    "notes": ""
  }
}
```

---

## 6. Actions: Structured vs Hybrid

### dnd5eapi.co: Fully structured
```json
{
  "actions": [
    {
      "name": "Tentacle",
      "desc": "Melee Weapon Attack: +9 to hit...",
      "attack_bonus": 9,
      "damage": [
        {
          "damage_type": {
            "index": "bludgeoning",
            "name": "Bludgeoning",
            "url": "/api/2014/damage-types/bludgeoning"
          },
          "damage_dice": "2d6+5"
        }
      ],
      "dc": {
        "dc_type": {
          "index": "con",
          "name": "CON",
          "url": "/api/2014/ability-scores/con"
        },
        "dc_value": 14,
        "success_type": "none"
      }
    }
  ]
}
```

### Open5e: Hybrid structured
```json
{
  "actions": [
    {
      "name": "Tentacle",
      "desc": "Melee Weapon Attack: +9 to hit...",
      "attack_bonus": 9,
      "damage_dice": "2d6",
      "damage_bonus": 5
    }
  ]
}
```

**Current srd-builder:**
```json
{
  "actions": [
    {
      "name": "Bite",
      "description": "Melee Weapon Attack: +5 to hit..."
    }
  ]
}
```

**Verdict:**
- **dnd5eapi.co** = most queryable, but very verbose
- **Open5e** = good balance (structured attack data + prose desc)
- **srd-builder** = least structured (prose-only)

**Recommendation:** Add structured fields while keeping description:
```json
{
  "actions": [
    {
      "name": "Tentacle",
      "description": "Melee Weapon Attack: +9 to hit...",
      "attack_bonus": 9,
      "damage_dice": "2d6+5",
      "damage_types": ["bludgeoning"],
      "reach": 10,
      "dc": {
        "ability": "constitution",
        "value": 14,
        "success": "none"
      }
    }
  ]
}
```

---

## 7. Armor Class: String vs Structured

### dnd5eapi.co: Array of objects
```json
{
  "armor_class": [
    {
      "type": "natural",
      "value": 17
    }
  ]
}
```

### Open5e: Value + description
```json
{
  "armor_class": 17,
  "armor_desc": "natural armor"
}
```

**Current srd-builder:**
```json
{
  "armor_class": "17 (natural armor)"
}
```

**Verdict:** Open5e's split approach is cleanest for simple cases.

**Recommendation:**
```json
{
  "armor_class": {
    "base": 17,
    "source": "natural armor",
    "with_shield": null,
    "with_mage_armor": null
  }
}
```

---

## 8. Senses: String vs Object

### dnd5eapi.co: Nested object
```json
{
  "senses": {
    "darkvision": "120 ft.",
    "passive_perception": 20
  }
}
```

### Open5e: Combined string + passive
```json
{
  "senses": "darkvision 120 ft., passive Perception 20"
}
```

**Current srd-builder:**
```json
{
  "senses": "darkvision 60 ft., passive Perception 12"
}
```

**Verdict:** dnd5eapi.co's structured approach is more queryable.

**Recommendation:**
```json
{
  "senses": {
    "darkvision": 120,
    "blindsight": 0,
    "tremorsense": 0,
    "truesight": 0,
    "passive_perception": 20
  }
}
```

---

## 9. Metadata Fields

### dnd5eapi.co:
```json
{
  "index": "aboleth",
  "url": "/api/2014/monsters/aboleth",
  "updated_at": "2025-10-24T20:42:13.741Z",
  "image": "/api/images/monsters/aboleth.png"
}
```

### Open5e:
```json
{
  "slug": "aboleth",
  "document__slug": "wotc-srd",
  "document__title": "5e Core Rules",
  "document__license_url": "http://open5e.com/legal",
  "document__url": "http://dnd.wizards.com/...",
  "page_no": 261,
  "v2_converted_path": "/v2/creatures/srd_aboleth/"
}
```

**Current srd-builder:**
```json
{
  "source": "SRD 5.1"
}
```

**Verdict:**
- **dnd5eapi.co** = API-focused (urls, timestamps, images)
- **Open5e** = provenance-focused (source documents, pages, versions)
- **srd-builder** = minimal (just source)

**Recommendation:** Add version/schema metadata:
```json
{
  "source": "SRD 5.1",
  "schema_version": "2.0.0",
  "extracted_at": "2025-12-22",
  "index": "aboleth"
}
```

---

## 10. Summary Comparison Table

| Feature | dnd5eapi.co | Open5e | srd-builder | Recommendation |
|---------|-------------|--------|-------------|----------------|
| **Ability Scores** | Flat ✅ | Flat ✅ | Flat ✅ | Keep flat |
| **Speed** | Nested object | Nested object | String ❌ | **Nest as object** |
| **Armor Class** | Array[Object] | Value + Desc | String ❌ | **Split to object** |
| **Senses** | Nested object | String | String ❌ | **Nest as object** |
| **Proficiencies** | Unified array | Split fields ✅ | Split fields ✅ | Keep split |
| **Skills** | In proficiencies | Nested object ✅ | Nested object ✅ | Keep nested |
| **Cross-refs** | Rich objects | Strings | Arrays | **Add type_id fields** |
| **Actions** | Fully structured | Hybrid | Prose-only ❌ | **Add structure** |
| **List/Detail** | Separate | Separate | Single file ✅ | Keep single (simpler) |
| **Metadata** | API-focused | Provenance | Minimal | **Add schema_version** |

---

## Key Structural Patterns Observed

### Pattern 1: Hybrid Flat+Nested
- **Ability scores:** Always flat (all 6 at root)
- **Everything else:** Nested into logical groups
- **Why:** Ability scores are queried constantly, nesting them adds friction

### Pattern 2: Cross-Reference Objects
- **dnd5eapi.co:** `{index, name, url}` objects everywhere
- **Open5e:** Strings with structured slugs
- **Benefit:** Type-safe, enables graph traversal, supports future linking

### Pattern 3: Description + Structure Duality
- Keep human-readable prose (`description` field)
- Add structured fields for querying (`attack_bonus`, `damage_dice`, etc)
- **Never choose one over the other** - provide both

### Pattern 4: Minimal List, Full Detail
- List endpoints: just enough to render a table row
- Detail endpoints: complete data
- **Alternative:** Single complete file (srd-builder's current approach)

---

## Recommendations for srd-builder v2.0

### High Priority (Breaking Changes)

1. **Nest speed as object:**
   ```json
   "speed": {"walk": 30, "swim": 60}
   ```

2. **Nest senses as object:**
   ```json
   "senses": {"darkvision": 120, "passive_perception": 20}
   ```

3. **Structure armor_class:**
   ```json
   "armor_class": {"base": 17, "source": "natural armor"}
   ```

4. **Add structured action data:**
   ```json
   {
     "name": "Bite",
     "description": "...",
     "attack_bonus": 5,
     "damage_dice": "1d6+3",
     "damage_types": ["piercing"]
   }
   ```

### Medium Priority (Additive Changes)

5. **Add type_id to cross-references:**
   ```json
   {
     "damage_resistances": [
       {"type": "cold", "type_id": "cold"}
     ]
   }
   ```

6. **Add schema_version to all files:**
   ```json
   {
     "schema_version": "2.0.0",
     "source": "SRD 5.1"
   }
   ```

### Low Priority (Future Enhancements)

7. **Consider list/detail split** (only if building FastAPI)
8. **Add image URLs** (only if sourcing artwork)
9. **Add updated_at timestamps** (only if tracking changes)

---

## Migration Path

### Phase 1: Analysis (Current)
- ✅ Collected API structures
- ✅ Identified patterns
- 🔄 Build before/after examples

### Phase 2: Design
- Draft complete v2.0 monster.schema.json
- Create migration examples (Aboleth, Goblin, Adult Red Dragon)
- Get user feedback on proposed structure

### Phase 3: Implementation
- Update parser to generate v2.0 structure
- Update postprocessor for new nesting
- Run golden tests, fix edge cases

### Phase 4: Release
- Bundle v2.0.0 with backward-incompatible notice
- Archive v1.x.x as "legacy" branch
- Update documentation and examples

---

## Open Questions

1. **Backward Compatibility:**
   - Provide v1 → v2 migration script?
   - Maintain both formats for one release?
   - Hard cut to v2.0 only?

2. **Consumer Impact:**
   - Notify Blackmoor of changes?
   - Survey other known consumers?
   - Provide compatibility shim?

3. **Performance:**
   - Measure file size impact of nested objects
   - Test parse time differences
   - Benchmark query performance (if relevant)

4. **Field Grouping:**
   - Group defenses? `"defenses": {"resistances": [], "immunities": []}`
   - Group stats? `"combat": {"ac": {}, "hp": {}, "speed": {}}`
   - Or keep relatively flat with selective nesting?

---

## Next Steps

1. **User Decision:** Review this analysis and decide on v2.0 scope
2. **Draft Schema:** Create complete v2.0 monster.schema.json
3. **Build Examples:** Show Aboleth before/after in both formats
4. **Validate:** Run examples through schema validator
5. **Implement:** Update pipeline to generate v2.0 structure
6. **Test:** Golden tests must pass with new structure
7. **Release:** v2.0.0 with clear migration notes
