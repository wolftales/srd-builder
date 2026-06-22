# SRD-Builder Architecture

<!-- AUTO-SYNC:arch:version START -->
**Version:** v0.37.1
<!-- AUTO-SYNC:arch:version END -->
**Purpose:** Technical reference documenting design decisions, tooling choices, and lessons learned

> The authoritative item counts and schema versions live in `dist/srd_5_1/meta.json` (the `datasets` and `schemas` blocks). The tables below are a human-readable snapshot — if they ever disagree with the live `meta.json`, `meta.json` wins.

---

## Datasets Overview

<!-- AUTO-SYNC:arch:total-line START -->
SRD-Builder extracts structured JSON datasets from the SRD 5.1 PDF. The v0.37.1 build ships **16 datasets** containing **1,687 items**:
<!-- AUTO-SYNC:arch:total-line END -->

<!-- AUTO-SYNC:arch:overview-table START -->
| File | Count | Schema | Description |
|------|------:|--------|-------------|
| `ability_scores.json` | 6 | v1.0.0 | Atomic reference: STR/DEX/CON/INT/WIS/CHA |
| `classes.json` | 12 | v2.1.0 | Character classes with progression |
| `conditions.json` | 15 | v3.0.0 | Status conditions (poisoned, stunned, etc.) |
| `damage_types.json` | 13 | v1.0.0 | Atomic reference: damage type vocabulary |
| `diseases.json` | 3 | v3.0.0 | Cackle Fever, Sewer Plague, Sight Rot |
| `equipment.json` | 259 | v2.2.0 | Weapons, armor, adventuring gear |
| `features.json` | 245 | v4.0.0 | Class features and lineage traits |
| `lineages.json` | 13 | v2.0.0 | Races/lineages with traits |
| `magic_items.json` | 240 | v2.0.0 | Magic items with descriptions |
| `monsters.json` | 317 | v2.0.0 | Monsters, creatures, and NPCs |
| `poisons.json` | 14 | v2.0.0 | Poison gear entries + descriptions |
| `rules.json` | 167 | v3.0.0 | Core mechanics from 7 chapters |
| `skills.json` | 18 | v1.0.0 | Atomic reference: skill vocabulary |
| `spells.json` | 319 | v2.0.0 | Spell list with effects, components, casting |
| `tables.json` | 35 | v3.0.0 | Reference tables (equipment, expenses, services, madness) |
| `weapon_properties.json` | 11 | v1.0.0 | Atomic reference: weapon property vocabulary |
<!-- AUTO-SYNC:arch:overview-table END -->

**Bundle collateral** (also under `dist/srd_5_1/`):

| File | Purpose |
|------|---------|
| `meta.json` | Version, license, page index, terminology aliases, `datasets` and `schemas` manifest |
| `index.json` | Fast lookup maps (by name, CR, type, etc.) |
| `build_report.json` | Per-stage parse/postprocess counts and warnings |
| `README.md` | Generated dynamically from `meta.json` (see [build.py](src/srd_builder/build.py)) |
| `schemas/` | All 16 JSON Schema files |
| `docs/` | DATA_DICTIONARY.md, SCHEMAS.md (shipped to consumers) |

**Dataset shape note:** All datasets follow `{"_meta": ..., "items": [...]}`. Three datasets (`conditions`, `diseases`, `features`) previously used the dataset name as the array key; they were normalized to `items` in v0.30.0. Consumers reading any bundle ≥ v0.30.0 can use a single `doc["items"]` access pattern.

---

## Overview

srd-builder extracts structured data from PDF documents (specifically SRD 5.1) and produces clean, validated JSON datasets. The project prioritizes **reproducibility**, **provenance**, and **clean separation of concerns**.

## Module Boundaries

**Critical separation of concerns:**

- **parse_*.py**: Pure parsing/mapping only (no I/O/logging)
- **postprocess/**: Pure normalization/polish (legendary, CR, text, defenses, ids)
- **indexer.py**: Pure index building
- **build.py**: The only I/O orchestrator
- **validate.py**: Schema validation; no mutations

**Why these boundaries matter:**
- Testability: Pure functions can be tested without file system
- Composability: Stages can be chained or reordered
- Clarity: Each module has ONE job
- Maintainability: Change normalization without touching parsing

### Design Philosophy

1. **Pure Functions**: Parsing and processing modules have no I/O or side effects
2. **Single Responsibility**: Each module does one thing well
3. **Determinism**: Same input → same output (no timestamps in datasets)
4. **Provenance**: Track everything back to source PDF (page numbers, hash)
5. **Clean Boundaries**: Extract → Parse → (Postprocess) → Index → Validate
6. **Maximum SRD Extraction**: Extract as much structured information *from the SRD* as possible
   - Goal: Comprehensive extraction of what exists in the source document, not data augmentation
   - Beyond minimal requirements: enrich datasets with prose descriptions, mechanics details found in SRD
   - Example: Poison table data + poison descriptions (both from SRD) merged into comprehensive records
   - Example: Equipment stats + equipment descriptions (both from SRD) for richer item details
   - Boundary: No external data sources, no homebrew content, no data invented beyond what's in the PDF
   - Future: Consider merging prose datasets (equipment_descriptions, poison_descriptions) into parent datasets at engine/consumer layer
   - Rationale: Downstream applications benefit from rich, complete data extracted from the official SRD

**Note on Pipeline Evolution:**

Two architectural patterns exist in the codebase, reflecting different design tradeoffs:

- **Modular Pattern (monsters, spells, equipment):** Extract → Parse → **Postprocess** → Output
  - Parse: Extract/structure data from PDF metadata (e.g., `parse_monsters.py` - 987 lines)
  - Postprocess: Normalize/clean/generate IDs using shared utilities (e.g., `postprocess/monsters.py` - 375 lines)
  - **Benefits:** Clear separation of concerns, reusable utilities, better testability
  - Two modules per dataset

- **Monolithic Pattern (magic_items, tables):** Extract → Parse (All-in-One) → Output
  - Parse does everything: structure + normalize + IDs (e.g., `parse_magic_items.py` - 325 lines)
  - No postprocess module
  - **Trade-offs:** Simpler file structure, but mixes parsing and normalization concerns
  - Code duplication (reimplements `normalize_id()` instead of using shared utility)
  - Single module per dataset

**Target Architecture (Modular Pattern):**

All datasets should follow this pattern for consistency and maintainability:

```
Extract (PDF → Raw JSON) → Parse (Structure) → Postprocess (Normalize) → Index → Validate
```

**Stage Responsibilities:**

1. **Extract** (`extract_*.py`): PDF text extraction only
   - Font/position metadata capture
   - Block identification (headers, paragraphs)
   - Output: `*_raw.json` with verbatim PDF content
   - **No parsing, no normalization**

2. **Parse** (`parse_*.py`): Structure extraction only
   - Field mapping from raw blocks
   - Type identification and conversion
   - Description segmentation
   - Output: Structured dicts with original values
   - **No ID generation, no text cleanup**

3. **Postprocess** (`postprocess/*.py`): Normalization only
   - Generate stable IDs using shared `normalize_id()`
   - Polish text using shared `polish_text()`
   - Deduplicate arrays
   - Apply domain-specific transformations
   - Output: Final clean records
   - **Uses shared utilities, no duplication**

**Benefits:**
- ✅ Separation of concerns (parsing ≠ normalization)
- ✅ Code reuse (`normalize_id()`, `polish_text()` shared across datasets)
- ✅ Testability (each stage independently testable)
- ✅ Maintainability (change normalization without touching parsing)
- ✅ Consistency (all datasets follow same pattern)

**Migration Path:**
- Monolithic datasets (magic_items, tables) should be refactored to extract normalization logic into `postprocess/` modules
- Future datasets must use modular pattern from the start

---

## Config-Driven Engine Pattern

A recurring architectural pattern across the build pipeline: **a per-dataset
configuration dictionary + a dispatcher that reads the configuration and
delegates to pluggable handlers**. The same idiom solves the same problem at
multiple stages, but each stage gets its own engine because the operations
are stage-specific.

### Stages and their engines

| Stage | Engine | Config registry | Pluggable handlers | Status |
|-------|--------|-----------------|---------------------|--------|
| `extract/` | [engine.py](../src/srd_builder/extract/engine.py) | [extraction_metadata.TABLES](../src/srd_builder/extract/extraction_metadata.py) | [patterns/](../src/srd_builder/extract/patterns/) package (one module per pattern type: `standard_grid`, `split_column`, `text_region`, `multipage_text_region`, `prose_section`, `calculated`, `reference`, `font_fingerprint_walk`, `font_stateful_walk`) | ✅ In production |
| `parse/` | _none_ | _none_ | _none_ — per-dataset modules | 📋 Phase 3 (future) |
| `postprocess/` | [engine.py](../src/srd_builder/postprocess/engine.py) | [configs.DATASET_CONFIGS](../src/srd_builder/postprocess/configs.py) | `RecordConfig.custom_transform` (escape hatch) | 🔄 Phase 1 (v0.29.0) |
| `assemble/` | _none_ | _none_ | _none_ — orchestration only | n/a |

### The pattern, in one paragraph

For a given pipeline stage, declare what each dataset needs as a config
entry in a single registry (e.g. `extraction_metadata.TABLES["ability_scores_and_modifiers"]`
or `DATASET_CONFIGS["condition"]`). The engine reads the registry, applies
the common processing steps to every dataset uniformly, and falls back to a
pluggable handler (pattern type, custom transform) only where the dataset
genuinely needs custom logic. Most datasets need only a config entry; a small
minority need a config entry plus a small handler.

### Why this pattern, not per-dataset modules

- **Less duplicated code.** The 12 boilerplate-heavy postprocess modules
  do the same 5 operations in ~30-50 lines each. One engine + 12 5-line
  configs is materially less code than 12 near-identical modules.
- **One place to fix shared logic.** A bug in `polish_text()` or
  `normalize_id()` was already one fix; a bug in the *pattern of applying
  those utilities* (e.g. "polish nested struct fields") becomes one fix
  too, instead of 12.
- **Declarative additions for new SRDs.** Adding SRD 5.2.1 or Pathfinder
  for the boilerplate-heavy datasets becomes "add a config entry" instead
  of "write another module". Complex datasets (monsters, rules, spells,
  equipment) still need per-ruleset modules because they have real
  domain differences across rulesets.
- **Proven elsewhere in this codebase.** The `extract/` stage has used this
  exact pattern since v0.9.5 for table extraction. It works.

### When NOT to use the engine

The engine is for boilerplate consolidation. Use a custom per-dataset
module when:

- The processing has irreducible domain logic that doesn't reduce to
  declarative config (e.g. monster legendary-action parsing, statblock
  cleanup, ability-modifier derivation).
- The function signature differs (extra kwargs like
  `spell_classes_map=`, `equipment_packs=`, etc.).
- The dataset is the *only* one of its shape (one-off transforms don't
  need a registry).

Currently 4 of the 16 postprocess datasets stay custom for these reasons:
`monsters` (370 lines), `rules` (123 lines), `spells` (62 lines, takes
`spell_classes_map=`), `equipment` (53 lines, takes pack/description
kwargs).

### Phases

- **Phase 1 (v0.29.0)** — migrate the 12 boilerplate-heavy postprocess
  modules to `DATASET_CONFIGS`. Keep 4 custom modules. Un-skip the 19
  engine tests. See [docs/BACKLOG.md § v0.29.0](BACKLOG.md) for the
  task list.
- **Phase 2 (deferred)** — consider migrating `spells`/`equipment` via
  richer `custom_transform`. Small wins; not urgent.
- **Phase 3 (deferred until Phase 1 proves itself)** — apply the same
  idiom to `parse/`. Bigger investment; defer until at least one
  release cycle of Phase 1 in production.
- **Endgame (much later)** — a single per-dataset registry tying
  `dataset → {schema, extract_config, parse_strategy, postprocess_config}`.
  Premature until Phase 1 + Phase 3 ship.

## Pipeline Architecture

**Target Modular Pattern (all datasets):**

```
┌─────────────────────────────────────────────────────────────┐
│ 1. EXTRACT (extract_*.py) - PDF → Raw JSON                 │
│ • Font/position metadata from PDF                          │
│ • Block detection (headers, paragraphs)                    │
│ • NO parsing, NO normalization                             │
│ • Output: *_raw.json                                       │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. PARSE (parse_*.py) - Structure Extraction               │
│ • Field mapping from raw blocks                            │
│ • Type identification                                      │
│ • Description segmentation                                 │
│ • NO ID generation, NO text cleanup                        │
│ • Output: Structured dicts (not normalized)                │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. POSTPROCESS (postprocess/*.py) - Normalization           │
│ • Generate IDs: normalize_id() - SHARED UTILITY            │
│ • Polish text: polish_text() - SHARED UTILITY              │
│ • Deduplicate arrays                                       │
│ • Domain-specific transformations                          │
│ • Output: Final clean records                              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. INDEX (indexer.py) - Build Lookups                      │
│ • by_name, by_type, by_cr maps                            │
│ • Expand aliases                                           │
│ • Track conflicts                                          │
└─────────────────────────────────────────────────────────────┘
```

**Current Implementation Example (monsters, spells, equipment):**

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
│ POSTPROCESS (postprocess/*.py)                             │
│ • Domain-specific modules (monsters, equipment, spells)    │
│ • Normalize legendary actions, challenge ratings           │
│ • Deduplicate defense arrays + polish nested text          │
│ • Generate stable IDs shared across parse + postprocess    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ INDEX (indexer.py)                                         │
│ • Build by_name, by_cr, by_type lookups                   │
│ • Expand entity aliases into by_name indexes               │
│ • Add terminology aliases (races→lineages)                 │
│ • Track conflicts                                          │
└─────────────────────────────────────────────────────────────┘
```

**Preferred Pattern (magic_items, tables):**

```
┌─────────────────────────────────────────────────────────────┐
│ INPUT: rulesets/srd_5_1/raw/SRD_CC_v5.1.pdf                │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ EXTRACT (extract_magic_items.py)                           │
│ • PDF text extraction with font/position metadata          │
│ • Detect item headers (18pt GillSans-SemiBold)             │
│ • Extract metadata, description blocks                     │
│ • Output: magic_items_raw.json (blocks + metadata)         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ PARSE (parse_magic_items.py) - ALL-IN-ONE                 │
│ • Parse rarity, type, attunement from metadata             │
│ • Segment description paragraphs                           │
│ • Generate stable IDs (magic_item:bag_of_holding)          │
│ • Normalize text (remove PDF artifacts)                    │
│ • Filter invalid entries                                   │
│ • Pure function: dict → list[dict] (FINAL OUTPUT)          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ INDEX (indexer.py)                                         │
│ • Build by_name, by_type, by_rarity lookups               │
│ • Track conflicts                                          │
└─────────────────────────────────────────────────────────────┘
```

**Key Differences:**
- Legacy: Parse → Postprocess (two modules, ~1300 lines total)
- Preferred: Parse only (one module, ~300 lines)
- Preferred pattern produces final output directly from parse phase
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
│ BUILD (build.py + metadata.py)                             │
│ • Orchestrates pipeline (only I/O module)                  │
│ • metadata.py builds deterministic _meta + meta.json       │
│ • Writes datasets to dist/ + build_report.json             │
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
│ • meta.json (license, provenance, datasets, schemas)       │
│ • build_report.json (build metadata)                       │
│ • monsters.json (317 normalized monsters)                  │
│ • index.json (lookup tables)                               │
│ • README.md (generated from meta.json)                     │
│ • schemas/ (16 JSON Schema files)                          │
│ • docs/ (DATA_DICTIONARY.md, SCHEMAS.md)                   │
└─────────────────────────────────────────────────────────────┘
```

---

## Prose Extraction Framework

Most datasets pull from layout-rich PDF regions (monsters, equipment, spells), but several pull primarily from running prose: conditions, diseases, poisons, rules, features, magic items. The shared helpers for that pattern live in [src/srd_builder/extract/extract_prose.py](src/srd_builder/extract/extract_prose.py).

**Core helpers** (importable from `srd_builder.extract.extract_prose`):

| Helper | Purpose |
|--------|---------|
| `ProseExtractor` (class) | End-to-end: configure with `section_name`, `known_headers`, `start_page`, `end_page`; returns `(sections, warnings)` for downstream parsing |
| `extract_bullet_points(text)` | Detects `•`, numbered (`1. 2.`), or dashed (`-`) lists |
| `extract_table_by_pattern(text, pattern, columns)` | Generic regex-based table extraction |
| `split_by_known_headers(text, headers)` | Section splitter when header names are known |
| `discover_headers_by_font(page, font_name, font_size)` | Font-based header discovery when names are not known |

Text cleanup (smart-quote normalization, whitespace, encoding fixes) lives in [src/srd_builder/postprocess/text.py](src/srd_builder/postprocess/text.py) as `clean_text()` — call it from your `parse_*.py` after structure extraction, not during extraction.

**Reference implementation:** [src/srd_builder/extract/extract_conditions.py](src/srd_builder/extract/extract_conditions.py) is the canonical example — short, complete, and follows the modular Extract → Parse → Postprocess split. Use it as the template when adding a new prose dataset.

**Composition:** [src/srd_builder/assemble/assemble_prose.py](src/srd_builder/assemble/assemble_prose.py) is the build-stage entry point that wires these helpers into the pipeline.

---

## PDF Primitives Library (`utils/`)

Every PDF mechanic with a clean `(inputs, config) → output` shape lives
in `src/srd_builder/utils/`. Modules under `extract/datasets/` are
**orchestration**: they pick which primitives to invoke, in what order,
with which dataset-specific predicates and constants. They do not
re-implement geometry, span iteration, table cleanup, page
concatenation, or hashing.

This is the codified discipline behind the "lift the mechanic, not the
caller" round of refactors. The engine (`extract/patterns/`) is one
such primitive — a config-driven orchestrator — not a tier above the
others.

### Current primitive inventory

| Module | Helper | Shape |
|--------|--------|-------|
| `utils/pdf_probe.py` | `open_pdf`, `page_text`, `pages_text`, `page_dict` | basic page-text access |
| `utils/pdf_probe.py` | `normalize_whitespace` | SRD tab/CR/nbsp → single space |
| `utils/pdf_probe.py` | `pdf_sha256` | file-hash for provenance |
| `utils/pdf_probe.py` | `concat_pages_with_offsets` | multi-page text + reverse-index |
| `utils/pdf_probe.py` | `offset_to_page` | reverse-map char offset → page |
| `utils/pdf_layout.py` | `iter_page_spans` | flat span iteration over a page dict |
| `utils/pdf_layout.py` | `span_matches_predicate` | declarative font/size/flag filter |
| `utils/pdf_layout.py` | `find_in_lookahead` | bounded forward scan with stop condition |
| `utils/pdf_layout.py` | `cluster_values_by_gap` | 1-D greedy clustering by gap threshold |
| `utils/pdf_layout.py` | `extract_columnar_spans`, `merge_spans_into_lines` | column-aware extraction + line merging |
| `utils/pdf_layout.py` | `merge_bboxes`, `color_to_rgb`, `determine_column`, `is_bold`, `is_italic` | small geometry/flag helpers |
| `utils/pdf_tables.py` | `clean_and_split_header` | normalize `table.extract()` rows + detect header |
| `utils/prose.py` | `clean_text`, `normalize_apostrophes` | shared text-cleanup primitives |
| `utils/page_index.py` | `PAGE_INDEX`, `pdf_index_for`, etc. | 1-indexed SRD page label → PDF index map |
| `utils/context_tracker.py` | `ContextTracker` | running section/subsection state across pages |
| `extract/patterns/` | engine + pattern handlers | config-driven extraction orchestrator |

### When to lift into `utils/`

A function belongs in `utils/` when it has all of:

1. A clean shape: well-defined `(inputs, config) → output`, no hidden global state.
2. PDF-shape generic: depends on PyMuPDF objects, span dicts, or
   primitive geometry — not on what a "monster" or "spell" is.
3. Dataset-specific work (predicates, keyword sets, regex) is supplied
   by the caller, not baked in.

The 2-caller rule applies to **inventing new abstractions**, not to
**naming what is already there**. If the mechanic is already shaped
like a primitive but currently has one caller, lift it — the next
extractor benefits, and even the single caller reads cleaner with the
named operation. This was the principle behind the
`find_in_lookahead`, `cluster_values_by_gap`,
`concat_pages_with_offsets`, and `clean_and_split_header` lifts: each
had exactly one caller at lift time.

### When to leave it in the dataset

Keep code in `extract/datasets/` when it embodies dataset-specific
knowledge that doesn't factor cleanly: monster-name fingerprints,
heading-to-id maps, column-name keyword sets, subsection terminator
lists, irregular table layouts. A predicate function passed to
`span_matches_predicate` lives in the dataset; the predicate runner
lives in `utils/`. Negated multi-OR conditions (e.g. classes' inline
`sz != 8.9 or "Bold" in font or "Cambria" in font` checks) stay inline
because the positive-AND predicate shape would obscure them rather
than help.

---

## Schema Stability Tiers

Adopted in v0.29.3 (Phase 5.3) to give consumers and future contributors a single place to see *how D&D-5e-specific* each schema is. This matters because srd-builder will eventually scaffold other tabletop SRDs (e.g. Pathfinder 2e, Cypher System) and the cost of adding a new game system is dominated by how many constraints have to be widened in the **Red-tier** schemas below.

Tier definitions:

| Tier | Meaning |
|------|---------|
| **Green** | System-agnostic. Fields and value spaces describe generic tabletop concepts (a damage type, a condition, a table row). Re-usable across systems with no schema edits. |
| **Yellow** | Light D&D-isms. Mostly generic structurally, but a few enums or numeric ranges encode 5e assumptions. Adapting to another system requires widening enums but not restructuring records. |
| **Red** | Heavy D&D coupling. Core fields encode 5e mechanics (Vancian spell levels 0-9, six-ability blocks, specific class structures). Supporting another system requires either per-system schema variants or non-trivial restructuring. |

Current classification (15 schemas as of v0.29.3):

| Tier | Schemas | Notes |
|------|---------|-------|
| **Green** (5) | `condition`, `damage_type`, `weapon_property`, `rule`, `table` | Pure structural shapes. `rule` carries free-form prose; `table` is a generic grid. |
| **Yellow** (5) | `equipment`, `magic_item`, `disease`, `poison`, `ability_score` | Equipment categories and magic-item rarity ladders are 5e conventions; ability_score IDs are the canonical six but the *shape* is generic. |
| **Red** (5) | `spell`, `monster`, `class`, `lineage`, `skill` + `features` | Spell levels (0-9), 8 schools, 8 caster classes; AC/HP/CR + six-ability stat block; `hit_die ∈ {d6,d8,d10,d12}` + exactly-2 saves; `size ∈ {Small,Medium}` + six-ability modifiers; skills are tied to the 5e ability list. |

**Implication for multi-system support:** when adding a non-5e ruleset, Green schemas can be shared as-is, Yellow schemas need enum widening (typically additive, non-breaking for existing consumers), and Red schemas should be branched per game-system rather than over-generalized. The `game_system` field on each `_meta` block (v0.29.3 Phase 5.1) and the `id_prefix` seam on `clean_record` (Phase 5.2) exist precisely to make that branching mechanical rather than invasive.

This table is informational; nothing in the build pipeline enforces a tier. It is reviewed when a schema changes — see [docs/BACKLOG.md](BACKLOG.md) for in-flight schema work.

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

**Test Strategy (v0.23.0: 292 passing, 19 skipped):**
```
tests/
├── test_extract_*.py         # PDF extraction
├── test_parse_*.py           # Field parsing (minimal, covered by golden)
├── test_postprocess_*.py     # Normalization
├── test_indexer*.py          # Index building
├── test_build_pipeline.py    # End-to-end
├── test_validate_*.py        # Schema validation
├── test_golden_*.py          # Golden file comparison (16 — one per dataset)
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

**Decision:** `parse_monsters.py` and `postprocess/` are pure functions (no I/O).

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

### 7. Alias System (v0.8.1)

**Decision:** Three-level alias pattern for flexible searches and backward compatibility.

**Architecture:**

1. **Index-level (terminology)**: Category mappings in `index.json`
   - Maps historical/alternative names to canonical: `"races"` → `"lineages"`
   - Both singular and plural: `"race"`/`"races"` → `"lineage"`/`"lineages"`
   - Used by consumers to resolve category names before lookup

2. **Entity-level (search terms)**: Optional `aliases` array on entities
   - Compound items: `flask_or_tankard.aliases = ["flask", "tankard"]`
   - Historical terms, common variations, partial names
   - Stored in entity data, automatically indexed

3. **Indexer-level (automatic expansion)**: Build pipeline handles indexing
   - `indexer.py` reads entity `aliases` field
   - Adds each alias as lookup key in `by_name` indexes
   - Result: `by_name["tankard"]` → `"item:flask_or_tankard"`

**Rationale:**
- **Backward compatibility**: Legacy code using "race" continues to work
- **Discoverability**: Aliases programmatically accessible in `index.json`
- **Natural search**: Find items using partial/alternative names
- **Clean separation**: Terminology (index) vs entity data (aliases field)
- **No breaking changes**: Additive only, doesn't affect existing lookups

**Implementation:**
- Added optional `aliases: string[]` to all entity schemas (v1.3.0)
- Modified `_build_by_name_map()` to expand entity aliases
- Added top-level `aliases` object to `index.json`
- Documented in `meta.json` for reference

**What we learned:**
- Initial attempt (aliases only in `meta.json`) didn't help searches
- Consumers use `index.json` for lookups, not `meta.json`
- Three levels needed: terminology, entity data, automatic indexing
- One-way resolution is sufficient (no bidirectional needed)

---

## Data Consistency Guidelines

**Output Determinism:**
- **Alphabetical ordering:** Dictionary keys in metadata should be alphabetically sorted
- **No timestamps:** Timestamps only in build_report.json, never in datasets
- **Sorted arrays:** Sort by name/id, not insertion order
- **Stable IDs:** Use slug from name, not UUID

**Metadata Accuracy:**
- meta.json must reflect actual build output, not design intent
- Use file existence checks to determine what was built
- PAGE_INDEX is authoritative for page ranges

**Data Shapes:**
- Target shapes defined in schemas/exemplars/*.exemplar.json (generated by scripts/generate_exemplars.py)
- Fixtures split: tests/fixtures/.../raw vs .../normalized
- Entities and nested entries must include `simple_name` where applicable

**Testing Philosophy:**
- **Test failures over skips:** Tests should FAIL when expected data is missing
- This catches build issues immediately
- Exception: CI tests where PDF is unavailable
- **No duplication:** Use references/aliases instead of duplicating data
- **Field ordering:** Maintain consistent field order in _meta blocks

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

### Testing Guidelines

**Golden Test Pattern (Fixture-Based):**

- **Location:** `tests/test_golden_*.py` (one per dataset)
- **Purpose:** End-to-end validation that parsing produces consistent, deterministic output
- **Fixture structure:**
  - `tests/fixtures/srd_5_1/raw/{dataset}.json` - Raw extraction data (input to parser)
  - `tests/fixtures/srd_5_1/normalized/{dataset}.json` - Expected final output (golden reference)
- **Pattern:** Load raw fixture → parse (+ postprocess if modular) → compare to normalized fixture
- **Benefits:**
  - No dependency on `dist/` directory (works in CI without PDF)
  - Uses committed fixtures (always available)
  - Tests entire pipeline in one assertion
  - Catches any regression in parsing or postprocessing logic

**Golden Test Examples:**

*All-in-one parse (monolithic pattern):*
```python
def test_magic_items_dataset_matches_normalized_fixture() -> None:
    raw_path = Path("tests/fixtures/srd_5_1/raw/magic_items.json")
    expected_path = Path("tests/fixtures/srd_5_1/normalized/magic_items.json")

    magic_items_raw = json.loads(raw_path.read_text(encoding="utf-8"))
    parsed = parse_magic_items({"items": magic_items_raw})

    document = {"_meta": meta_block(...), "items": parsed}

    rendered = json.dumps(document, indent=2, ensure_ascii=False) + "\n"
    expected = expected_path.read_text(encoding="utf-8")
    assert rendered == expected
```

*Parse + postprocess (modular pattern):*
```python
def test_monster_dataset_matches_normalized_fixture() -> None:
    raw_path = Path("tests/fixtures/srd_5_1/raw/monsters.json")
    expected_path = Path("tests/fixtures/srd_5_1/normalized/monsters.json")

    monsters_raw = json.loads(raw_path.read_text(encoding="utf-8"))
    parsed = parse_monster_records(monsters_raw)
    processed = [clean_monster_record(monster) for monster in parsed]

    document = {"_meta": meta_block(...), "items": processed}

    rendered = json.dumps(document, indent=2, ensure_ascii=False) + "\n"
    expected = expected_path.read_text(encoding="utf-8")
    assert rendered == expected
```

**Fixture Maintenance:**
- Keep fixtures small (5-10 representative items, not entire datasets)
- Update fixtures when parser output format changes (expected breakage)
- Fixtures are NOT for backwards compatibility - they validate current behavior
- Regenerate fixtures from actual build output when making intentional changes

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

**Golden Fixture Tests:**

Golden tests validate the complete pipeline using committed fixtures:

- **Modular pattern** (monsters/spells/equipment):
  ```python
  # Load raw → parse → postprocess → compare to normalized fixture
  raw = json.loads(Path("tests/fixtures/srd_5_1/raw/monsters.json").read_text())
  parsed = parse_monster_records(raw)
  processed = [clean_monster_record(m) for m in parsed]
  assert rendered_output == expected_fixture
  ```

- **Monolithic pattern** (magic_items/tables):
  ```python
  # Load raw → parse (all-in-one) → compare to normalized fixture
  raw = json.loads(Path("tests/fixtures/srd_5_1/raw/magic_items.json").read_text())
  parsed = parse_magic_items({"items": raw})  # Returns final output
  assert rendered_output == expected_fixture
  ```

**Key Principles:**
1. **Golden files catch everything**: One test covers entire pipeline
2. **Fixtures need both formats**: raw (for parsing tests) + normalized (for golden)
3. **Mock PDF extraction**: Avoids PDF dependency in CI
4. **Small unit tests**: Better for debugging than large integration tests
5. **Coverage != quality**: 100% coverage can still miss edge cases
6. **Separate package tests**: Don't require a build for unit tests
7. **Committed fixtures**: Always available, work in CI without PDF

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

**Current (v0.23.0, 16 datasets):**
- Extraction: ~5-10 seconds per dataset (the slow stages)
- Parsing: sub-second per dataset
- Postprocessing: sub-second per dataset
- Indexing: sub-second
- Total `make bundle`: ~60-90 seconds end-to-end

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

### 1. Package Version

**Source of truth:** `pyproject.toml` `[project] version` field
**Current:** `0.23.0`
**Format:** Semantic versioning (`X.Y.Z`)

**Purpose:** Software release version — tracks the package we produce.

**How code reads it:** `src/srd_builder/__init__.py` calls `importlib.metadata.version("srd-builder")` so there is **no version literal in code** — `pyproject.toml` is the single source of truth. The helper script [scripts/bump_version.py](scripts/bump_version.py) updates `pyproject.toml` and regenerates committed fixtures in one step.

**When it changes:**
- PATCH (0.X.Z): Bug fixes, documentation updates, non-functional changes
- MINOR (0.Y.0): New features, new entity types, new optional fields
- MAJOR (X.0.0): Breaking changes (field renames, type changes, required fields removed)

**Used in:**
- `pyproject.toml` `[project] version` (canonical)
- Package distribution (pip install)
- `meta.json` → `build.builder_version`
- `build_report.json` → `generated_by`
- Every dataset's `_meta.generated_by`
- The dynamic bundle README

**Example changes:**
- `0.22.1 → 0.22.2`: `make init` auto-clears macOS UF_HIDDEN flag on `.venv` (bug fix)
- `0.22.2 → 0.23.0`: Dynamic bundle README, inventory manifest, full 16-schema coverage (feature)

---

### 2. Extractor Version (`EXTRACTOR_VERSION`)

**Location:** `src/srd_builder/constants.py`
**Current:** `0.4.0`
**Format:** Semantic versioning (`X.Y.Z`)

**Purpose:** Tracks the raw extraction format for `*_raw.json` files.

**When it changes:**
- MINOR: New metadata fields in raw files (font info, positioning data)
- MAJOR: Breaking changes to raw extraction structure (column detection algorithm, table parsing format)

**Used in:**
- `*_raw.json` → `_meta.extractor_version`

**Why separate from package version?**
- Extraction format stays stable across many package releases
- Documents the intermediate format between PDF and parsed output
- Useful for debugging extraction issues
- Changes independently of parsing/postprocessing improvements

**Example changes:**
- `0.3.0 → 0.4.0`: Added font metadata blocks (header_blocks/description_blocks) for spells

---

### 3. Schema Version

**Location:** Each `schemas/*.schema.json` carries its own `$id` with embedded version.
**Current range:** v1.0.0 (atomic reference schemas: ability_score, damage_type, skill, weapon_property) through v2.0.0 (most others).
**Format:** Semantic versioning (`X.Y.Z`)

**Purpose:** JSON Schema validation rules version — tracks structure of final output data.

**When it changes:**
- PATCH (X.Y.Z): Documentation improvements, example updates (rare)
- MINOR (X.Y.0): New optional properties, new enum values (backward compatible)
- MAJOR (X.0.0): Breaking schema changes (new required fields, type changes)

**Used in:**
- Each `schemas/*.schema.json` → `$id` field
- Each dataset's `_meta.schema_version`
- `meta.json` → `schemas` block lists every shipped schema and its version
- Validation in `validate.py`

**Why separate from package version?**
- Schema defines the data contract for consumers
- Package version can increment (bug fixes) without changing data structure
- Consumers can check schema version to know if data is compatible
- Enables long-term schema stability across multiple package releases

**Example changes:**
- `1.1.0 → 1.2.0`: Added optional action parsing fields (backward compatible)
- `1.x.0 → 2.0.0`: Removed redundant summary fields, added cross-reference IDs

---

### Version Relationships

```
EXTRACTOR_VERSION (0.4.0)  →  *_raw.json format  →  [parsing/postprocessing]
                                                              ↓
Package version (0.23.0, from pyproject.toml)  →  Bundle release  →  16 datasets
                                                              ↓
Schema version (per-schema, v1.0.0–v2.0.0)  →  Data contract  →  Consumer validation
```

**Key insight:** Extractor version tracks "how we extract from PDF" (affects all `*_raw.json` files); package version tracks "the bundle we produce"; schema version is per-schema and tracks "the contract consumers validate against".

---

### Version Update Checklist

When releasing a new version:

1. **Determine change type:**
   - Bug fix only? → PATCH package version
   - New feature/entity type? → MINOR package version
   - Breaking change? → MAJOR package version (rare)

2. **Bump the package version:**
   - Run `python scripts/bump_version.py X.Y.Z` — this edits `pyproject.toml` AND regenerates every committed normalized fixture in one shot.

3. **Update extractor version (if raw extraction changed):**
   - Only if `*_raw.json` format changes (rare)
   - Edit `src/srd_builder/constants.py` → `EXTRACTOR_VERSION`

4. **Update schema version (if data structure changed):**
   - Edit `schemas/<dataset>.schema.json` → `$id`
   - Re-run `make bundle` so dataset `_meta.schema_version` and `meta.json.schemas` get the new value

5. **Update documentation:**
   - `docs/ROADMAP.md` → completed version section
   - This file's dataset table if counts changed materially

6. **Rebuild + verify:**
   - `make bundle && ./scripts/smoke.sh srd_5_1 dist bundle && pytest -q`
   - Confirm `dist/srd_5_1/meta.json` `datasets` and `schemas` blocks match expectations

---

## Reference Data

<!-- AUTO-SYNC:arch:stats-header START -->
### Dataset Statistics (v0.37.1)
<!-- AUTO-SYNC:arch:stats-header END -->

Live counts come from `dist/srd_5_1/meta.json.datasets`. Snapshot for this revision:

<!-- AUTO-SYNC:arch:stats-table START -->
| Dataset | Count | Notes |
|---------|------:|-------|
| spells | 319 | Cantrip through 9th, all 8 schools |
| monsters | 317 | Pages 261–394; 27 fields, 100% required coverage |
| equipment | 259 | Weapons, armor, adventuring gear (11 weapon properties) |
| features | 245 | Class features and lineage traits |
| magic_items | 240 | Magic items with descriptions |
| rules | 167 | 7 chapters of core mechanics |
| tables | 35 | Equipment, expenses, services, madness, etc. |
| skills | 18 | Atomic reference |
| conditions | 15 | Status conditions |
| poisons | 14 | Poison gear + descriptions |
| damage_types | 13 | Atomic reference |
| lineages | 13 | 9 base + 4 subraces |
| classes | 12 | Full progression tables (levels 1–20) |
| weapon_properties | 11 | Atomic reference |
| ability_scores | 6 | STR/DEX/CON/INT/WIS/CHA |
| diseases | 3 | Cackle Fever, Sewer Plague, Sight Rot |
| **Total** | **1,687** | |
<!-- AUTO-SYNC:arch:stats-table END -->

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
