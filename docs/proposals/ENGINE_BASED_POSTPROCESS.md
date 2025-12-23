# Proposal: Engine-Based Postprocess System

**Date:** December 22, 2025
**Status:** Draft Proposal
**Problem:** Proliferation of duplicate postprocess logic across 12 dataset modules
**Impact:** Scalability concerns for multi-version SRD support

---

## Problem Statement

### Current State (v0.18.0)

We have **12 separate postprocess modules**, each implementing similar logic with slight variations:

```
src/srd_builder/postprocess/
├── monsters.py (120 lines)
├── spells.py (89 lines)
├── equipment.py (95 lines)
├── magic_items.py (68 lines)
├── rules.py (78 lines)
├── poisons.py (35 lines)
├── diseases.py (44 lines)
├── conditions.py (44 lines)
├── lineages.py (52 lines)
├── features.py (39 lines)
├── tables.py (48 lines)
└── classes.py (56 lines)
```

**Total:** 768 lines of similar code doing 3 core operations:
1. Generate `simple_name` if missing (using `normalize_id()`)
2. Generate `id` if missing (using `f"{prefix}:{simple_name}"`)
3. Polish text fields (using `polish_text()`)

### Evidence of Duplication

**Every module has this pattern:**
```python
def clean_X_record(record: dict[str, Any]) -> dict[str, Any]:
    if "simple_name" not in record:
        record["simple_name"] = normalize_id(record["name"])
    if "id" not in record:
        record["id"] = f"X:{record['simple_name']}"
    if "description" in record:
        record["description"] = polish_text(record["description"])
    # ... variations for dataset-specific fields
    return record
```

**12 modules × ~40-120 lines each = 768 lines of template code**

### Architectural Concern

**Current trajectory:**
- v0.18.0: 1 SRD version, 12 datasets, 12 postprocess modules (768 lines)
- v0.19.0: 2 SRD versions?, 12 datasets × 2 = 24 modules (1,536 lines)
- v1.0.0: 3 SRD versions?, 12 datasets × 3 = 36 modules (2,304 lines)

**Problem:** We're copying code, not configuring behavior. This doesn't scale.

**User quote:**
> "I've tried this engine route several times, and I keep seeing the sprawl of scripts thinking this isn't what I envisioned. This isn't going to go well when we try this against a new version of the SRD. We'll have another complete copied set of stuff."

---

## Root Cause Analysis

### Why Do We Have 12 Modules?

**Variations in:**
1. **ID prefix:** `monster:`, `spell:`, `equipment:`, etc.
2. **Text field names:** `description`, `higher_levels`, `effects`, `summary`, etc.
3. **Nested structures:** Arrays of traits, proficiencies, actions, etc.
4. **Special cases:** Some datasets have unique transformations

**But 90% of the logic is identical:**
- ID generation algorithm: Same
- Text polishing algorithm: Same
- Structure traversal pattern: Same

### What We're Really Building

We're not building 12 different postprocessors. We're building:

**1 generic record normalizer + 12 configuration files**

But we've expressed it as **12 imperative functions** instead of **1 declarative engine**.

---

## Proposed Solution: Configuration-Driven Engine

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│ BEFORE: Function-based (v0.18.0)                        │
├─────────────────────────────────────────────────────────┤
│ monsters.py    → clean_monster_record(monster)          │
│ spells.py      → clean_spell_record(spell)              │
│ equipment.py   → clean_equipment_record(item)           │
│ ... (12 total modules, 768 lines)                       │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ AFTER: Engine-based (proposal)                          │
├─────────────────────────────────────────────────────────┤
│ engine.py      → clean_record(record, config)           │
│ configs.py     → DATASET_CONFIGS = {...}                │
│ Total: ~200 lines (engine) + ~150 lines (configs)       │
└─────────────────────────────────────────────────────────┘
```

### Core Components

**1. Record Configuration (Declarative YAML)**

**UPDATE:** Initial prototype used Python dataclasses, but YAML is more appropriate for true configuration.

```yaml
# configs/datasets/v5_1/monster.yaml
id_prefix: monster
name_field: name
text_fields:
  - description
  - environment
text_arrays: []
nested_structures:
  actions:
    - name
    - description
  traits:
    - name
    - description
custom_transform: null  # or "srd_builder.postprocess.custom.clean_monsters"

# configs/datasets/v5_1/spell.yaml
id_prefix: spell
name_field: name
text_fields:
  - description
  - higher_levels
text_arrays:
  - components_verbose
nested_structures: {}

# configs/datasets/v5_1/poison.yaml
id_prefix: poison
name_field: name
text_fields:
  - description
text_arrays: []
nested_structures: {}
```

**Why YAML over Python:**
- ✅ Language-agnostic (not tied to Python)
- ✅ Easier to edit (no programming knowledge needed)
- ✅ Clear separation of code (engine) vs config (datasets)
- ✅ Runtime loading (change without code restart)
- ✅ Could support GUI config editor
- ✅ Standard for configuration in modern tools

**Handling Custom Transforms:**
```yaml
# For complex edge cases, reference Python plugin
custom_transform: "srd_builder.postprocess.plugins.clean_table_rows"
```

**Python loader:**
```python
import yaml
from pathlib import Path
from typing import Any

def load_dataset_config(dataset_name: str, version: str = "v5_1") -> dict[str, Any]:
    """Load YAML config for a dataset."""
    config_path = Path(f"configs/datasets/{version}/{dataset_name}.yaml")
    with open(config_path) as f:
        return yaml.safe_load(f)
```

**2. Generic Engine (Imperative)**

```python
# src/srd_builder/postprocess/engine.py

def clean_record(
    record: dict[str, Any],
    config: RecordConfig
) -> dict[str, Any]:
    """
    Generic record normalization engine.

    Applies transformations based on config:
    1. Generate simple_name if missing
    2. Generate id if missing
    3. Polish text fields
    4. Polish nested structures
    5. Apply custom transforms
    """
    # 1. Ensure simple_name
    if "simple_name" not in record:
        record["simple_name"] = normalize_id(record[config.name_field])

    # 2. Ensure id
    if "id" not in record:
        record["id"] = f"{config.id_prefix}:{record['simple_name']}"

    # 3. Polish top-level text fields
    for field in config.text_fields:
        if field in record and isinstance(record[field], str):
            record[field] = polish_text(record[field])

    # 4. Polish text arrays
    for field in config.text_arrays:
        if field in record and isinstance(record[field], list):
            record[field] = [polish_text(item) for item in record[field]]

    # 5. Polish nested structures
    for field, subfields in config.nested_structures.items():
        if field in record and isinstance(record[field], list):
            for item in record[field]:
                for subfield in subfields:
                    if subfield in item and isinstance(item[subfield], str):
                        item[subfield] = polish_text(item[subfield])

    # 6. Custom transformations (escape hatch)
    if config.custom_transform:
        record = config.custom_transform(record)

    return record


def clean_records(
    records: list[dict[str, Any]],
    dataset_name: str
) -> list[dict[str, Any]]:
    """Convenience wrapper for batch processing."""
    config = DATASET_CONFIGS[dataset_name]
    return [clean_record(r, config) for r in records]
```

**3. Backward-Compatible Wrappers (Optional)**

```python
# Keep existing function names for compatibility
def clean_monster_record(monster: dict) -> dict:
    return clean_record(monster, DATASET_CONFIGS["monster"])

def clean_spell_record(spell: dict) -> dict:
    return clean_record(spell, DATASET_CONFIGS["spell"])
```

### Usage Examples

**In build.py:**
```python
# BEFORE (v0.18.0):
from srd_builder.postprocess import clean_monster_record
processed_monsters = [clean_monster_record(m) for m in monsters]

# AFTER (engine-based):
from srd_builder.postprocess import clean_records
processed_monsters = clean_records(monsters, "monster")

# OR keep function names:
from srd_builder.postprocess import clean_monster_record
processed_monsters = [clean_monster_record(m) for m in monsters]
```

---

## Benefits

### 1. **Reduced Code Duplication**

**Current:** 768 lines across 12 modules
**Proposed:** ~200 lines (engine) + ~150 lines (configs) = **350 lines total**

**Reduction:** 54% fewer lines, all logic in one place

### 2. **Multi-Version SRD Support**

**Current approach (would require):**
```
postprocess/
├── v5_1/
│   ├── monsters.py (120 lines)
│   ├── spells.py (89 lines)
│   └── ... (10 more)
├── v5_2/
│   ├── monsters.py (120 lines, mostly copied)
│   ├── spells.py (89 lines, mostly copied)
│   └── ... (10 more)
```

**Engine approach:**
```
postprocess/
├── engine.py (200 lines, shared)
├── configs/
│   ├── v5_1.py (150 lines)
│   └── v5_2.py (160 lines, only differences)
```

**For 3 SRD versions:**
- Current: 768 × 3 = **2,304 lines**
- Engine: 200 + (150 × 3) = **650 lines** (72% reduction)

### 3. **Easier Testing**

**Current:** Test 12 separate functions
```python
def test_clean_monster_record(): ...
def test_clean_spell_record(): ...
# ... 12 tests
```

**Engine:** Test 1 engine + 12 configs
```python
def test_clean_record_engine():
    # Test engine with various configs

@pytest.mark.parametrize("dataset", DATASET_CONFIGS.keys())
def test_config_completeness(dataset):
    # Ensure all configs have required fields
```

### 4. **Centralized Bug Fixes**

**Current:** Bug in text polishing → Fix in 12 places
**Engine:** Bug in text polishing → Fix in 1 place (engine)

### 5. **Clear Extension Point**

**Adding new dataset:**

**Current (v0.18.0):**
1. Copy postprocess/monsters.py → postprocess/new_dataset.py
2. Modify clean_monster_record → clean_new_dataset_record
3. Update imports, exports
4. ~40-120 lines of code

**Engine:**
1. Add config to DATASET_CONFIGS
2. ~8-15 lines of config

```python
"new_dataset": RecordConfig(
    id_prefix="new_dataset",
    text_fields=["description"],
),
```

---

## Challenges & Mitigations

### Challenge 1: Complex Special Cases

**Problem:** Some datasets have unique transformations not covered by config

**Example:** Monsters have CR calculations, spells have level parsing

**Solution:** Escape hatch in config
```python
def _custom_monster_transform(monster: dict) -> dict:
    # Special monster logic
    monster["cr_numeric"] = calculate_cr(monster["challenge_rating"])
    return monster

"monster": RecordConfig(
    id_prefix="monster",
    text_fields=["description"],
    custom_transform=_custom_monster_transform,
)
```

**Guideline:** Use custom_transform sparingly. If >3 datasets need same transform, add to engine.

### Challenge 2: Config Complexity

**Problem:** Deeply nested structures might make configs unreadable

**Example:** Spells have multiple nested levels

**Mitigation:**
1. Start simple (text_fields, text_arrays only)
2. Add complexity incrementally as patterns emerge
3. Document config schema clearly

### Challenge 3: Migration Effort

**Problem:** 12 existing modules work, why change?

**Mitigation:**
1. Create engine alongside existing modules (backward compatible)
2. Migrate one dataset at a time
3. Keep wrapper functions if needed for compatibility

**Migration path:**
- v0.18.0: Current state (12 modules)
- v0.18.1: Add engine + migrate 3 datasets
- v0.18.2: Migrate remaining 9 datasets
- v0.19.0: Remove old modules (breaking change)

---

## Prototype Implementation

### Phase 1: Core Engine (Minimal)

**Goal:** Prove concept with 3 simple datasets (poisons, diseases, conditions)

**Deliverables:**
1. `src/srd_builder/postprocess/engine.py` (~100 lines)
2. `src/srd_builder/postprocess/configs.py` (~50 lines)
3. Tests for engine + 3 configs
4. Benchmarks (performance comparison)

**Success criteria:**
- 3 datasets pass existing golden tests
- No performance degradation
- Code reduction: 123 lines → ~150 lines (with engine overhead)

### Phase 2: Complex Datasets

**Goal:** Handle nested structures (monsters, spells, classes)

**Deliverables:**
1. Extend engine with nested structure support
2. Add 3 complex dataset configs
3. Custom transform examples

**Success criteria:**
- All 12 datasets pass golden tests
- Code reduction: 768 lines → ~350 lines (54%)

### Phase 3: Multi-Version Support

**Goal:** Demonstrate SRD version config separation

**Deliverables:**
1. `configs/v5_1.py` (current configs)
2. `configs/v5_2.py` (hypothetical future SRD)
3. Version selection in build.py

**Success criteria:**
- Can build from multiple SRD versions
- Shared engine code, separate configs

---

## Recommendation

### Immediate Action (v0.19.0)

**Do NOT implement engine yet.** Instead:

1. **Document this proposal** (this document)
2. **Add to roadmap** as v0.20.0 or later
3. **Focus v0.19.0 on third-party review** (current plan)

**Rationale:**
- v0.18.0 just established modular pattern
- Let it stabilize before another refactor
- Get external validation first (v0.19.0)
- Engine-based refactor is v0.20.0+ work

### Future Implementation (v0.20.0+)

**When:** After v0.19.0 external review, before multi-version support

**Approach:**
1. **Spike:** 1-2 day prototype with 3 datasets
2. **Evaluate:** Compare complexity, readability, maintainability
3. **Decide:** Go/no-go based on team consensus
4. **Migrate:** If approved, incremental migration over 2-3 versions

**Decision criteria:**
- ✅ Code reduction >40%
- ✅ No performance degradation
- ✅ Configs are readable (not XML-like complexity)
- ✅ Team agrees pattern is maintainable

---

## Alternative Approaches Considered

### Alternative 1: Keep Current Approach

**Pros:** Works, established pattern, no migration cost
**Cons:** Doesn't scale to multi-version SRD, high duplication

**When to choose:** If we never support multiple SRD versions

### Alternative 2: Class-Based (OOP)

```python
class RecordPostprocessor:
    def __init__(self, config: RecordConfig):
        self.config = config

    def clean(self, record: dict) -> dict:
        # ... engine logic

monster_processor = RecordPostprocessor(MONSTER_CONFIG)
monster_processor.clean(monster)
```

**Pros:** More traditional OOP, encapsulation
**Cons:** More boilerplate, doesn't add value over function + config

**When to choose:** If we need stateful processing (we don't)

### Alternative 3: Schema-Driven (Declarative)

```python
MONSTER_SCHEMA = {
    "id_prefix": "monster",
    "fields": {
        "description": {"type": "text", "polish": True},
        "actions": {"type": "array", "item_schema": {...}},
    }
}
```

**Pros:** Most declarative, JSON-serializable
**Cons:** Very complex for nested structures, reinvents JSON Schema

**When to choose:** If we need runtime schema validation or GUI config

---

## Open Questions

1. **Performance:** Does config lookup add measurable overhead?
   - **Answer:** Benchmark in Phase 1 prototype

2. **Readability:** Are configs easier to understand than functions?
   - **Answer:** Get team feedback on prototype

3. **Flexibility:** Can engine handle all 12 current datasets?
   - **Answer:** Phase 2 will prove or disprove

4. **Multi-version:** Do SRD versions differ enough to need separate configs?
   - **Answer:** Unknown until we see SRD 5.2 or 6.0

5. **Migration cost:** How much work to convert 12 modules?
   - **Answer:** Phase 1 + Phase 2 estimates = 3-5 days total

---

## References

**Related documents:**
- [ARCHITECTURE.md](../ARCHITECTURE.md) - Current modular pattern
- [v0.18.0_CLEANUP_REPORT.md](../reports/v0.18.0_CLEANUP_REPORT.md) - Duplication analysis

**Relevant code:**
- `src/srd_builder/postprocess/*.py` - 12 current modules (768 lines)
- `src/srd_builder/postprocess/ids.py` - Shared normalize_id utility
- `src/srd_builder/postprocess/text.py` - Shared polish_text utility

**Inspiration:**
- Django ORM field configuration
- FastAPI route configuration
- Pydantic model definitions

---

## Appendix: Current Duplication Metrics

```
Module          Lines   ID Gen   Text Polish   Nested   Custom
─────────────────────────────────────────────────────────────
monsters.py     120     ✓        ✓             ✓        CR calc
spells.py       89      ✓        ✓             ✓        Level parse
equipment.py    95      ✓        ✓             ✓        Cost parse
magic_items.py  68      ✓        ✓             ✗        Rarity
rules.py        78      ✓        ✓             ✗        —
poisons.py      35      ✓        ✓             ✗        —
diseases.py     44      ✓        ✓             ✓        Effects
conditions.py   44      ✓        ✓             ✓        Effects
lineages.py     52      ✓        ✓             ✓        Traits
features.py     39      ✓        ✓             ✗        —
tables.py       48      ✓        ✓             ✓        Rows
classes.py      56      ✓        ✓             ✓        Profs
─────────────────────────────────────────────────────────────
TOTAL           768     12/12    12/12         8/12     4/12
```

**Observations:**
- 100% of modules do ID generation (identical logic)
- 100% of modules do text polishing (identical logic)
- 67% have nested structures (similar pattern, different field names)
- 33% have custom logic (would need escape hatch)

**Estimated consolidation:**
- Engine core: ~150 lines (ID gen, text polish, nested traversal)
- Configs: ~12 × 10-15 lines = ~150 lines
- Custom transforms: ~50 lines (4 datasets × ~12 lines each)
- **Total: ~350 lines** vs current 768 lines (54% reduction)

---

## Decision Log

**2024-12-22:** Proposal created, added to roadmap discussion
**Status:** Awaiting team review and v0.19.0 completion
**Next step:** Prototype Phase 1 (3 simple datasets) for evaluation
