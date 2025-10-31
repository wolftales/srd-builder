# Terminology & Aliases - Decision Log

This document explains terminology choices made during SRD 5.1 extraction and when/how to use the `terminology.aliases` field in `meta.json`.

---

## Quick Reference

| Source Term | Our Term | Filename | Namespace | Alias Needed? |
|-------------|----------|----------|-----------|---------------|
| Races | Lineages | `lineages.json` | `lineage:*` | ✅ Yes - cultural sensitivity |
| Equipment | Equipment | `equipment.json` | `item:*` | ❌ No - no conflict |
| Monsters | Monsters | `monsters.json` | `monster:*` | ❌ No - matches source |
| Spells | Spells | `spells.json` | `spell:*` | ❌ No - matches source |
| Classes | Classes | `classes.json` | `class:*` | ❌ No - matches source |

---

## terminology.aliases Field in meta.json

**Status:** Implemented for "races" → "lineages" mapping

### Intent
Help consumers find content when terminology differs between rulesets or versions. Provides a mapping from alternative terms to the canonical names used in this dataset.

### Example from Blackmoor
```json
"terminology": {
  "aliases": {
    "races": "lineages",
    "race": "lineage"
  },
  "note": "We use 'lineage' terminology to be future-proof and align with modern D&D direction."
}
```

### Context

#### Why We Chose "Lineages" Over "Races"

**The Problem:**
- SRD 5.1 source PDF uses the term "races" (Dwarf, Elf, Halfling, etc.)
- Modern D&D direction is moving away from "race" terminology
- Future editions and systems are adopting alternatives: "lineage", "ancestry", "heritage", "species"
- We want our data structure to be future-proof and not require breaking changes

**The Decision:**
- Use `lineages.json` as the canonical filename
- Use `lineage:*` as the namespace prefix
- Add `terminology.aliases` to `meta.json` mapping `"races": "lineages"`
- This lets consumers know "if you're looking for races, check lineages.json"

**Benefits:**
1. **Future-Proof:** Won't need to rename files when WotC updates terminology
2. **Modern Alignment:** Matches direction of D&D One / 5.5e
3. **Clear Intent:** Shows we made a deliberate choice, not an error
4. **Backward Compatible:** Aliases help consumers using old terminology

**Example:**
- Source PDF says: "Chapter 2: Races"
- Our data structure: `lineages.json` with namespace `lineage:hill-dwarf`
- Meta.json explains: `"aliases": {"races": "lineages"}`

#### Equipment Terminology - No Alias Needed

**The Question:**
Should we use `equipment.json` or `items.json`? Do we need an alias?

**Analysis:**
- SRD 5.1 uses "Equipment" as the chapter title
- Common game terminology: "items", "gear", "equipment" used interchangeably
- Namespace consideration: We chose `item:*` over `equipment:*`

**Decision:**
- **Filename:** `equipment.json` (matches SRD chapter name)
- **Namespace:** `item:*` (shorter, more common in game engines)
- **No alias needed** - "equipment" vs "items" aren't competing terms like "race" vs "lineage"

**Rationale:**
1. **Filename clarity:** `equipment.json` immediately tells you this is the SRD equipment chapter
2. **Namespace brevity:** `item:longsword` is shorter and cleaner than `equipment:longsword`
3. **No conflict:** Unlike "race/lineage", there's no cultural/social reason to prefer one term
4. **Common pattern:** Game engines typically use "item" as the class/type name
5. **Internal consistency:** Within the file, use `item:*` namespace for all IDs

**Example Structure:**
```json
// File: equipment.json
{
  "source": "SRD_CC_v5.1",
  "weapons": [
    {
      "id": "item:longsword",
      "name": "Longsword",
      ...
    }
  ],
  "armor": [
    {
      "id": "item:chain-mail",
      "name": "Chain Mail",
      ...
    }
  ]
}
```

**Key Point:** The filename can describe the content source ("equipment" from SRD), while the namespace describes the data type ("item" for game engine use). These don't conflict.

---

### Open Questions

1. **Scope:** Is this for top-level file names only, or also field names within data structures?
   - Example: Should it map `monster.race` → `monster.lineage`?
   - Or just `races.json` → `lineages.json`?

2. **Direction:** Which way should the mapping go?
   - Option A: Old → New (`races` → `lineages`) - "if you're looking for races, check lineages"
   - Option B: New → Old (`lineages` → `races`) - "we call it lineages, you might know it as races"
   - Blackmoor uses Option A

3. **Per-Ruleset vs Global:**
   - Should each ruleset have its own aliases?
   - Or should this be a global srd-builder convention?
   - SRD 5.1 specifically uses "classes" and "races" terminology in the source PDF
   - Other systems might differ

4. **When to Add:**
   - Add now as empty placeholder?
   - Add when we extract a second ruleset with different terminology?
   - Add when we actually encounter a naming conflict?

5. **Consumer Behavior:**
   - How should consumers use this? Auto-redirects? Documentation only?
   - Should we provide utility functions to resolve aliases?

### Decision Point
Implement when:
- We extract a second ruleset with different terminology, OR
- We identify an actual naming conflict that affects consumers, OR
- A consumer specifically requests this feature

### Related Files
- `docs/external/blackmoor/README_v1.md` - Original structure with `races/`
- `docs/external/blackmoor/README_v2.md` - Updated structure with `lineages.json`
- `docs/external/blackmoor/meta.json` - Reference implementation with aliases

### Implementation Checklist (When Triggered)
- [x] Decide on alias direction and scope - File-level only, old→new direction
- [ ] Update `_generate_meta_json()` in `build.py` (if automated build exists)
- [ ] Add schema validation for terminology section
- [x] Document usage in README - meta.json includes terminology section
- [x] Consider adding to TEMPLATE files - Not needed, meta-level only
- [ ] Update tests to verify alias structure

---

## Practical Guide for Extraction

### When Adding New Data Types

**Ask yourself:**
1. Does the SRD use different terminology than we want to use long-term?
2. Is there a cultural, social, or future-proofing reason to diverge?
3. Would consumers be confused looking for the SRD term?

**If YES to all three:** Add an alias
**If NO to any:** Just match the SRD terminology

### Filename vs Namespace Pattern

You can (and should) diverge between filename and namespace when it makes sense:

**Pattern:**
- **Filename** = Source document structure (helps humans find content)
- **Namespace** = Game engine data type (helps code reference content)

**Examples:**
- ✅ `equipment.json` with `item:*` namespace - Different but both clear
- ✅ `lineages.json` with `lineage:*` namespace - Consistent divergence from source
- ✅ `monsters.json` with `monster:*` namespace - Matches source, no divergence

**Anti-patterns:**
- ❌ `items.json` with `equipment:*` namespace - Confusing mismatch
- ❌ `races.json` with `lineage:*` namespace - Filename doesn't explain why IDs differ

### For Week 2+ Equipment Extraction

**Use these conventions:**
- **Filename:** `equipment.json`
- **Namespace:** `item:*` for all IDs
- **No alias needed** in meta.json
- **Rationale:** Filename matches SRD, namespace matches common usage

**Example IDs:**
```json
{
  "id": "item:longsword",        // ✅ Good
  "id": "item:chain-mail",       // ✅ Good
  "id": "equipment:longsword"    // ❌ Don't use this
}
```

---

## Future Considerations

**When extracting other rulesets:**
- Pathfinder might use "ancestry" instead of "race" or "lineage"
- Different systems might categorize equipment differently (gear, items, possessions)
- Track these in their respective meta.json files
- Consider a global terminology mapping if patterns emerge across multiple rulesets
