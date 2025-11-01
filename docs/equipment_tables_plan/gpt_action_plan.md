# GPT Action Plan: Equipment Fixes + Strategic Foundation

**Date:** 2025-11-01
**Status:** Ready for implementation
**Decisions:** Aligned with Copilot's pragmatic approach + strategic extensions

---

## Executive Summary

Fix 5 equipment bugs this week while establishing reusable patterns for future datasets (spells, lineages, classes). Schema philosophy: **current reality + clearly marked future fields**.

---

## Phase 1: Equipment Bug Fixes (This Week)

### Priority Order

#### 1. Armor AC Column Detection (CRITICAL - 2 hours)
**Problem:** Getting cost (50) instead of AC (13)

**Root Cause:** Fixed column indices don't work across armor types

**Solution:**
```python
# In extract_equipment.py or parse_equipment.py

def detect_armor_columns(table_rows):
    """
    Parse header row to build column map.
    More robust than assuming column[2] = AC.
    """
    if not table_rows:
        return None

    header_row = table_rows[0]  # First row is usually headers
    column_map = {}

    for idx, cell in enumerate(header_row):
        cell_lower = cell.lower().strip()

        if 'armor class' in cell_lower or cell_lower == 'ac':
            column_map['ac'] = idx
        elif 'cost' in cell_lower:
            column_map['cost'] = idx
        elif 'weight' in cell_lower:
            column_map['weight'] = idx
        elif 'strength' in cell_lower:
            column_map['strength'] = idx
        elif 'stealth' in cell_lower:
            column_map['stealth'] = idx

    return column_map

# Usage in parser
def parse_armor_row(row, category):
    columns = detect_armor_columns([row])  # Or pass header separately

    ac_value = row[columns['ac']] if 'ac' in columns else None
    cost_value = row[columns['cost']] if 'cost' in columns else None

    return {
        'armor_class': {
            'base': parse_ac(ac_value),
            'dex_bonus': get_dex_bonus_rule(category),
            'max_bonus': get_max_bonus(category)
        },
        'cost': parse_cost(cost_value),
        # ...
    }
```

**Test Cases:**
```python
def test_armor_ac_parsing():
    """Chain Shirt should have AC 13, not 50"""
    item = find_item_by_id('item:chain-shirt')
    assert item['armor_class']['base'] == 13
    assert item['cost']['amount'] == 50

def test_breastplate_ac():
    """Breastplate should have AC 14, not 400"""
    item = find_item_by_id('item:breastplate')
    assert item['armor_class']['base'] == 14
    assert item['cost']['amount'] == 400
```

---

#### 2. Weight Parsing (HIGH - 1 hour)
**Problem:** Schema expects number, storing string "10 lb."

**Solution:** Emit BOTH formats per compromise
```python
# In parse_equipment.py

def parse_weight(weight_str):
    """
    Parse weight to number (pounds) while preserving original.

    Returns:
        tuple: (weight_lb: float|None, weight_raw: str)

    Examples:
        "10 lb." → (10.0, "10 lb.")
        "1/4 lb." → (0.25, "1/4 lb.")
        "—" → (None, "—")
    """
    if not weight_str or weight_str.strip() in ['—', '–', 'n/a']:
        return (None, weight_str)

    weight_raw = weight_str.strip()

    try:
        # Handle fractions: "1/4 lb." → 0.25
        if '/' in weight_raw:
            fraction_part = weight_raw.split('lb')[0].strip()
            numerator, denominator = fraction_part.split('/')
            weight_lb = float(numerator) / float(denominator)
            return (weight_lb, weight_raw)

        # Handle decimals: "10.5 lb." → 10.5
        numeric_part = weight_raw.split('lb')[0].strip()
        weight_lb = float(numeric_part)
        return (weight_lb, weight_raw)

    except (ValueError, ZeroDivisionError):
        # Parsing failed, return None for number
        return (None, weight_raw)

# Usage
weight_lb, weight_raw = parse_weight(row['weight'])
item['weight_lb'] = weight_lb
item['weight_raw'] = weight_raw
```

**Test Cases:**
```python
def test_weight_parsing():
    assert parse_weight("10 lb.") == (10.0, "10 lb.")
    assert parse_weight("1/4 lb.") == (0.25, "1/4 lb.")
    assert parse_weight("—") == (None, "—")
    assert parse_weight("15.5 lb.") == (15.5, "15.5 lb.")

def test_longsword_weight():
    item = find_item_by_id('item:longsword')
    assert item['weight_lb'] == 3.0
    assert item['weight_raw'] == "3 lb."
```

---

#### 3. Versatile Damage Extraction (HIGH - 1.5 hours)
**Problem:** Properties has "versatile (1d10)" but field not populated

**Solution:**
```python
# In parse_equipment.py

def extract_versatile_damage(properties):
    """
    Parse 'versatile (1d10)' from properties array.

    Args:
        properties: List of property strings

    Returns:
        dict|None: {"dice": "1d10"} or None

    Note: Damage type is implicit (same as base damage)
    """
    if not properties:
        return None

    for prop in properties:
        # Match: "versatile (1d10)" or "Versatile (2d6)"
        match = re.search(
            r'versatile\s*\(([0-9]+d[0-9]+)\)',
            prop,
            re.IGNORECASE
        )
        if match:
            return {"dice": match.group(1)}

    return None

# Usage in parser
properties = parse_properties(row['properties'])
versatile = extract_versatile_damage(properties)

weapon = {
    'properties': properties,
    'versatile_damage': versatile,
    # ...
}
```

**Test Cases:**
```python
def test_versatile_extraction():
    props = ["finesse", "versatile (1d10)"]
    result = extract_versatile_damage(props)
    assert result == {"dice": "1d10"}

def test_longsword_versatile():
    item = find_item_by_id('item:longsword')
    assert item['versatile_damage'] == {"dice": "1d10"}
    assert "versatile" in [p.lower() for p in item['properties']]
```

---

#### 4. Range Extraction (MEDIUM - 1.5 hours)
**Problem:** "thrown (range 20/60)" stored as string

**Solution:**
```python
# In parse_equipment.py

def extract_range(properties):
    """
    Parse 'thrown (range 20/60)' or 'range (80/320)'.

    Args:
        properties: List of property strings

    Returns:
        dict|None: {"normal": 20, "long": 60} or None
    """
    if not properties:
        return None

    for prop in properties:
        # Match: "range (20/60)" or "thrown (range 20/60)"
        match = re.search(
            r'range\s*\((\d+)/(\d+)\)',
            prop,
            re.IGNORECASE
        )
        if match:
            return {
                "normal": int(match.group(1)),
                "long": int(match.group(2))
            }

    return None

# Usage
weapon['range'] = extract_range(properties)
```

**Test Cases:**
```python
def test_range_extraction():
    props = ["thrown (range 20/60)"]
    assert extract_range(props) == {"normal": 20, "long": 60}

def test_dagger_range():
    item = find_item_by_id('item:dagger')
    assert item['range'] == {"normal": 20, "long": 60}
```

---

#### 5. Armor Category Detection (LOW - 2 hours)
**Problem:** Leather marked as "medium" (should be "light")

**Root Cause:** Subsection headers not reliably detected

**Solution:**
```python
# In extract_equipment.py

def detect_armor_category(page_blocks):
    """
    Look for subsection headers: "Light Armor", "Medium Armor", "Heavy Armor"

    Returns:
        str|None: "light", "medium", "heavy", or None
    """
    for block in page_blocks:
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                size = span.get("size", 0)
                text = span.get("text", "").strip().lower()

                # Subsection headers are 13-14pt
                if 13 < size < 15:
                    if "light armor" in text:
                        return "light"
                    elif "medium armor" in text:
                        return "medium"
                    elif "heavy armor" in text:
                        return "heavy"

    return None

# Usage in context tracker
class ContextTracker:
    def __init__(self):
        self.section = None
        self.armor_category = None

    def update_from_page(self, page):
        blocks = page.get_text("dict")["blocks"]

        # Update armor category if found
        detected_category = detect_armor_category(blocks)
        if detected_category:
            self.armor_category = detected_category
```

**Test Cases:**
```python
def test_armor_categories():
    """Verify armor items have correct categories"""
    leather = find_item_by_id('item:leather')
    assert leather['sub_category'] == 'light'

    chain_shirt = find_item_by_id('item:chain-shirt')
    assert chain_shirt['sub_category'] == 'medium'

    plate = find_item_by_id('item:plate')
    assert plate['sub_category'] == 'heavy'
```

---

### Schema Update Required

Apply the **schema compromise** from `schema_compromise_recommendation.md`:

**Key changes:**
1. Add `weight_lb` (number) and `weight_raw` (string)
2. Change `armor_class` from integer to object
3. Add `range` object for weapons
4. Mark future fields (variant_of, is_magic, etc.) with "FUTURE:" in description
5. Set `is_magic: false` as default for all base equipment

**File:** `schemas/equipment.schema.json`

---

### Implementation Checklist

```markdown
- [ ] 1. Update schema to v1.1.0 (hybrid approach)
- [ ] 2. Implement column header detection for armor
- [ ] 3. Add weight parsing (emit both formats)
- [ ] 4. Extract versatile_damage from properties
- [ ] 5. Extract range from properties
- [ ] 6. Fix armor category detection
- [ ] 7. Update parse_equipment.py to use new functions
- [ ] 8. Run schema validation on output
- [ ] 9. Add test cases for each fix
- [ ] 10. Validate all 114 items parse correctly
```

**Estimated Time:** 6-8 hours total

---

## Phase 2: Extract Reusable Patterns (Next Week)

Once equipment bugs are fixed, extract patterns for future datasets.

### 2.1 Create Context Tracker (2 hours)

**Purpose:** Track hierarchical context (section/subsection) across pages

**File:** `src/srd_builder/context_tracker.py`

```python
"""
Context tracking for multi-page extraction.
Maintains section/subsection state as parser moves through PDF.
"""

class ContextTracker:
    """Track hierarchical context across PDF pages"""

    def __init__(self):
        self.section = None       # "Armor", "Weapons", "Barbarian", "Dwarf"
        self.subsection = None    # "Light Armor", "Path of Berserker", "Hill Dwarf"
        self.page = None
        self.context_history = []

    def update_from_headers(self, page_num, headers):
        """
        Update context when section/subsection headers detected.

        Args:
            page_num: Current page number
            headers: Dict with 'section' and/or 'subsection' keys
        """
        self.page = page_num

        if 'section' in headers:
            self.section = headers['section']
            self.subsection = None  # Reset subsection

        if 'subsection' in headers:
            self.subsection = headers['subsection']

        self.context_history.append({
            'page': page_num,
            'section': self.section,
            'subsection': self.subsection
        })

    def get_current_context(self):
        """Get current hierarchical context"""
        return {
            'section': self.section,
            'subsection': self.subsection,
            'page': self.page
        }

    def in_section(self, section_name):
        """Check if currently in a specific section"""
        return self.section and section_name.lower() in self.section.lower()
```

**Usage:**
```python
# In extract_equipment.py
tracker = ContextTracker()

for page_num, page in enumerate(pdf_pages):
    headers = detect_headers(page)
    tracker.update_from_headers(page_num, headers)

    # Use context when parsing items
    context = tracker.get_current_context()
    items = extract_items_from_page(page, context)
```

---

### 2.2 Create Extraction Strategies (3 hours)

**Purpose:** Separate extraction logic for different content types

**Files:**
- `src/srd_builder/extraction/table_extractor.py` (refactor from equipment)
- `src/srd_builder/extraction/structured_prose_extractor.py` (for spells)
- `src/srd_builder/extraction/formatted_text_extractor.py` (for lineages, conditions)

**Structure:**
```python
# extraction/base.py
class BaseExtractor:
    """Base class for extraction strategies"""

    def extract(self, page, context):
        """Extract content from page given context"""
        raise NotImplementedError

# extraction/table_extractor.py
class TableExtractor(BaseExtractor):
    """Extract structured data from PDF tables"""

    def extract(self, page, context):
        tables = page.find_tables()
        # ... existing equipment table logic
        return items

# extraction/structured_prose_extractor.py
class StructuredProseExtractor(BaseExtractor):
    """Extract from formatted prose (spells, feats)"""

    def extract(self, page, context):
        # Detect bold names + header lines + descriptions
        # Return structured entries
        pass

# extraction/formatted_text_extractor.py
class FormattedTextExtractor(BaseExtractor):
    """Extract from bold headers + text blocks (lineages, conditions)"""

    def extract(self, page, context):
        # Detect bold headers as entry boundaries
        # Capture text until next header
        pass
```

---

### 2.3 Document Patterns (1 hour)

**File:** `docs/EXTRACTION_PATTERNS.md`

```markdown
# Extraction Patterns

## Overview
Reusable patterns for extracting different content types from SRD PDF.

## Pattern 1: Context Tracking
Used by: All datasets
Purpose: Maintain section/subsection state across pages
Implementation: `ContextTracker` class

## Pattern 2: Table Extraction
Used by: Equipment, class level tables, treasure tables
Purpose: Extract structured data from PDF tables
Implementation: `TableExtractor` class

## Pattern 3: Structured Prose
Used by: Spells, feats, magic items
Purpose: Extract from consistent format (bold name + header + description)
Implementation: `StructuredProseExtractor` class

## Pattern 4: Formatted Text
Used by: Lineages, conditions, backgrounds
Purpose: Extract from bold headers + prose blocks
Implementation: `FormattedTextExtractor` class

## Pattern 5: Mixed Content
Used by: Classes (tables + prose features)
Purpose: Combine multiple extraction strategies
Implementation: Use multiple extractors in sequence
```

---

## Phase 3: Validate with Second Dataset (Week After)

**Recommended:** Spells (validates structured prose extraction)

**Why spells:**
- Different enough from tables to test patterns
- Large dataset (~300 items) for thoroughness
- High-value dataset for consumers

**Alternative:** Conditions (simpler, quicker win)

---

## Success Criteria

### Equipment is "Done" when:
- ✅ All 114 items parse correctly
- ✅ AC values correct for all armor
- ✅ Weight, versatile, range extracted
- ✅ Armor categories (light/medium/heavy) correct
- ✅ Schema validates 100%
- ✅ Test coverage >80% for parse functions

### Patterns are "Proven" when:
- ✅ Second dataset uses extracted patterns
- ✅ Less than 20% new code for second dataset
- ✅ Patterns documented and testable

---

## Testing Strategy

### Unit Tests (Per Function)
```python
# tests/test_parse_equipment.py

def test_weight_parsing():
    """Test weight parsing edge cases"""
    assert parse_weight("10 lb.") == (10.0, "10 lb.")
    assert parse_weight("1/4 lb.") == (0.25, "1/4 lb.")
    assert parse_weight("—") == (None, "—")

def test_versatile_extraction():
    """Test versatile damage extraction"""
    props = ["finesse", "versatile (1d10)"]
    assert extract_versatile_damage(props) == {"dice": "1d10"}

def test_range_extraction():
    """Test range extraction"""
    props = ["thrown (range 20/60)"]
    assert extract_range(props) == {"normal": 20, "long": 60}
```

### Integration Tests (Full Item)
```python
def test_longsword_complete():
    """Verify longsword parses correctly"""
    item = find_item_by_id('item:longsword')

    assert item['id'] == 'item:longsword'
    assert item['name'] == 'Longsword'
    assert item['category'] == 'weapon'
    assert item['damage'] == {"dice": "1d8", "type": "slashing"}
    assert item['versatile_damage'] == {"dice": "1d10"}
    assert item['weight_lb'] == 3.0
    assert item['cost'] == {"amount": 15, "currency": "gp"}

def test_chain_shirt_ac():
    """Verify chain shirt AC correct (was bug)"""
    item = find_item_by_id('item:chain-shirt')

    assert item['armor_class']['base'] == 13  # Not 50!
    assert item['cost']['amount'] == 50
```

### Schema Validation Test
```python
def test_schema_validation():
    """All equipment validates against schema"""
    import jsonschema

    data = load_json('dist/srd_5_1/data/equipment.json')
    schema = load_json('schemas/equipment.schema.json')

    try:
        jsonschema.validate(data, schema)
    except jsonschema.ValidationError as e:
        pytest.fail(f"Schema validation failed: {e}")
```

---

## Coordination with Copilot

**Copilot's Concerns Addressed:**

1. **"Don't refactor until bugs fixed"**
   → Phase 1 focuses 100% on bug fixes, no refactoring

2. **"Don't plan too far ahead"**
   → Phase 2 extracts patterns from working code, not speculation
   → Phase 3 validates patterns with real dataset

3. **"Focus on what's parsing now"**
   → All immediate work is equipment-focused
   → Future fields clearly marked in schema

**Workflow:**
1. Implement Phase 1 fixes (this week)
2. Review with Copilot after each fix
3. Validate equipment.json completeness
4. Then move to Phase 2 (pattern extraction)

---

## Files to Create/Update

### Create New:
- `src/srd_builder/context_tracker.py` (Phase 2)
- `src/srd_builder/extraction/base.py` (Phase 2)
- `src/srd_builder/extraction/table_extractor.py` (Phase 2)
- `src/srd_builder/extraction/structured_prose_extractor.py` (Phase 2)
- `src/srd_builder/extraction/formatted_text_extractor.py` (Phase 2)
- `docs/EXTRACTION_PATTERNS.md` (Phase 2)

### Update Existing:
- `schemas/equipment.schema.json` (Phase 1 - use compromise schema)
- `src/srd_builder/parse_equipment.py` (Phase 1 - add parsing functions)
- `src/srd_builder/extract_equipment.py` (Phase 1 - fix column detection)
- `tests/test_equipment.py` (Phase 1 - add test cases)

---

## Questions Before Starting?

1. Do you have the actual code files to reference? (parse_equipment.py, extract_equipment.py)
2. Are there existing tests to extend?
3. Any constraints on library usage? (regex is fine?)
4. Preferred error handling approach? (log warnings vs raise exceptions)

---

## Summary: Next Actions

**Immediate (Today/Tomorrow):**
1. Review this plan with Copilot
2. Align on schema compromise approach
3. Start Phase 1 implementation

**This Week:**
1. Fix all 5 equipment bugs
2. Update schema to v1.1.0
3. Validate equipment.json

**Next Week:**
1. Extract reusable patterns (Phase 2)
2. Document patterns
3. Prepare for spells dataset

**Success Metric:** Equipment parsing complete, patterns ready for reuse
