# SRD-Builder Architecture

**Version:** v0.4.2
**Purpose:** Technical reference documenting design decisions, tooling choices, and lessons learned

---

## Overview

srd-builder extracts structured data from PDF documents (specifically SRD 5.1) and produces clean, validated JSON datasets. The project prioritizes **reproducibility**, **provenance**, and **clean separation of concerns**.

### Design Philosophy

1. **Pure Functions**: Parsing and processing modules have no I/O or side effects
2. **Single Responsibility**: Each module does one thing well
3. **Determinism**: Same input → same output (no timestamps in datasets)
4. **Provenance**: Track everything back to source PDF (page numbers, hash)
5. **Clean Boundaries**: Extract → Parse → Postprocess → Index → Validate

---

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ INPUT: rulesets/srd_5_1/raw/SRD_CC_v5.1.pdf                │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ EXTRACT (extract_monsters.py)                              │
│ • PDF text extraction with font/position metadata          │
│ • Detect monster headers (18pt GillSans-SemiBold)          │
│ • Column splitting (left/right at 306pt midpoint)          │
│ • Cross-page monster handling                              │
│ • Output: monsters_raw.json (verbatim blocks + metadata)   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ PARSE (parse_monsters.py)                                  │
│ • Field mapping: AC, HP, Speed, Ability Scores             │
│ • Type-line parsing: Size, Type, Alignment                 │
│ • Action/Trait/Legendary Action extraction                 │
│ • Pure function: list[dict] → list[dict]                   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ POSTPROCESS (postprocess.py)                               │
│ • Normalize legendary actions (add name to entries)        │
│ • Fix CR formatting (handle fractions, "0", edge cases)    │
│ • Clean defense fields (arrays, deduplication)             │
│ • Generate IDs (monster:aboleth from name)                 │
│ • Text cleanup (remove artifacts, normalize whitespace)    │
│ • Pure function: dict → dict                               │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ INDEX (indexer.py)                                         │
│ • Build lookup maps: by_name, by_cr, by_type, by_size     │
│ • Generate stats: unique counts, distributions             │
│ • Pure function: list[dict] → dict                         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ BUILD (build.py)                                           │
│ • Orchestrates pipeline (only I/O module)                  │
│ • Generates meta.json with provenance                      │
│ • Writes datasets to dist/                                 │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ VALIDATE (validate.py)                                     │
│ • JSON Schema validation (monster.schema.json)             │
│ • PDF hash verification                                    │
│ • Build report checks                                      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ OUTPUT: dist/srd_5_1/                                      │
│ • meta.json (license, provenance, page index)              │
│ • build_report.json (build metadata)                       │
│ • data/monsters.json (296 normalized monsters)             │
│ • data/index.json (lookup tables)                          │
└─────────────────────────────────────────────────────────────┘
```

---

## Technology Choices

### PDF Extraction: PyMuPDF (fitz)

**Why PyMuPDF over alternatives?**

- **Font metadata access**: Critical for detecting monster names (18pt headers)
- **Precise positioning**: X/Y coordinates for column detection
- **Performance**: Faster than pdfplumber for large documents
- **Mature**: Well-tested, stable API

**What we learned:**
- Font size is the most reliable signal for header detection (18pt vs 9.84pt body text)
- Column detection via fixed midpoint (306pt) works better than heuristics
- Cross-page monsters require buffering all lines before grouping
- Page numbers in extraction are essential for provenance

**Alternatives considered:**
- ❌ `pdfplumber`: Better for tables, but slower and less font metadata
- ❌ `PyPDF2`: Too low-level, would require more custom parsing
- ❌ `camelot`: Overkill for our needs, focused on table extraction

### Schema Validation: jsonschema

**Why jsonschema?**

- Industry standard (JSON Schema Draft 2020-12)
- Comprehensive validation (types, required fields, patterns)
- Good error messages for debugging
- Future-proof: Can validate nested structures as we add content types

**What we learned:**
- Schema validation catches 90% of parsing bugs early
- `additionalProperties: false` prevents field typos
- Required vs optional fields need careful consideration
- Schemas serve as both validation and documentation

### Testing: pytest

**Why pytest over unittest?**

- More Pythonic (no class boilerplate)
- Better fixtures (reusable test data)
- Cleaner assertions (no `assertEqual` verbosity)
- Great plugin ecosystem (pytest-cov for coverage)

**Test Strategy:**
```
tests/
├── test_extract_*.py        # PDF extraction (10 tests)
├── test_parse_*.py           # Field parsing (minimal, covered by golden)
├── test_postprocess_*.py     # Normalization (15 tests)
├── test_indexer*.py          # Index building (3 tests)
├── test_build_pipeline.py    # End-to-end (1 test)
├── test_validate_*.py        # Schema validation (10 tests)
├── test_golden_monsters.py   # Golden file comparison (1 test)
└── fixtures/                 # Test data (raw + normalized)
```

**What we learned:**
- Golden file testing catches regressions across the entire pipeline
- Fixtures split (raw vs normalized) isolates parsing from postprocessing
- Mock PDF extraction in tests to avoid PDF dependency
- Small, focused unit tests beat large integration tests for debugging

### Code Quality: Ruff + Black

**Why Ruff over Flake8/pylint?**

- **Speed**: 10-100x faster (Rust implementation)
- **Comprehensive**: Replaces flake8, isort, pyupgrade
- **Modern**: Supports Python 3.11+ syntax
- **Deterministic**: Consistent formatting every time

**What we learned:**
- `ruff check .` catches import issues, unused vars, complexity
- `black .` handles all formatting (no bikeshedding)
- Pre-commit hooks ensure quality before commit
- Config in `pyproject.toml` keeps tooling centralized

---

## Key Design Decisions

### 1. Pure Parsing Functions

**Decision:** `parse_monsters.py` and `postprocess.py` are pure functions (no I/O).

**Rationale:**
- Testable without file system
- Composable (can chain or reorder)
- Easier to reason about (no hidden state)
- Parallelizable (future optimization)

**Trade-off:** Build orchestration in `build.py` is slightly more complex, but worth it for purity.

### 2. Separate Extract vs Parse

**Decision:** Two-stage pipeline (extract → parse) instead of one-pass parsing.

**Rationale:**
- **Debugging**: Can inspect `monsters_raw.json` to see what PDF extraction produced
- **Iteration**: Can improve parsing without re-extracting PDF (slow)
- **Provenance**: Raw extraction preserves font/position metadata
- **Testing**: Can test parsing with fixtures independent of PDF

**What we learned:**
- Raw extraction should be **verbatim** (no interpretation)
- Parsing should be **lenient** (handle variations gracefully)
- Postprocessing should be **strict** (enforce consistency)

### 3. Structured Fields (AC, HP, Speed)

**Decision:** Use structured objects instead of primitives.

**Example:**
```json
"armor_class": {"value": 17, "source": "natural armor"}
"hit_points": {"average": 135, "formula": "18d10+36"}
"speed": {"walk": 30, "fly": {"value": 50, "condition": "hover"}}
```

**Rationale:**
- **Richer data**: Preserves source information (AC from armor vs spell)
- **Backwards compatible**: Consumers can flatten if needed (`ac.value`)
- **Future-proof**: Easy to add fields (AC modifiers, HP temp, etc.)
- **No data loss**: Original formula preserved for recalculation

**Trade-off:** Slightly more complex to consume, but much more useful.

### 4. Page Number Provenance

**Decision:** Every monster records source page numbers from PDF.

**Rationale:**
- **Traceability**: Can verify any extracted data against source
- **License compliance**: Shows exactly where content came from
- **Debugging**: When parsing fails, know which page to check
- **Quality**: Can detect cross-page monsters (e.g., Worg spans 393-394)

**Implementation:**
- Extraction captures page numbers as array: `"pages": [261]`
- Postprocessing flattens to single value: `"page": 261`
- Meta.json aggregates: `"monsters": {"start": 261, "end": 394}`

### 5. Deterministic Output

**Decision:** No timestamps in datasets, sorted arrays, stable IDs.

**Rationale:**
- **Git-friendly**: Only real changes trigger diffs
- **Testing**: Golden files can do byte-for-byte comparison
- **Reproducible**: Same PDF → same JSON every time
- **CI**: Builds are cacheable and verifiable

**What we learned:**
- Timestamps belong in `build_report.json` only (not datasets)
- Sort arrays by name/id (not insertion order)
- Use stable ID generation (slug from name, not UUID)
- Avoid floating point where possible (use fractions for CR)

### 6. Meta.json Separation

**Decision:** Two metadata files with different purposes.

**Files:**
- `rulesets/srd_5_1/raw/pdf_meta.json`: Input validation (PDF hash)
- `dist/srd_5_1/meta.json`: Consumer metadata (license, provenance, file manifest)

**Rationale:**
- **Clear intent**: Input validation vs output documentation
- **Provenance**: Rich metadata in output for compliance
- **Separation**: Don't pollute raw input directory with output metadata

**What we learned:**
- Consumers need license, page index, extraction status
- PDF hash verification catches corrupted/wrong source files
- Different audiences need different metadata (builder vs consumer)

---

## Lessons Learned

### PDF Extraction

1. **Font size is gold**: 18pt headers are 100% reliable for monster detection
2. **Fixed midpoint wins**: 306pt column split works better than dynamic detection
3. **Buffer everything**: Must collect all pages before grouping (cross-page monsters)
4. **Preserve metadata**: Font/position/page data crucial for debugging
5. **Warnings are valuable**: Track parsing issues without failing builds

### Field Parsing

1. **Type-line is tricky**: "Medium humanoid (any race), any alignment" has many formats
2. **AC sources matter**: "17 (natural armor)" vs "17" needs structure
3. **HP formulas vary**: Some have "+36", some have "plus 36", handle both
4. **Speed conditions**: Preserve `(hover)` for gameplay relevance
5. **Ability scores**: Constructs have 1s for mental stats (not 0)

### Postprocessing

1. **Legendary actions need names**: Add monster name to each legendary action
2. **CR edge cases**: "0", "1/8", "1/4", "1/2" all need special handling
3. **Defense deduplication**: Remove duplicate immunities/resistances
4. **ID generation**: Lowercase, snake_case, ASCII-only for stability
5. **Text cleanup**: Remove PDF artifacts ("\n\n", extra spaces, etc.)

### Testing

**Test Organization:**
Tests are split into two categories using pytest markers:

1. **Unit/Integration tests** (default, no build required)
   - Run with: `make test` or `pytest -m "not package"`
   - Test parsing logic, postprocessing, extraction algorithms
   - Mock external dependencies (PDF files, etc.)
   - Fast feedback for development

2. **Package validation tests** (requires built package)
   - Run with: `make test-package` or `pytest -m package`
   - Validate `dist/` output structure and content
   - Check schema version consistency in built files
   - Ensure meta.json structure is correct
   - Run after `make output` or `make bundle`

**Key Principles:**
1. **Golden files catch everything**: One test covers entire pipeline
2. **Fixtures need both formats**: raw (for parsing tests) + normalized (for golden)
3. **Mock PDF extraction**: Avoids PDF dependency in CI
4. **Small unit tests**: Better for debugging than large integration tests
5. **Coverage != quality**: 100% coverage can still miss edge cases
6. **Separate package tests**: Don't require a build for unit tests

### Project Organization

1. **Pure functions first**: Separate I/O from logic
2. **Archive early**: Move old docs/research before they accumulate
3. **Version everything**: README, ROADMAP, schemas all reference versions
4. **Minimize external refs**: Don't brand with private project names
5. **Document decisions**: Future you will thank past you

---

## Build Behavior

### File Handling

**Overwrites on every build:**
- All files in `dist/<ruleset>/` are completely regenerated
- No incremental updates or merging
- Old data is replaced, not preserved

**Rationale:**
- **Reproducibility**: Same input → same output, always
- **Simplicity**: No complex merge logic or state tracking
- **Predictability**: What you see is what was built
- **No stale data**: Can't have orphaned entries from removed monsters

**Clean vs Dirty Builds:**
Currently all builds are "clean" (full regeneration). The output directory structure ensures:
- Each ruleset is isolated: `dist/srd_5_1/`, `dist/srd_5_2/`, etc.
- Files within a ruleset are atomic (written completely or not at all)
- No cleanup needed - overwrite handles it

**Multiple Rulesets:**
Different rulesets coexist peacefully:
```
dist/
├── srd_5_1/          # D&D 5.1 (current)
├── srd_5_2/          # D&D 5.2 (future)
└── pathfinder_2e/    # Pathfinder 2E (future)
```
Each has independent meta.json, data/, schemas - no conflicts.

**Future Formats:**
When adding output formats (YAML, SQLite, etc.):
- Will NOT replace JSON (JSON remains primary)
- Will ADD alongside JSON in parallel directories or with suffixes
- Design will preserve flexibility without locking into JSON-only structure

## Performance Characteristics

**Current (v0.4.2):**
- Extraction: ~5-10 seconds (134 pages, 296 monsters)
- Parsing: ~0.5 seconds (296 monsters)
- Postprocessing: ~0.1 seconds
- Indexing: ~0.05 seconds
- Total build: ~6-11 seconds

**Bottlenecks:**
- PDF extraction (80-90% of time)
- Column detection (many character-level operations)

**Optimizations considered:**
- ❌ Parallel extraction: PDF libraries not thread-safe
- ⚠️ Caching: Would break reproducibility guarantee
- ✅ Incremental: Only re-extract if PDF changes (via hash check)

---

## Future Considerations

### Multi-Content Extraction

When adding equipment/spells/classes:
- Reuse extraction patterns (font size, column detection)
- Separate parsers per content type
- Shared postprocessing utilities
- Unified index.json with all content types

### Schema Evolution

- Maintain backwards compatibility (additive changes only)
- Version schemas independently from builder
- Document breaking changes in migration guide

### Performance

- Consider streaming for very large PDFs (1000+ pages)
- Optimize column detection (current: character-level, future: line-level)
- Cache extraction results (keyed by PDF hash)

### Quality

- Add more edge case tests as we encounter them
- Improve error messages (better context in warnings)
- Consider fuzzy matching for typos in source PDF

---

## Version Management

srd-builder uses **three version numbers** that serve different purposes.

### 1. Package Version (`__version__`)

**Location:** `src/srd_builder/__init__.py`
**Current:** `0.5.2`
**Format:** Semantic versioning (`X.Y.Z`)

**Purpose:** Software release version - tracks the data/package we produce.

**When it changes:**
- PATCH (0.5.Z): Bug fixes, documentation updates, non-functional changes
- MINOR (0.Y.0): New features, new entity types, new optional fields
- MAJOR (X.0.0): Breaking changes (field renames, type changes, required fields removed)

**Used in:**
- `pyproject.toml` version field
- Package distribution (pip install)
- `meta.json` → `build.builder_version`
- `build_report.json` → `generated_by`
- `monsters.json` → `_meta.generated_by`
- All consumer-facing documentation

**Example changes:**
- `0.5.0 → 0.5.1`: Added action parsing + ability modifiers (feature)
- `0.4.2 → 0.5.0`: Added equipment extraction (new entity type)

---

### 2. Extractor Version (`EXTRACTOR_VERSION`)

**Location:** `src/srd_builder/constants.py`
**Current:** `0.3.0`
**Format:** Semantic versioning (`X.Y.Z`)

**Purpose:** Tracks the raw extraction format for **all** `*_raw.json` files (monsters_raw, equipment_raw, spells_raw, etc.).

**When it changes:**
- MINOR: New metadata fields in raw files (font info, positioning data)
- MAJOR: Breaking changes to raw extraction structure (column detection algorithm, table parsing format)

**Used in:**
- `monsters_raw.json` → `_meta.extractor_version`
- `equipment_raw.json` → `_meta.extractor_version`
- Future: `spells_raw.json`, `classes_raw.json`, etc.

**Why separate from package version?**
- Extraction format may stay stable across many package releases
- Documents the intermediate format between PDF and parsed output
- Useful for debugging extraction issues
- Changes independently of parsing/postprocessing improvements

**Example changes:**
- `0.3.0 → 0.4.0`: Add character-level positioning metadata to raw output
- `0.4.0 → 1.0.0`: Switch from line-based to block-based extraction format

---

### 3. Schema Version

**Location:** `schemas/monster.schema.json`, `constants.py`
**Current:** `1.2.0`
**Format:** Semantic versioning (`X.Y.Z`)

**Purpose:** JSON Schema validation rules version - tracks structure of final output data.

**When it changes:**
- PATCH (1.2.Z): Documentation improvements, example updates (rare)
- MINOR (1.Y.0): New optional properties, new enum values (backward compatible)
- MAJOR (X.0.0): Breaking schema changes (new required fields, type changes)

**Used in:**
- `schemas/monster.schema.json` → `$id` field
- `build.py` → `SCHEMA_VERSION` constant
- `meta.json` → `schema_version`
- `monsters.json` → `_meta.schema_version`
- Validation in `validate.py`

**Why separate from package version?**
- Schema defines the data contract for consumers
- Package version can increment (bug fixes) without changing data structure
- Consumers can check schema version to know if data is compatible
- Enables long-term schema stability across multiple package releases

**Example changes:**
- `1.1.0 → 1.2.0`: Added optional action parsing fields (backward compatible)
- `1.0.0 → 2.0.0`: Would indicate breaking data structure changes

---

### Version Relationships

```
EXTRACTOR_VERSION (0.3.0)  →  *_raw.json format  →  [parsing/postprocessing]
                                                              ↓
__version__ (0.5.1)  →  Package release  →  monsters.json, equipment.json
                                                              ↓
SCHEMA_VERSION (1.2.0)  →  Data contract  →  Consumer validation
```

**Key insight:** Extractor version tracks "how we extract from PDF" (affects all `*_raw.json` files), while package version tracks "the data/package we produce".

---

### Version Update Checklist

When releasing a new version:

1. **Determine change type:**
   - Bug fix only? → PATCH package version
   - New feature/entity type? → MINOR package version
   - Breaking change? → MAJOR package version (rare)

2. **Update package version:**
   - Edit `src/srd_builder/__init__.py` → `__version__`

3. **Update extractor version (if raw extraction changed):**
   - Only if `*_raw.json` format changes (rare)
   - New metadata fields? → MINOR extractor version
   - Breaking raw format changes? → MAJOR extractor version
   - Edit `constants.py` → `EXTRACTOR_VERSION`

4. **Update schema version (if data structure changed):**
   - New optional fields? → MINOR schema version
   - Breaking changes? → MAJOR schema version
   - Edit `constants.py` → `SCHEMA_VERSION`
   - Edit `schemas/monster.schema.json` → `$id`

5. **Update documentation:**
   - `README.md` → version references
   - `ROADMAP.md` → completed version section

6. **Regenerate test fixtures:**
   - Run: `python -m srd_builder.build --ruleset srd_5_1`
   - Copy `dist/srd_5_1/data/monsters.json` → `tests/fixtures/srd_5_1/normalized/monsters.json`
   - Version consistency tests will validate automatically

---

## Reference Data

### Monster Extraction Statistics (v0.4.2)

- **Total monsters**: 296
- **Source pages**: 261-394 (134 pages)
- **Field coverage**: 27 fields, 100% required fields
- **Optional field rates**:
  - Legendary actions: 10.1%
  - Reactions: 2.7%
  - Condition immunities: 29.7%
  - Damage immunities: 42.6%
  - Damage resistances: 20.3%
  - Damage vulnerabilities: 5.1%

### PDF Typography (SRD 5.1)

- **Monster headers**: GillSans-SemiBold @ 18.0pt
- **Variant headers**: GillSans-SemiBold @ 13.92pt
- **Section headers**: Calibri-Bold @ 12.0pt
- **Body text**: Calibri @ 9.84pt
- **Column midpoint**: 306.0pt (exact, all pages)
- **Left column**: ~88-97pt
- **Right column**: ~349-374pt

---

## Contributing

When adding new features or content types, maintain these principles:

1. **Keep functions pure**: No I/O in parse/postprocess modules
2. **Add tests first**: Write failing test, then implement feature
3. **Document decisions**: Update this doc with "why" behind changes
4. **Preserve provenance**: Always track back to source PDF
5. **Validate early**: Use schemas to catch issues before build completes

See `docs/ROADMAP.md` for planned features and milestones.
