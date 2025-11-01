# Equipment Extraction Status & Architecture Review

**Date:** 2025-11-01
**Purpose:** Detailed review for GPT consultation on extraction patterns and future dataset planning
**Context:** Week 2 of srd-builder project - first complete table-based extraction

---

## Executive Summary

We've successfully implemented equipment extraction from SRD 5.1 PDF tables, producing `equipment.json` with 114 items using `item:*` namespace. The extraction pipeline works, but we have parsing issues (armor AC values) and architectural questions about how to apply these patterns to future datasets (lineages, classes, spells, conditions).

**Key Question:** Can GPT help us identify patterns, improve metadata structure, and design extraction approaches for non-tabular content?

---

## Current State: equipment.json

### What We Built

**Pipeline:** `extract → parse → postprocess → write`

1. **extract_equipment.py** - PDF table extraction using PyMuPDF
   - Uses `find_tables()` to extract rows from pages 62-73
   - Position-aware section detection via font headers (18pt, 13.92pt)
   - Tracks category context across pages (armor → weapon → gear)
   - Filters reference tables (Trade Goods pricing, Lifestyle Expenses)
   - Output: `equipment_raw.json` with `table_row` arrays

2. **parse_equipment.py** - Raw table data → structured records
   - Maps columns to schema fields by category
   - Parses cost (regex: "15 gp" → {amount: 15, currency: "gp"})
   - Parses damage (regex: "1d8 slashing" → {dice: "1d8", type: "slashing"})
   - Parses properties (comma-split, lowercase)
   - Generates `item:*` namespace IDs

3. **postprocess.py** - Normalize and clean
   - Remove trailing periods from names
   - Lowercase properties arrays
   - Prune empty optional fields
   - **Note:** Does NOT normalize IDs (preserves `item:` namespace)

4. **build.py** - Orchestration
   - Calls extraction → parsing → postprocessing
   - Writes `equipment.json` with `_meta` wrapper
   - Updates `meta.json` with page_index, file manifest, extraction status

### What Works Well

✅ **Table extraction** - PyMuPDF `find_tables()` cleanly extracts rows
✅ **Section detection** - Font-based headers identify category context
✅ **Reference filtering** - Successfully removed 11 false positives (pricing tables, lifestyle levels)
✅ **ID namespace** - Consistent `item:longsword` pattern per terminology guidance
✅ **Cost parsing** - Reliably extracts "15 gp" → {amount: 15, currency: "gp"}
✅ **Weapon parsing** - Damage and properties parse correctly
✅ **Pipeline separation** - Clean boundaries: extract (I/O) vs parse (pure) vs postprocess (polish)

**Example - Good Weapon:**
```json
{
  "id": "item:dagger",
  "name": "Dagger",
  "simple_name": "dagger",
  "category": "weapon",
  "damage": {"dice": "1d4", "type": "piercing"},
  "properties": ["finesse", "light", "thrown (range 20/60)"],
  "weapon_type": "melee",
  "cost": {"amount": 2, "currency": "gp"},
  "weight": "1 lb.",
  "page": 66,
  "src": "SRD 5.1"
}
```

### What Doesn't Work / Issues

❌ **Armor AC parsing** - Getting cost instead of AC value
- Chain Shirt: AC shows 50 (should be 13) - this is the *cost*
- Breastplate: AC shows 400 (should be 14) - this is the *cost*
- Root cause: Column detection logic picking wrong column

❌ **Armor category assignment** - Leather marked as "medium" (should be "light")
- Section detection propagating wrong subcategory
- Subsection headers not reliably detected

❌ **Weight format inconsistency** - Schema expects number, we store "10 lb." string
- Schema: `"weight": {"type": "number"}`
- Actual: `"weight": "10 lb."`
- Causes validation failure

❌ **Missing versatile damage** - Properties include "versatile (1d10)" but no `versatile_damage` field
- Parser finds versatile in properties but doesn't extract damage value
- Should populate `versatile_damage: {dice: "1d10"}`

❌ **Missing range data** - Thrown/ranged weapons don't have structured range
- Properties: "thrown (range 20/60)" - stored as string
- Should extract: `range: {normal: 20, long: 60}`

❌ **Incomplete armor_class schema** - Current: integer, Should: object with dex modifiers
- Schema shows: `"armor_class": {"type": "integer"}`
- Real need: `{base: 14, dex_bonus: true, max_bonus: 2}` for medium armor
- Parser code has this logic but schema doesn't support it

### Schema vs Reality Gaps

**Schema says:**
```json
"weight": {"type": "number"}
"armor_class": {"type": "integer"}
```

**Reality has:**
```json
"weight": "10 lb."  // String with unit
"armor_class": {     // Object with modifiers (in parser, not schema)
  "base": 14,
  "dex_bonus": true,
  "max_bonus": 2
}
```

**Versatile damage issue:**
- Schema has `versatile_damage` field
- Parser code attempts to extract it
- But doesn't populate successfully from properties array

---

## Extraction Patterns: Tables vs Prose

### Current Understanding: Tables (Equipment)

**Structure:**
- PDF has explicit tables with rows/columns
- PyMuPDF `find_tables()` extracts cleanly
- Column positions relatively stable within section
- Headers visible in font size (18pt = section, 13.92pt = subsection)

**Challenges:**
- Column mapping varies by category (armor vs weapons vs gear)
- Need context propagation across pages
- Reference tables vs data tables (filtering needed)
- Merged cells, split names across columns

**Pattern that works:**
1. **Position-aware extraction** - Track Y-position of headers
2. **Context propagation** - Section/subsection flows across pages
3. **Category-specific parsing** - Different columns per category
4. **Filtering heuristics** - Detect non-item rows (prices, headers, levels)

### Speculation: Non-Table Content

#### Lineages (Races) - Chapter 2

**Expected structure:**
- Prose descriptions with embedded stat blocks
- Traits as bullet lists or paragraphs
- Size, speed, languages as structured data within prose
- Sub-races (Hill Dwarf, High Elf) as subsections

**Extraction challenges:**
- No tables - need prose parsing
- Stat blocks might be consistent format but in paragraphs
- Trait names in bold, descriptions follow
- Need to detect trait boundaries (formatting cues)

**Possible approach:**
1. Section detection by headers (chapter → race → subrace)
2. Parse stat blocks (Age, Alignment, Size, Speed patterns)
3. Extract traits by bold formatting + following text until next bold
4. Structure into: `{id, name, size, speed, languages, traits: [{name, text}]}`

**Metadata needs:**
- Trait categories (ability score, size, speed, proficiency, special)
- Parent race relationships (Hill Dwarf → Dwarf)
- Source page ranges (may span multiple pages)

#### Classes - Chapter 3

**Expected structure:**
- Class overview (prose)
- Class table (level progression with columns: XP, Proficiency, Features, Spell Slots)
- Features as subsections with prose descriptions
- Subclasses as separate sections

**Extraction challenges:**
- **Tables:** Level progression (can use table extraction)
- **Prose:** Feature descriptions (need text parsing)
- **Structure:** Class → Subclass hierarchy
- **Spells:** Spell list tables separate from spell descriptions

**Possible approach:**
1. Extract level table (similar to equipment tables)
2. Parse feature sections by header detection
3. Link features to levels from table
4. Handle subclass branching (Barbarian → Path of the Berserker)

**Metadata needs:**
- Hit dice, saving throws, proficiencies (structured data)
- Feature unlocks by level (array of {level, feature_id})
- Subclass choices and when they're available
- Spell progression (caster vs non-caster)

#### Spells - Chapter 11

**Expected structure:**
- Alphabetical list
- Each spell: bold name, level/school/casting time/range/components/duration header line
- Description paragraphs
- Some have "At Higher Levels:" subsections

**Extraction challenges:**
- Consistent format makes parsing easier
- Header line has structured data (level, school, etc.)
- Description prose needs capturing
- Higher level variants as sub-entries

**Possible approach:**
1. Detect spell by bold name + header pattern
2. Parse header line with regex (Level: \d, School: \w+, etc.)
3. Capture description until next spell
4. Extract "At Higher Levels" as separate field

**Metadata needs:**
- Components parsed (V, S, M with material description)
- Range types (touch, self, radius, distance)
- Duration types (instant, concentration, time-based)
- Damage scaling by level

#### Conditions - Appendix A

**Expected structure:**
- Short entries: bold name, prose description
- Effects as bullet lists or inline
- References to mechanics (speed=0, disadvantage, etc.)

**Extraction challenges:**
- Very short entries (1-3 paragraphs)
- No tables or complex structure
- Need to preserve mechanics in text
- Cross-references to other rules

**Possible approach:**
1. Detect by bold condition name
2. Capture description until next bold name
3. Extract as simple: `{id, name, description}`
4. Optionally parse common patterns (speed=0, advantage/disadvantage)

**Metadata needs:**
- Minimal - mostly just structured text
- Maybe tag common effects (movement, advantage, unconscious)

---

## Pattern Recognition: What's Similar?

### All Datasets Share:

1. **ID namespace pattern** - `entity-type:normalized-name`
   - Equipment: `item:longsword`
   - Lineage: `lineage:hill-dwarf`
   - Class: `class:barbarian`
   - Spell: `spell:fireball`
   - Condition: `condition:prone`

2. **Required base fields** - `{id, name, simple_name, page, src}`

3. **Nested entries pattern** - Many have sub-items with names
   - Equipment: properties array (simple strings)
   - Lineages: traits array `[{name, text}]`
   - Classes: features array `[{name, level, text}]`
   - Spells: higher_levels as sub-entry

4. **Page context** - All need source page tracking

5. **Text cleanup** - All need polish (spacing, OCR artifacts, em-dashes)

### Key Differences:

| Dataset    | Primary Structure | Extraction Method | Parsing Challenge |
|------------|-------------------|-------------------|-------------------|
| Equipment  | Tables            | PyMuPDF tables    | Column mapping    |
| Lineages   | Prose + lists     | Text blocks       | Trait boundaries  |
| Classes    | Mixed (tables + prose) | Both       | Level/feature linking |
| Spells     | Structured prose  | Pattern matching  | Header parsing    |
| Conditions | Simple prose      | Text blocks       | Entry boundaries  |

---

## Ideal State: What We Want

### General Goals

1. **Deterministic extraction** - Same PDF → same JSON every time
2. **Schema-driven** - Output matches schema 100%
3. **Pure transformations** - No I/O or logging in parse functions
4. **Composable pipeline** - extract → parse → postprocess → validate → write
5. **Fixture-driven tests** - Raw samples + expected normalized output

### Equipment-Specific Fixes Needed

1. **Fix armor AC parsing** - Detect AC column correctly, not cost
2. **Fix armor categories** - Light/Medium/Heavy detection from subsections
3. **Fix weight format** - Parse "10 lb." → 10 (number) per schema
4. **Extract versatile damage** - Parse "versatile (1d10)" → field
5. **Extract range data** - Parse "thrown (range 20/60)" → {normal: 20, long: 60}
6. **Update schema for AC** - Change integer → object with dex_bonus, max_bonus
7. **Add strength requirements** - Heavy armor needs Strength field
8. **Add stealth disadvantage** - Flag for heavy armor

### Cross-Dataset Architecture Questions

1. **Schema versioning** - How to evolve schemas without breaking consumers?
2. **Nested entry IDs** - Should traits/features have their own IDs?
   - Example: `lineage:dwarf#darkvision` or just `{name: "Darkvision"}`?
3. **Cross-references** - How to link related entities?
   - Spell schools, class spell lists, condition effects
4. **Text richness** - Store markdown? Plain text? Structured annotations?
5. **Metadata consistency** - What goes in `_meta` vs in records?

---

## Questions for GPT

### Immediate (Equipment)

1. **Column detection strategy:** How to reliably detect which column is AC vs cost vs weight in varying table layouts?
2. **Weight parsing:** Should we store "10 lb." as string or parse to number? What about fractional (1/4 lb)?
3. **Properties extraction:** Better way to parse "thrown (range 20/60)" into structured data?
4. **Schema evolution:** How to version armor_class from integer → object without breaking?

### Pattern Design (Future Datasets)

5. **Prose parsing approach:** Best practices for extracting traits/features from formatted text?
6. **Bold-as-delimiter:** Is "bold text = entry name" a reliable heuristic for SRD parsing?
7. **Nested IDs:** Should sub-items (traits, features, higher-level spell effects) get their own IDs?
8. **Table detection:** How to distinguish level progression tables from reference tables?

### Architecture (System-Wide)

9. **Extraction boundaries:** When to split vs combine related content (equipment vs magic items)?
10. **Reference resolution:** If magic items reference base items, how do consumers resolve efficiently?
11. **Metadata strategy:** What belongs in `_meta` wrapper vs in individual records?
12. **Testing approach:** How to create fixtures for prose extraction (non-deterministic splits)?

### Schema Design

13. **Type flexibility:** When to use string vs number vs object (weight, armor_class examples)?
14. **Optional field patterns:** How to handle category-specific fields (weapon vs armor)?
15. **Array conventions:** When to use array of strings vs array of objects?
16. **Validation strictness:** How much to enforce in schema vs document as "should"?

---

## Current Technical Constraints

### What We Know Works

- **PyMuPDF** for PDF parsing (fonts, text blocks, tables)
- **Python 3.11** with type hints
- **JSON Schema** for validation
- **Ruff + Black** for code style
- **pytest** for testing
- **Pre-commit hooks** enforce quality

### Guardrails (from AGENTS.md)

1. **One feature per branch** - No mixing concerns
2. **Pure functions** - parse_*.py has no I/O
3. **Deterministic** - No timestamps or env-dependent values in output
4. **Boundaries respected** - extract (I/O), parse (pure), postprocess (polish), build (orchestrate)
5. **Template-driven** - docs/templates/ define structure

### Pain Points

- **Table column variability** - Armor table ≠ weapon table ≠ gear table
- **Context propagation** - Section headers on page 62 affect tables on page 65
- **Reference table filtering** - Hard to distinguish "equipment table" from "price reference table"
- **OCR artifacts** - "H it" instead of "Hit", spacing issues
- **Font detection reliability** - Headers sometimes missed or misdetected

---

## Request for GPT

Please review this status and provide insights on:

1. **Immediate fixes** for equipment parsing (AC, weight, versatile, range)
2. **Pattern recommendations** for non-table extraction (lineages, spells)
3. **Schema design patterns** for handling varied content types
4. **Metadata strategy** for organizing and linking related data
5. **Testing approaches** for prose extraction validation
6. **Any architectural red flags** or better patterns we should consider

We're especially interested in:
- How other TTRPG data projects handle similar challenges
- Balancing schema strictness vs flexibility
- Best practices for prose → structured data extraction
- Reference/linking patterns for related entities

---

## Appendix: File Locations

**Source:**
- `rulesets/srd_5_1/raw/SRD_CC_v5.1.pdf` - Original PDF
- `rulesets/srd_5_1/raw/equipment_raw.json` - Extracted table data

**Code:**
- `src/srd_builder/extract_equipment.py` - PDF → raw JSON
- `src/srd_builder/parse_equipment.py` - Raw → structured
- `src/srd_builder/postprocess.py` - Polish and normalize
- `src/srd_builder/build.py` - Pipeline orchestration

**Output:**
- `dist/srd_5_1/data/equipment.json` - Final dataset
- `dist/srd_5_1/meta.json` - Dataset metadata

**Schema:**
- `schemas/equipment.schema.json` - Validation schema
- `docs/templates/TEMPLATE_equipment.json` - Structure template

**Guidance:**
- `docs/terminology.aliases.md` - Naming conventions
- `docs/PARKING_LOT.md` - Deferred decisions
- `docs/AGENTS.md` - Development guardrails
