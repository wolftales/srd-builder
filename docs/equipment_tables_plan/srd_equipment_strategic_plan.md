# SRD Equipment: Strategic Analysis & Action Plan

**Date:** 2025-11-01
**Purpose:** Bridge immediate equipment fixes with long-term architectural patterns
**For:** GPT implementation, with consideration for Copilot's pragmatic concerns

---

## Executive Summary

You've successfully built a working extraction pipeline (extract → parse → postprocess → write) for equipment tables. The **core pattern works**, but you have:

1. **Tactical bugs** in column detection and parsing (AC, weight, versatile damage)
2. **Strategic questions** about schema design and extensibility to other datasets
3. **Tension** between "fix what's broken now" vs "design for future datasets"

**Key Insight:** The equipment issues reveal patterns you'll face with ALL datasets. Solving them strategically now will accelerate lineages, classes, and spells later.

---

## Part 1: Immediate Equipment Fixes (Tactical)

### Critical Path Issues

These bugs block equipment.json from being production-ready:

#### 1. Armor AC Parsing (HIGH PRIORITY)
**Problem:** Column detection grabbing cost (50gp) instead of AC (13)

**Root Cause:** Table columns aren't in consistent positions across armor types
- Light armor table: [Name, Cost, AC, Strength, Stealth, Weight]
- Medium armor table: [Name, Cost, AC, Strength, Stealth, Weight] (different widths)
- Heavy armor table: [Name, Cost, AC, Strength, Stealth, Weight] (different widths)

**Solution Strategy:**
```python
# Instead of fixed column indices, use column header detection
def detect_armor_columns(table_data):
    """
    Find column positions by looking for header keywords.
    More robust than assuming column[2] = AC
    """
    headers = table_data[0]  # First row usually has headers
    column_map = {}

    for idx, header in enumerate(headers):
        header_lower = header.lower().strip()
        if 'armor class' in header_lower or header_lower == 'ac':
            column_map['ac'] = idx
        elif 'cost' in header_lower:
            column_map['cost'] = idx
        elif 'weight' in header_lower:
            column_map['weight'] = idx
        # ... etc

    return column_map
```

**Actionable:** Parse header row to build column map per table section

---

#### 2. Weight Format Mismatch (MEDIUM PRIORITY)
**Problem:** Schema expects number, storing "10 lb." string

**Decision Point:** Which way to go?

**Option A: Parse to number**
```python
def parse_weight(weight_str):
    """Extract numeric value from '10 lb.' or '1/4 lb.'"""
    if not weight_str or weight_str == '—':
        return None

    # Handle fractions: "1/4 lb." → 0.25
    if '/' in weight_str:
        numerator, rest = weight_str.split('/')
        denominator = rest.split()[0]  # "4 lb." → "4"
        return float(numerator) / float(denominator)

    # Handle decimals: "10.5 lb." → 10.5
    return float(weight_str.split()[0])

# Schema: "weight": {"type": "number"}
```

**Option B: Keep string, update schema**
```json
{
  "weight": {
    "type": "string",
    "pattern": "^(\\d+(\\.\\d+)?|\\d+/\\d+) lb\\.$"
  }
}
```

**Recommendation:** **Option A** - Parse to number
- **Why:** Enables sorting, filtering, encumbrance calculations
- **Trade-off:** Loses unit information (assumes pounds)
- **Mitigation:** Document unit assumption, add `weight_unit` field if multiple units needed

**Actionable:** Add `parse_weight()` function, update schema to `number`

---

#### 3. Versatile Damage Extraction (MEDIUM PRIORITY)
**Problem:** Properties has "versatile (1d10)" but `versatile_damage` field not populated

**Current Code Attempt:**
```python
# Parser sees properties: ["finesse", "versatile (1d10)"]
# But doesn't extract the damage value
```

**Solution:**
```python
def extract_versatile_damage(properties):
    """
    Parse 'versatile (1d10)' from properties array.
    Returns damage object or None.
    """
    for prop in properties:
        if prop.startswith('versatile'):
            # Extract dice from "versatile (1d10)"
            match = re.search(r'versatile \(([0-9]+d[0-9]+)\)', prop, re.IGNORECASE)
            if match:
                return {"dice": match.group(1)}
    return None

# Usage in parse_equipment.py
weapon['versatile_damage'] = extract_versatile_damage(properties)
```

**Actionable:** Add extraction function, populate field when present

---

#### 4. Range Data Extraction (LOW PRIORITY)
**Problem:** "thrown (range 20/60)" stored as string, not structured

**Solution:**
```python
def extract_range(properties):
    """
    Parse 'thrown (range 20/60)' or 'range (80/320)'.
    Returns {normal: int, long: int} or None.
    """
    for prop in properties:
        match = re.search(r'range \((\d+)/(\d+)\)', prop, re.IGNORECASE)
        if match:
            return {
                "normal": int(match.group(1)),
                "long": int(match.group(2))
            }
    return None
```

**Actionable:** Add to schema, extract when present

---

#### 5. Armor Category Assignment (LOW PRIORITY)
**Problem:** Leather armor marked as "medium" (should be "light")

**Root Cause:** Subsection header detection not reliable
- Section: "Armor" (18pt font)
- Subsection: "Light Armor" (13.92pt font)
- If subsection header missed, previous category persists

**Solution:** More robust header detection
```python
def detect_section_headers(page):
    """
    Look for both section and subsection headers.
    Return hierarchy: {section: "Armor", subsection: "Light Armor"}
    """
    headers = {}
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                size = span["size"]
                text = span["text"].strip()

                if size > 17:  # Section header
                    headers['section'] = text
                elif 16 > size > 13:  # Subsection header
                    # "Light Armor" → category = "light"
                    if "light" in text.lower():
                        headers['subcategory'] = "light"
                    elif "medium" in text.lower():
                        headers['subcategory'] = "medium"
                    elif "heavy" in text.lower():
                        headers['subcategory'] = "heavy"

    return headers
```

**Actionable:** Add subcategory detection, propagate correctly

---

### Implementation Order for Equipment Fixes

1. **AC Column Detection** (1-2 hours) - Blocks schema validation
2. **Weight Parsing** (1 hour) - Schema mismatch
3. **Versatile Damage** (1 hour) - Missing game data
4. **Armor Category** (2 hours) - Wrong categorization
5. **Range Extraction** (1 hour) - Nice-to-have

**Total:** ~6-7 hours of focused work

---

## Part 2: Strategic Architecture (Cross-Dataset Patterns)

### Pattern Recognition: What's Reusable?

Looking at equipment extraction, here are the patterns that will apply to other datasets:

#### Pattern 1: Context Propagation Across Pages
**Equipment Example:**
- Page 62 has "Armor" header (section)
- Page 63 has "Light Armor" subheader (category)
- Page 64-65 have light armor tables (no repeated header)
- Parser must "remember" we're in light armor section

**Applies To:**
- **Classes:** Class header → subclass sections → features (spans multiple pages)
- **Lineages:** Race header → subrace → traits
- **Spells:** Alphabetical, need to track current spell across pages

**Generalized Solution:**
```python
class ContextTracker:
    """Track hierarchical context across pages"""
    def __init__(self):
        self.section = None      # "Armor", "Barbarian", "Dwarf"
        self.subsection = None   # "Light Armor", "Path of Berserker", "Hill Dwarf"
        self.page = None

    def update_from_headers(self, page_headers):
        """Update context when headers detected"""
        if 'section' in page_headers:
            self.section = page_headers['section']
        if 'subsection' in page_headers:
            self.subsection = page_headers['subsection']

    def get_current_context(self):
        """Get full hierarchical context"""
        return {
            'section': self.section,
            'subsection': self.subsection,
            'page': self.page
        }
```

**Key Insight:** All datasets need context tracking, not just equipment

---

#### Pattern 2: Multi-Strategy Extraction (Tables + Prose)
**Equipment:** Mostly tables
**Classes:** Tables (level progression) + prose (feature descriptions)
**Lineages:** Mostly prose + stat blocks
**Spells:** Structured prose (consistent format)
**Conditions:** Pure prose

**Architecture Implication:** Need multiple extraction strategies
```python
# extraction_strategies.py
class TableExtractor:
    """For equipment, class tables"""
    def extract(self, page): ...

class StructuredProseExtractor:
    """For spells (name + header line + description)"""
    def extract(self, page): ...

class FormattedTextExtractor:
    """For lineages, conditions (bold headers + text blocks)"""
    def extract(self, page): ...
```

**Question for GPT:** Should these be:
- Separate modules? (extract_tables.py, extract_prose.py)
- Strategy pattern classes?
- Simple functions with different signatures?

**Recommendation:** **Separate modules**, one per strategy
- Keeps extraction logic focused
- Each dataset picks the appropriate extractor(s)
- Can compose: classes need BOTH table + prose extraction

---

#### Pattern 3: Category-Specific Parsing
**Equipment:** Armor ≠ Weapon ≠ Gear (different fields)
**Classes:** Caster ≠ Martial (spell slots vs extra attacks)
**Lineages:** Base race ≠ Subrace (inheritance)

**Architecture Decision:**
```python
# Option A: Single parser with conditionals
def parse_equipment_item(raw_item, category):
    base = parse_common_fields(raw_item)

    if category == "armor":
        return parse_armor_specific(base, raw_item)
    elif category == "weapon":
        return parse_weapon_specific(base, raw_item)
    else:
        return base

# Option B: Separate parsers per category
# parse_armor.py, parse_weapon.py, parse_gear.py
```

**Recommendation:** **Option B** for complex categories, **Option A** for simple variants
- Equipment: Separate (armor/weapon very different)
- Classes: Separate (caster/martial distinct enough)
- Lineages: Single parser (subraces are just adding traits)

---

#### Pattern 4: Schema Flexibility vs Strictness

**Current Tension:**
- Schema says `weight: number`
- Reality has `weight: "10 lb."`
- Parser tried to do `armor_class: {base, dex_bonus, max}` but schema says `integer`

**The Real Issue:** Schema-first vs Data-first design

**Two Philosophies:**

**Schema-First (Strict):**
```json
// Define ideal structure, force data to conform
{
  "weight": {"type": "number"},  // Parse "10 lb." → 10
  "armor_class": {
    "type": "object",
    "properties": {
      "base": {"type": "integer"},
      "dex_bonus": {"type": "boolean"},
      "max_bonus": {"type": ["integer", "null"]}
    }
  }
}
```

**Data-First (Flexible):**
```json
// Let data structure emerge, refine schema later
{
  "weight": {"type": ["number", "string"]},  // Accept both
  "armor_class": {
    "oneOf": [
      {"type": "integer"},  // Simple case
      {"type": "object"}    // Complex case
    ]
  }
}
```

**Recommendation:** **Hybrid approach**
1. Start data-first during extraction prototyping
2. Converge to schema-first once patterns stable
3. Use schema versioning when structure changes

**For Equipment Now:**
- Update schema to match parser reality (AC as object, weight as number)
- Document the "why" in schema comments
- Version as `v1.0` when stable

---

### Schema Design Patterns (General Principles)

Based on equipment challenges, here are guidelines for ALL datasets:

#### 1. Field Type Selection
```markdown
**Use STRING when:**
- Format may vary (em-dashes, fractions, units)
- Parsing is complex or error-prone
- Human readability matters more than computation
Example: `"speed": "30 ft."` (not `{value: 30, unit: "ft"}`)

**Use NUMBER when:**
- Need sorting, comparison, math
- Format is consistent and parseable
- Loss of unit info acceptable (or track separately)
Example: `"weight": 10` (assuming pounds)

**Use OBJECT when:**
- Multiple related values
- Needs sub-structure for clarity
Example: `"damage": {"dice": "1d8", "type": "slashing"}`

**Use ARRAY OF STRINGS when:**
- Simple list, order doesn't matter much
- Items don't need sub-fields
Example: `"properties": ["finesse", "light"]`

**Use ARRAY OF OBJECTS when:**
- Items have multiple attributes
- Need consistent structure per item
Example: `"traits": [{"name": "Darkvision", "text": "You can see..."}]`
```

#### 2. Optional vs Required Fields
```json
// Equipment pattern
{
  "id": "required",
  "name": "required",
  "category": "required",
  "cost": "required",

  // Category-specific (optional)
  "damage": "optional - weapons only",
  "armor_class": "optional - armor only",
  "versatile_damage": "optional - some weapons"
}
```

**Principle:** Required = present for ALL items, Optional = category-specific

#### 3. Nested Entry IDs
**Question from review:** Should traits/features have IDs?

**Examples:**
```json
// Option A: No IDs (simple)
{
  "id": "lineage:dwarf",
  "traits": [
    {"name": "Darkvision", "text": "..."},
    {"name": "Dwarven Resilience", "text": "..."}
  ]
}

// Option B: Nested IDs (structured)
{
  "id": "lineage:dwarf",
  "traits": [
    {"id": "lineage:dwarf#darkvision", "name": "Darkvision", "text": "..."},
    {"id": "lineage:dwarf#dwarven-resilience", "name": "Dwarven Resilience", "text": "..."}
  ]
}
```

**Recommendation:** **Start without IDs, add if needed**
- **Without IDs:** Simpler, sufficient if traits aren't referenced elsewhere
- **With IDs:** Needed if building cross-reference system (e.g., "Classes that get Darkvision trait")

**Guideline:** Add complexity only when there's a concrete use case

#### 4. Cross-References
**Future Challenge:** Linking related data

Examples:
- Spell schools (reference to school definition)
- Class spell lists (array of spell IDs)
- Magic items (reference to base item)

**Pattern:**
```json
{
  "id": "spell:fireball",
  "school": "evocation",  // String reference
  "school_ref": "school:evocation"  // Explicit ID reference (optional)
}
```

**Decision:** Defer until you have 2+ datasets that need linking

---

## Part 3: Non-Table Extraction Strategies

### Strategy 1: Structured Prose (Spells)

**Characteristics:**
- Consistent format: [Name] + [Header line] + [Description]
- Pattern-based extraction possible

**Extraction Approach:**
```python
def extract_spells(page):
    """
    Detect: **Bold Name** followed by italic stats line.
    Capture description until next bold name.
    """
    spells = []
    current_spell = None

    for block in page.get_text("dict")["blocks"]:
        for line in block["lines"]:
            # Check if this line is a spell name (bold, larger)
            if is_spell_name(line):
                if current_spell:
                    spells.append(current_spell)
                current_spell = {"name": get_text(line), "description": ""}

            # Check if this is the stats line (italic)
            elif current_spell and is_stats_line(line):
                current_spell['stats'] = parse_stats_line(line)

            # Otherwise, accumulate description text
            elif current_spell:
                current_spell['description'] += get_text(line) + " "

    return spells
```

**Key Functions:**
- `is_spell_name()`: Bold font, certain size, starts at left margin
- `parse_stats_line()`: Regex for "Level X School, Casting Time: ..., Range: ..."
- `get_text()`: Extract clean text from PyMuPDF span

**Parse Challenge:** Stats line format
```text
"1st-level evocation, Casting Time: 1 action, Range: 150 feet, ..."
```

**Parsing Strategy:**
```python
def parse_stats_line(line_text):
    """Extract structured data from stat line"""
    stats = {}

    # Level and school: "3rd-level conjuration"
    level_match = re.match(r'(\d+)(?:st|nd|rd|th)-level (\w+)', line_text)
    if level_match:
        stats['level'] = int(level_match.group(1))
        stats['school'] = level_match.group(2)

    # Extract key-value pairs: "Casting Time: 1 action"
    patterns = {
        'casting_time': r'Casting Time: ([^,]+)',
        'range': r'Range: ([^,]+)',
        'components': r'Components: ([^,]+)',
        'duration': r'Duration: ([^,]+)'
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, line_text)
        if match:
            stats[key] = match.group(1).strip()

    return stats
```

**Testing Strategy:**
```python
# Fixture: Raw spell text
SAMPLE_SPELL = """
**Fireball**
3rd-level evocation, Casting Time: 1 action, Range: 150 feet, Components: V, S, M, Duration: Instantaneous

A bright streak flashes from your pointing finger to a point you choose...
"""

def test_spell_extraction():
    result = extract_spell(SAMPLE_SPELL)
    assert result['name'] == "Fireball"
    assert result['level'] == 3
    assert result['school'] == "evocation"
    # ...
```

---

### Strategy 2: Formatted Text (Lineages, Conditions)

**Characteristics:**
- Bold headers mark entry boundaries
- Description follows until next bold header
- May have bullet lists or sub-sections

**Extraction Approach:**
```python
def extract_formatted_entries(page):
    """
    Generic extraction for bold-name + description pattern.
    Works for lineages, conditions, feats, etc.
    """
    entries = []
    current_entry = None

    for block in page.get_text("dict")["blocks"]:
        for line in block["lines"]:
            # Bold text at start = new entry
            if line_starts_with_bold(line):
                if current_entry:
                    entries.append(current_entry)
                current_entry = {
                    "name": get_bold_text(line),
                    "content": []
                }

            # Accumulate content for current entry
            elif current_entry:
                current_entry['content'].append(get_text(line))

    # Join content lines into single text
    for entry in entries:
        entry['text'] = ' '.join(entry['content'])
        del entry['content']

    return entries
```

**Challenge:** Structured data within prose

**Lineage Example:**
```text
**Dwarf**

Size: Medium
Speed: 25 feet
Languages: Common, Dwarvish

Darkvision. You can see in dim light within 60 feet...
Dwarven Resilience. You have advantage on saving throws...
```

**Parsing Strategy:**
```python
def parse_lineage(raw_entry):
    """Extract stat block + traits from lineage text"""
    text = raw_entry['text']

    # Extract stat block (Size, Speed, Languages)
    stats = {}
    stats['size'] = extract_pattern(text, r'Size: (\w+)')
    stats['speed'] = extract_pattern(text, r'Speed: ([\d\w ]+)')
    stats['languages'] = extract_pattern(text, r'Languages: ([^\.]+)')

    # Extract traits (bold name + description)
    traits = []
    trait_pattern = r'\*\*([^*]+)\*\*\.?\s+([^*]+)'
    for match in re.finditer(trait_pattern, text):
        traits.append({
            "name": match.group(1),
            "text": match.group(2).strip()
        })

    return {
        "id": f"lineage:{slugify(raw_entry['name'])}",
        "name": raw_entry['name'],
        **stats,
        "traits": traits
    }
```

**Key Insight:** Need flexible parsers that can extract structure from prose without rigid table assumptions

---

### Strategy 3: Mixed Content (Classes)

**Characteristics:**
- Prose overview
- Level progression table
- Feature descriptions (prose)
- Subclass sections

**Extraction Approach:** Combine strategies
```python
def extract_class(pages):
    """
    Multi-pass extraction:
    1. Extract level table (use table strategy)
    2. Extract feature sections (use formatted text strategy)
    3. Link features to levels
    """
    class_data = {
        "name": None,
        "hit_die": None,
        "proficiencies": [],
        "level_table": [],
        "features": []
    }

    for page in pages:
        # Pass 1: Look for level table
        tables = page.find_tables()
        for table in tables:
            if is_level_table(table):
                class_data['level_table'] = parse_level_table(table)

        # Pass 2: Look for features (bold headers + descriptions)
        features = extract_formatted_entries(page)
        class_data['features'].extend(features)

    # Pass 3: Link features to levels
    link_features_to_levels(class_data)

    return class_data
```

**Challenge:** Associating features with levels

**Solution:** Use level table as index
```python
def link_features_to_levels(class_data):
    """
    Level table: [{level: 1, features: ["Rage", "Unarmored Defense"]}, ...]
    Features: [{name: "Rage", text: "..."}, ...]

    Goal: Add 'level' field to each feature
    """
    level_to_features = {}
    for row in class_data['level_table']:
        for feature_name in row['features']:
            level_to_features[feature_name] = row['level']

    for feature in class_data['features']:
        feature['level'] = level_to_features.get(feature['name'])
```

---

## Part 4: Metadata & System Architecture

### Metadata Strategy

**Question from review:** What goes in `_meta` vs records?

**Current Pattern:**
```json
{
  "_meta": {
    "id": "equipment",
    "version": "1.0.0",
    "extracted_at": "2025-03-20T14:30:00Z",
    "source": {
      "title": "SRD 5.1",
      "pages": "62-73"
    },
    "schema_version": "1.0.0",
    "record_count": 114
  },
  "equipment": [ /* records */ ]
}
```

**Principle:** `_meta` is ABOUT the dataset, records are the dataset

**What Goes in `_meta`:**
- Dataset identification (id, version)
- Extraction metadata (when, from where, by what)
- Schema version (for evolution tracking)
- Summary stats (count, categories)
- Validation status
- Known issues/limitations

**What Goes in Records:**
- The actual data
- Source page per record
- Record-specific metadata (nothing)

**Example for Future:**
```json
{
  "_meta": {
    "id": "lineages",
    "version": "1.0.0",
    "schema_version": "1.0.0",
    "source": {
      "title": "SRD 5.1",
      "pages": "4-12"
    },
    "record_count": 9,
    "categories": {
      "base_races": 7,
      "subraces": 2
    },
    "known_issues": [
      "Subrace traits may duplicate base race traits in text"
    ]
  },
  "lineages": [ /* records */ ]
}
```

---

### Cross-Dataset Relationships

**Future Challenge:** tables.json relates to items

**Possible Patterns:**

**Pattern 1: Inline References**
```json
// In magic_items.json
{
  "id": "item:+1-longsword",
  "base_item": "item:longsword",  // Reference to equipment.json
  "modifiers": {
    "attack": 1,
    "damage": 1
  }
}
```

**Pattern 2: Separate Relationship File**
```json
// In relationships.json
{
  "magic_item_bases": [
    {"magic_item": "item:+1-longsword", "base_item": "item:longsword"}
  ],
  "class_spell_lists": [
    {"class": "class:wizard", "spells": ["spell:fireball", "spell:shield", ...]}
  ]
}
```

**Pattern 3: Linked Data (JSON-LD)**
```json
{
  "@context": "https://schema.org/",
  "@type": "MagicItem",
  "@id": "item:+1-longsword",
  "basedOn": {"@id": "item:longsword"}
}
```

**Recommendation:** **Pattern 1 for now**
- Simplest, inline references
- Good enough until you have 3+ datasets
- Can migrate to Pattern 2 if cross-references proliferate

**Guideline:** Start simple, add structure when needed

---

### Validation & Quality

**Current State:** Schema validation via JSON Schema

**Recommended Additions:**

```python
# validation.py
def validate_dataset(data, schema):
    """
    Multi-level validation:
    1. Schema conformance (JSON Schema)
    2. Business rules (custom)
    3. Cross-record consistency
    """
    issues = []

    # Level 1: Schema
    try:
        jsonschema.validate(data, schema)
    except jsonschema.ValidationError as e:
        issues.append(f"Schema validation failed: {e}")

    # Level 2: Business rules
    for record in data['equipment']:
        # Example: Armor must have AC
        if record['category'] == 'armor' and 'armor_class' not in record:
            issues.append(f"{record['id']}: armor missing AC")

        # Example: Weapons must have damage
        if record['category'] == 'weapon' and 'damage' not in record:
            issues.append(f"{record['id']}: weapon missing damage")

    # Level 3: Consistency
    ids = [r['id'] for r in data['equipment']]
    if len(ids) != len(set(ids)):
        issues.append("Duplicate IDs found")

    return issues
```

**Testing Strategy:**
```python
# tests/test_equipment.py
def test_equipment_schema_validation():
    """All equipment records validate against schema"""
    data = load_json('dist/srd_5_1/data/equipment.json')
    schema = load_json('schemas/equipment.schema.json')

    errors = validate_dataset(data, schema)
    assert len(errors) == 0, f"Validation errors: {errors}"

def test_armor_has_ac():
    """All armor items have AC values"""
    data = load_json('dist/srd_5_1/data/equipment.json')

    for item in data['equipment']:
        if item['category'] == 'armor':
            assert 'armor_class' in item, f"{item['id']} missing AC"
```

---

## Part 5: Tables.json & Relationships

**Challenge:** Equipment tables (like treasure tables, encounter tables) reference items

**Example:**
```json
// tables.json (hypothetical)
{
  "id": "table:treasure-hoard-cr-0-4",
  "name": "Treasure Hoard: Challenge 0-4",
  "rolls": [
    {
      "roll": "01-06",
      "result": "no magic items"
    },
    {
      "roll": "07-16",
      "result": "2d6 items from Magic Item Table A",
      "table_ref": "table:magic-item-a"
    }
  ]
}

// magic_item_table_a.json
{
  "id": "table:magic-item-a",
  "rolls": [
    {
      "roll": "01-50",
      "result": "Potion of Healing",
      "item_ref": "item:potion-of-healing"
    },
    {
      "roll": "51-60",
      "result": "Spell scroll (cantrip)",
      "item_ref": null,  // Not a specific item
      "note": "DM chooses cantrip"
    }
  ]
}
```

**Key Decisions:**

1. **Separate tables.json or inline?**
   - Separate file: Keeps equipment.json clean
   - Inline: All item info in one place
   - **Recommendation:** Separate, link via IDs

2. **How to handle generic references?**
   - "Potion of Healing" → specific item ✓
   - "Spell scroll (cantrip)" → category, not specific ❌
   - **Solution:** Use `item_ref` for specific, `category` for generic

3. **Table relationships?**
   - Tables reference other tables ("roll on Table A")
   - Need `table_ref` field
   - **Pattern:** Same as item references

**Schema Sketch:**
```json
{
  "tables": {
    "type": "array",
    "items": {
      "type": "object",
      "properties": {
        "id": {"type": "string", "pattern": "^table:"},
        "name": {"type": "string"},
        "description": {"type": "string"},
        "rolls": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "roll": {"type": "string"},  // "01-06" or "1d6"
              "result": {"type": "string"},
              "item_ref": {"type": ["string", "null"]},
              "table_ref": {"type": ["string", "null"]},
              "note": {"type": ["string", "null"]}
            }
          }
        }
      }
    }
  }
}
```

**Recommendation:** Defer tables.json until you have magic_items.json
- Equipment doesn't reference tables
- Tables need magic items to be useful
- Build magic_items next (uses equipment patterns)

---

## Part 6: Actionable Recommendations

### For GPT: Immediate Implementation Plan

**Phase 1: Fix Equipment Bugs (This Week)**
1. Implement column header detection for armor AC
2. Add weight parsing (string → number)
3. Extract versatile_damage from properties
4. Fix armor category detection
5. Extract range data
6. Update schema to match parser output
7. Add validation tests

**Deliverables:**
- Working equipment.json with correct AC, weight, categories
- Updated schema (v1.0)
- Test suite covering edge cases

---

**Phase 2: Establish Extraction Patterns (Next Week)**
1. Create `extraction_strategies` module:
   - `table_extractor.py` (refactor from extract_equipment)
   - `structured_prose_extractor.py` (for spells)
   - `formatted_text_extractor.py` (for lineages, conditions)

2. Create `context_tracker.py`:
   - Generic context propagation across pages
   - Used by all extractors

3. Document patterns in `docs/EXTRACTION_PATTERNS.md`

**Deliverables:**
- Reusable extraction utilities
- Pattern documentation
- Foundation for lineages/spells

---

**Phase 3: Second Dataset (Week After)**
Pick ONE to validate patterns:

**Option A: Spells** (recommended)
- Tests structured prose extraction
- Large dataset (~300 spells)
- Different enough from tables to validate pattern

**Option B: Conditions** (simpler)
- Tests formatted text extraction
- Small dataset (~15 conditions)
- Quick win to build confidence

**Option C: Lineages** (complex)
- Tests prose + stat blocks
- Hierarchical (race → subrace)
- Good if you want challenge

**Recommendation:** **Spells** - validates new pattern, high value dataset

---

### For Copilot: Pragmatic Concerns Addressed

**"Don't refactor until bugs are fixed"**
→ Agreed. Phase 1 fixes bugs without refactoring.

**"Don't plan too far ahead"**
→ Phase 2 extracts reusable patterns from working code, not speculation.

**"Focus on what's parsing now"**
→ Phase 1 is 100% focused on equipment. Phases 2-3 build on proven patterns.

**Bridge:** Fix → Extract Pattern → Apply to Next Dataset
- Each phase delivers working code
- Patterns emerge from real code, not theory
- No speculative architecture

---

### For Both: Collaboration Framework

**Decision Points to Align On:**

1. **Weight format:** Number or string? (Recommendation: number)
2. **Armor AC schema:** Integer or object? (Recommendation: object)
3. **Nested entry IDs:** Include or defer? (Recommendation: defer)
4. **Extraction module structure:** Strategies or simple functions? (Recommendation: strategies)
5. **Next dataset:** Spells, conditions, or lineages? (Recommendation: spells)

**Workflow:**
1. GPT drafts implementation based on this plan
2. Copilot reviews for pragmatic issues
3. Align on any changes needed
4. Implement incrementally (one fix/feature per branch)

---

## Part 7: Testing Strategy for Prose Extraction

**Challenge:** Prose extraction is less deterministic than tables

**Approach: Fixture-Based Testing**

```python
# tests/fixtures/spell_samples.py
FIREBALL_RAW = """
**Fireball**
3rd-level evocation, Casting Time: 1 action, Range: 150 feet, Components: V, S, M (a tiny ball of bat guano and sulfur), Duration: Instantaneous

A bright streak flashes from your pointing finger to a point you choose within range...

At Higher Levels: When you cast this spell using a spell slot of 4th level or higher...
"""

FIREBALL_EXPECTED = {
    "id": "spell:fireball",
    "name": "Fireball",
    "level": 3,
    "school": "evocation",
    "casting_time": "1 action",
    "range": "150 feet",
    "components": "V, S, M (a tiny ball of bat guano and sulfur)",
    "duration": "Instantaneous",
    "description": "A bright streak flashes from your pointing finger...",
    "higher_levels": "When you cast this spell using a spell slot..."
}

# tests/test_spell_extraction.py
def test_spell_parsing():
    """Verify spell parser handles standard format"""
    result = parse_spell(FIREBALL_RAW)
    assert result == FIREBALL_EXPECTED

def test_spell_edge_cases():
    """Handle spells with missing fields, special formats"""
    # Cantrip (no higher levels)
    # Concentration duration
    # Self range
    # ...
```

**Key Principles:**
1. **Fixtures = Real examples** from PDF
2. **Expected output = Hand-crafted** correct structure
3. **Edge cases** identified from actual PDF content
4. **Tests = Regression prevention** as parser evolves

---

## Part 8: Long-Term Vision

**Goal:** Complete SRD 5.1 dataset extraction

**Datasets (Priority Order):**
1. ✅ Equipment (done, needs fixes)
2. Spells (~300 items, structured prose)
3. Conditions (~15 items, simple prose)
4. Lineages (~9 races + subraces, prose + stats)
5. Classes (~12 classes + subclasses, tables + prose)
6. Magic Items (~200+ items, tables + prose, references equipment)
7. Monsters (~300+ creatures, stat blocks, most complex)
8. Tables (treasure, encounters, references items/monsters)

**Estimated Timeline:**
- Equipment fixes: 1 week
- Pattern extraction: 1 week
- Spells: 2 weeks
- Conditions: 1 week
- Lineages: 2 weeks
- Classes: 3 weeks (most complex)
- Magic Items: 2 weeks
- Monsters: 4 weeks (largest, most variation)
- Tables: 1 week

**Total:** ~17 weeks (4 months) for complete extraction

**Milestones:**
- **Month 1:** Equipment fixed, patterns established, spells extracted
- **Month 2:** Conditions, lineages, classes (prose + table combo proven)
- **Month 3:** Magic items (cross-references working), start monsters
- **Month 4:** Finish monsters, tables, full dataset integration

---

## Summary: Strategic Takeaways

### Key Insights

1. **Equipment bugs reveal systemic patterns** - Not just equipment problems, but lessons for all datasets

2. **Context propagation is universal** - Every dataset needs hierarchical context tracking across pages

3. **Multiple extraction strategies needed** - Tables, structured prose, formatted text all required

4. **Schema flexibility is a feature** - Balance strictness (validation) with adaptability (evolving understanding)

5. **Test early, test often** - Fixtures prevent regression as patterns emerge

6. **Build incrementally** - Fix → Pattern → Apply >> Big Design Up Front

### Decisions Made

| Question | Decision | Rationale |
|----------|----------|-----------|
| Weight format? | **BOTH** - `weight_lb` (number) + `weight_raw` (string) | Copilot compromise: preserve source, enable computation |
| Armor AC schema? | Object with modifiers | Matches game mechanics |
| Schema philosophy? | **Current reality + marked future** | Include optional fields for magic items, clearly documented |
| Nested entry IDs? | Defer until needed | YAGNI - wait for use case |
| Extraction modules? | Separate strategies | Clean separation of concerns |
| Next dataset? | Spells | Validates new pattern, high value |
| Tables timing? | After magic items | Needs items to reference |

### Success Criteria

**Equipment is "done" when:**
- ✅ All 114 items parse correctly
- ✅ AC values correct for armor
- ✅ Weight, versatile, range extracted
- ✅ Schema validates 100%
- ✅ Test coverage >80%

**Patterns are "proven" when:**
- ✅ Second dataset (spells) uses extracted patterns
- ✅ Less than 20% new code per dataset
- ✅ Patterns documented and testable

**Project is "successful" when:**
- ✅ All SRD 5.1 core datasets extracted
- ✅ Datasets cross-reference cleanly
- ✅ Consumer applications can use JSON directly
- ✅ Extraction reproducible and maintainable

---

## Next Steps

**Immediate (This Session):**
1. Review this plan with GPT and Copilot
2. Align on Phase 1 decisions (weight format, AC schema)
3. Prioritize equipment bug fixes

**This Week:**
1. Implement Phase 1 fixes
2. Update tests and schema
3. Validate equipment.json completeness

**Next Week:**
1. Extract reusable patterns (Phase 2)
2. Draft spell extraction approach
3. Begin spell implementation

---

## Appendix: Reference Materials

### Helpful Resources (from review)
- SRD PDF: `rulesets/srd_5_1/raw/SRD_CC_v5.1.pdf`
- Current code: `src/srd_builder/*.py`
- Schemas: `schemas/*.schema.json`
- Templates: `docs/templates/TEMPLATE_*.json`
- Guidance: `docs/terminology.aliases.md`, `docs/AGENTS.md`

### Key Files to Update
- `src/srd_builder/parse_equipment.py` - Main fixes here
- `schemas/equipment.schema.json` - Update for AC object, weight number
- `tests/test_equipment.py` - Add validation tests
- `docs/EXTRACTION_PATTERNS.md` - New file, document patterns

---

**End of Strategic Plan**
