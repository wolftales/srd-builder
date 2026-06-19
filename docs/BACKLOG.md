# Backlog

Captured ideas not yet scheduled. Pull items into a release plan as priorities allow.

## Completed: v0.27.x — Retire the largest hand-curated surfaces

Five planned retirements + one follow-on structural fix have shipped.
~2,458 lines of hand-curated Python data deleted in total, plus a
silent data-loss bug closed:

- **P1 — `lineage_targets.py` (326 lines, v0.27.0)** — replaced by
  [src/srd_builder/extract/datasets/extract_lineages.py](src/srd_builder/extract/datasets/extract_lineages.py).
- **P2 — `spell_class_targets.py` (917 lines, v0.27.0)** — replaced by
  [src/srd_builder/extract/datasets/extract_spell_classes.py](src/srd_builder/extract/datasets/extract_spell_classes.py).
- **P3 — `class_targets.py` (763 lines, v0.27.2)** — replaced by
  [src/srd_builder/extract/datasets/extract_classes.py](src/srd_builder/extract/datasets/extract_classes.py).
  Five-step pipeline (discovery → hit_die+abilities+proficiencies →
  features+subclasses → spellcasting → bbox-aware progression walk).
  `parse_classes()` and `parse_features()` now take `class_data=` kwargs;
  `build.py` calls `extract_classes()` once and threads the result.
- **P4 — `poison_descriptions.py` (129 lines, v0.27.3)** — replaced by
  [src/srd_builder/parse/parse_poison_descriptions.py](src/srd_builder/parse/parse_poison_descriptions.py).
  Damage-formula regex extended from `takes?` to `tak(?:es?|ing)` to cover
  the four delayed-damage poisons; description header strip and `type_id`
  emission added; 14/14 byte-perfect parity vs. legacy `POISON_DESCRIPTIONS`.
  `parse_poisons_table.py` no longer imports the manual dict.
- **P5 — `extract_equipment.py` page-constants drift (v0.27.4)** —
  `EQUIPMENT_START_PAGE` / `EQUIPMENT_END_PAGE` were 0-indexed where the
  other three per-dataset extractors are 1-indexed; the end constant was
  off by one. Harmonized to 1-indexed (`62`–`74`, matching
  `PAGE_INDEX["equipment"]`) which recovers 8 silently-dropped rows from
  PDF page 74 (Bread loaf, Inn-stay tiers, Skilled hireling, Messenger,
  Ship's passage, etc.). Pinned by new audit test
  [tests/test_pdf_provenance.py::test_extractor_page_constants_agree_with_page_index](tests/test_pdf_provenance.py),
  parametrized across equipment, spells, magic_items, conditions.
- **P6 — `equipment_packs.py` (323 lines, v0.27.5)** — replaced by
  [src/srd_builder/extract/datasets/extract_equipment_packs.py](src/srd_builder/extract/datasets/extract_equipment_packs.py).
  Parser walks PDF page 70 with a pack-header regex
  (`{Name}’s Pack (N gp).`) and a section-end sentinel (`Tools\nA tool helps`),
  splits each `Includes …` clause on `, ` / ` and ` boundaries, and
  resolves each token through a small typed `_PHRASE_TO_ITEM` table that
  maps the SRD's exact prose phrase to a stable `item_id` and a quantity
  rule. Trailing "50 feet of hempen rope strapped to the side" sentence
  handled. Curly-apostrophe (U+2019) normalized to ASCII at output.
  7-for-7 byte-perfect parity (name, cost_gp, description, contents) vs.
  the retired `EQUIPMENT_PACKS` literal. `assemble_equipment_from_tables`
  now takes an `equipment_packs=` kwarg; `build.py` calls
  `extract_equipment_packs()` once and threads the result.
- **P7 — `equipment_descriptions.py` (398 lines, v0.27.6)** — replaced by
  [src/srd_builder/extract/datasets/extract_equipment_descriptions.py](src/srd_builder/extract/datasets/extract_equipment_descriptions.py).
  Parser walks four sections (armor p.63, adventure_gear pp.66–68, tools
  pp.70–71, lifestyle p.73) by concatenating each section's pages into a
  single normalized string, finding heading candidates with a Title-Case
  regex that allows lowercase glue words `and`/`or`/`of` in the middle
  (required to recover `block-and-tackle`, `case-map-or-scroll`,
  `potion-of-healing`), filtering through a 69-entry
  `_HEADING_TO_ITEM_ID` dispatch table, and slicing each item's body up
  to either the next resolving heading or one of four known subsection
  terminators (`Heavy Armor`, `Self-Sufficiency`, `Mounts and Vehicles`,
  `Adventuring Gear`). Normalization handles four PDF artifacts:
  soft-hyphen runs (`-\xad‐‑` → `-`) inside compound words, curly
  U+2019 → ASCII, page-footer text (`System Reference Document 5.1 N`)
  stripped to keep cross-page descriptions clean, and line-wrap em-dash
  spacing closed. 69-for-69 recovery; the new extractor surfaced 6
  description-content phrases the curated literal had silently stripped
  (book "described later", gaming-set / holy-symbol / musical-instrument
  table refs, pouch "described earlier", artisans-tools table mention)
  and 2 incorrect curated `page` fields (`item:antitoxin-vial`,
  `item:arcane-focus` are p. 66, not p. 67). `assemble_equipment_from_tables`
  now takes an `equipment_descriptions=` kwarg; `build.py` calls
  `extract_equipment_descriptions()` via the new `_extract_equipment_pdf_data`
  helper alongside the v0.27.5 packs extractor. Pinned by 73 assertions
  including a 69-row parametrized per-item snapshot.

Result: `PROVENANCE.md` registry shrank from 8 → 1 active hand-curated
entry (`equipment_extended.py` cross-reference glue) after v0.27.6
retired the last extractable hand-curated module
(`equipment_descriptions.py`).

### Test infrastructure follow-on (v0.27.7-era)

- **Golden fixture-version drift** — RESOLVED commit `8808222` (no
  version bump; test-infra only). The 16 golden tests compared rendered
  JSON against on-disk fixtures by byte-equality including
  `_meta.generated_by`, so every package version bump silently broke all
  16 goldens until each fixture was manually re-pinned. Introduced
  `assert_golden_matches` pytest fixture in
  [tests/conftest.py](../tests/conftest.py) that compares both documents
  as parsed JSON dicts, overlaying `_meta.generated_by` so version drift
  no longer triggers data-fidelity failures. Version sync stays covered
  by [tests/test_version_consistency.py](../tests/test_version_consistency.py).
  Test count: 580 passed, 19 skipped, 0 failed (was 563/17/19).

---

## Active: Extractor consolidation (attempt #4)

> **Honest framing.** Attempts 1–3 produced the engine in
> [src/srd_builder/extract/patterns.py](../src/srd_builder/extract/patterns.py)
> (7 config-driven pattern types: `standard_grid`, `split_column`,
> `text_region`, `multipage_text_region`, `prose_section`, `calculated`,
> `reference`) and the consolidated `extract/` namespace. The plan to
> move the bespoke per-dataset extractors into `extract/_legacy/`
> awaiting migration to the engine was **only partially right** — and
> we then proceeded to add five new bespoke extractors
> (`extract_lineages.py`, `extract_classes.py`, `extract_spell_classes.py`,
> `extract_equipment_packs.py`, `extract_equipment_descriptions.py`)
> alongside the original seven across v0.27.x without migrating any to
> the engine. The previous BACKLOG framing ("legacy awaiting migration")
> stopped being true the moment we stopped feeding new files through
> the engine. Calling them "legacy" was aspirational; reality is that
> [extract/datasets/](../src/srd_builder/extract/datasets/) is the LIVE
> home of all 13 per-dataset extractors.

### Reframe: `extract/datasets/` is the pattern registry, not a graveyard

The earlier sustainability argument made it sound like the goal is to
*empty* [extract/datasets/](../src/srd_builder/extract/datasets/). It
isn't. The right end state is for the directory to **stay**, with one
file per dataset, but each file shrinks to a slim declarative config
that binds to the engine:

```python
# extract/datasets/extract_pdf_metadata.py (illustrative target shape)
from srd_builder.extract import engine
from srd_builder.extract.patterns import extract_by_config

DATASET_CONFIG = {
    "pattern_type": "document_metadata",
    "fields": ["title", "creator", "page_count", "fingerprint"],
}

def extract_pdf_metadata(pdf_path: str) -> dict:
    return extract_by_config(pdf_path, DATASET_CONFIG)
```

In that end state:

- **`extract/datasets/`** becomes the **pattern registry** — one file
  per dataset, declarative, easy to diff, easy to audit. The directory
  having 13–20 files is a *feature*, not a smell, because each file is
  ~30–60 lines of config rather than ~300–800 lines of bespoke
  PDF-walking logic.
- **`extract/patterns.py`** (+ engine) is where logic gravitates. New
  dataset shapes add a new `pattern_type`; existing shapes reuse one.
- **SRD 5.2.1** = a sibling directory of config files (or per-ruleset
  config overrides) and possibly one or two new pattern types. Engine
  code does not change. This is what makes attempt #4 worth doing.

The migration steps below ("pick one extractor, factor its uniqueness,
ship it, then the next") are how each file *gets* to that slim shape.
We are not deleting files; we are converting bespoke walkers into
pattern bindings.

### Why this matters (the sustainability argument)

Every per-dataset bespoke file we ship doubles in cost when SRD 5.2.1
lands as a second ruleset. 13 files × N rulesets is unbounded growth.
The goal of attempt #4 is: **when SRD 5.2.1 lands, the per-dataset
config changes (page numbers, section headers, table targets, font
fingerprints) but engine code does not**. If we cannot articulate that
in one paragraph, the design is not done.

### Current state (audit 2026-06-19)

13 files in [extract/datasets/](../src/srd_builder/extract/datasets/),
all LIVE (12 imported by `build.py`; `extract_conditions` wired through
`parse_conditions` + tests). Internal quality tiers:

| Tier | Files | Uses `pdf_probe` | Notes |
| --- | --- | --- | --- |
| Modern (full `pdf_probe`) | `extract_equipment_descriptions.py`, `extract_equipment_packs.py` | ✅ `open_pdf` + `page_text` | v0.27.5–v0.27.6 |
| Mixed | `extract_lineages.py`, `extract_classes.py`, `extract_spell_classes.py` | ⚠️ `normalize_whitespace` only; still raw `fitz.open()` | v0.27.0–v0.27.2 |
| `ProseExtractor` framework | `extract_conditions.py` | ✅ (via `utils.prose`) | Higher abstraction |
| Pre-`pdf_probe` (legacy) | `extract_equipment.py`, `extract_magic_items.py`, `extract_features.py`, `extract_pdf_metadata.py`, `extract_rules.py`, `extract_monsters.py`, `extract_spells.py` | ❌ raw `fitz.open()` | **7 files violating AGENTS.md rule** |

All 7 raw-`fitz` files legitimately extract from PDF (walk pages, produce
raw JSON, no fabricated content). The problem is mechanism, not output:
they bypass `pdf_probe`'s deterministic-output and hidden-doc-lifecycle
guarantees, and they are not registered as engine pattern configs.

### Proposed approach (gradual, one extractor per release)

Forced big-bang migration is what failed attempts 1–3. The pattern that
worked in v0.27.x retirements was **pick one target, factor its
uniqueness, ship it, then the next**. Apply the same here:

1. Each release picks ONE bespoke extractor.
2. Identify the shape — does it map to an existing engine `pattern_type`,
   or does it need a new one (e.g., `font_fingerprint_walk` for monster
   stat blocks; `bbox_cursor_walk` for class progression tables)?
3. Add the pattern type to [patterns.py](../src/srd_builder/extract/patterns.py)
   if needed; add the dataset's config to
   [extraction_metadata.py](../src/srd_builder/extract/extraction_metadata.py).
4. Delete the bespoke file.
5. Pin parity (byte-perfect against pre-migration raw JSON, same way
   v0.27.5 P6 / v0.27.6 P7 did).

**Suggested order (cheapest → hardest):** `extract_pdf_metadata.py` (no
data shape, just doc metadata) → `extract_rules.py` (simple prose pages)
→ `extract_equipment.py` (table-grid, already overlaps engine domain) →
`extract_magic_items.py` → `extract_features.py` → `extract_spells.py` →
`extract_monsters.py` (largest, most unique shape, do last).

### Parse-layer consolidation (forward-looking, not v0.28.0 scope)

The same framework lesson should apply to [parse/](../src/srd_builder/parse/):
~15 modules each doing record-walking, prose-normalizing, id-synthesizing,
cross-reference-resolving in their own shape. Possible pattern types for
a parse engine: `record_walker`, `table_row_mapper`, `prose_narrator_stripper`,
`cross_reference_resolver`, `schema_stamp_normalizer`, `id_synthesizer`.

Do NOT start parse consolidation until extract consolidation has migrated
at least 3–4 datasets and the pattern is proven. The hard part is not
the design; it is resisting "this one is different, I will just write
it bespoke" for every dataset.

### Bottom line

We do not want multiple different approaches to extracting and later
parsing SRD sections. One approach (config-driven engine + pattern
types). Treat every new bespoke file as a regression on that goal.

---

## Active: v0.28.0 — Data integrity foundation

Builds on the engine-already-exists fact above: the data-integrity work
should produce artifacts (exemplars, known_truths, audit codes) that
multiple datasets share, instead of bespoke checks per dataset. Same
unification principle.

### Phase A — Schema → exemplar generator (foundation for B and the docs/templates issue)

- New `scripts/generate_exemplars.py`: walks `schemas/*.schema.json`,
  for each schema constructs a minimal valid example exercising every
  required field plus one optional, validates the result against its
  own schema with `jsonschema`, writes to
  `dist/<ruleset>/exemplars/<dataset>.example.json`.
- Replaces hand-written [docs/templates/](templates/) (5 stale exemplars
  vs. 16 schemas; spell template still pinned to `v1.3.0`).
- Drops the 5 hand-written templates; the generated set ships in the
  bundle next to `schemas/`.
- Wins three-for-one: homebrew authoring template + known_truths baseline
  pattern + schema round-trip smoke test (every schema must validate its
  own exemplar via `jsonschema.validate`). Build once, consume thrice.

### Phase B — `tests/fixtures/known_truths.json` (depends on Phase A)

> **✅ DONE 2026-06-19** (commit forthcoming). Design hardened after
> discovering CI has a structural inability to verify dist (no PDF, no
> build). Final design: known_truths is a **release-gate** test, not a
> CI test. `pytest tests/test_known_truths.py` is invoked inside
> `scripts/release_check.sh` and skips with a loud message when run
> outside a built tree. 37 truths spanning all 16 datasets, all passing.
> Datasets covered: ability_scores, classes, conditions, damage_types,
> diseases, equipment, features, lineages, magic_items, monsters,
> poisons, rules, skills, spells, tables, weapon_properties.

- Hand-curate ~30 facts spanning all 16 datasets: "Fireball is
  3rd-level evocation, 8d6 fire"; "Goblin AC is 15"; "Barbarian hit die
  is d12"; "Acid damage type id is `acid`".
- New `tests/test_known_truths.py` walks the file and asserts each fact
  against `dist/srd_5_1/*.json`.
- Single test file = single regression-catch point for "did we silently
  break a thing humans actually look up".

### Phase C — Audit codes (independent of A/B) — ✅ DONE 2026-06-19 (3 of 4)

Extended [scripts/audit_dataset_quality.py](../scripts/audit_dataset_quality.py)
with three of the four spec'd codes:

- ✅ `non_ascii_in_text` — `MOJIBAKE_RE = â€|Ã[\xa0-\xbf]`. Catches the
  UTF-8 → windows-1252 / latin-1 mis-decode family. 0 findings on current
  dist (clean).
- ✅ `hyphenation_artifact` — `[A-Za-z]{2,}-\s+[a-z]+` catches PDF soft-hyphen
  line breaks (`two- handed`, `well- being`, `5th- level`). **151 real
  findings** in current dist — all genuine PDF stitching bugs, none false
  positives. **FIXED 2026-06-19** in `postprocess/text.py`: pattern
  broadened to `(\w+)-\s+(\w+)` (with suspended-hyphen guard for
  `and`/`or`/`but`/`nor`, case-insensitive) and run to fixed point so
  chained dimensional expressions resolve fully. Covers letter-letter
  (`two-handed`), digit-letter (`10-foot`), letter-digit (`foot-by-5`),
  Title-Case (`Two-Headed`, `Sure-Footed`), and single-letter appendix
  refs (`PH-A`). Applied in both `clean_text()` and `polish_text()`
  after whitespace normalization. The audit `HYPHENATION_RE` was
  broadened to the same pattern so future regressions surface on the
  same signal. Post-fix audit: 0 hyphenation findings. Survey across
  all 16 datasets showed zero false positives with the broader pattern.
- ✅ `word_boundary_loss` — `\b[A-Za-z]{21,}\b` for run-on tokens
  (`fireballyou`). 0 findings on current dist (clean).
- ⏳ `unknown_word` — deferred. Needs `pyspellchecker` dep + extended
  dictionary built from all dataset names to avoid noise. Standalone task.

The 151 hyphenation findings are the next backlog item — fix the extractor's
line-stitching pass, not the audit. **✅ DONE 2026-06-19** — fix shipped
in `postprocess/text.py::_HYPHEN_LINE_BREAK_RE`, run to fixed point in
both `clean_text()` and `polish_text()`. Audit pattern broadened to
match. See the `hyphenation_artifact` line above for details.

### Phase D — Round-trip PDF sampling — ✅ DONE 2026-06-19

Shipped as [tests/test_round_trip_pdf.py](../tests/test_round_trip_pdf.py).
For each shipped dataset, samples the first 5 records (sorted by id),
looks up each record's `page` field, renders the corresponding PDF page
via `utils.pdf_probe`, and asserts the record's `name` appears as a
substring within ±1 page of the declared page.

Design:
- **Sampling:** deterministic (first 5 by id), not random — reproducible
  failures matter more than coverage breadth for a smoke test.
- **Matching field:** `name` only (`name`-with-`text`-fallback was
  considered and deferred to keep the false-positive floor at zero).
- **Tolerance:** ±1 page — the `page` field is the heading page, which
  the SRD often places one page before the actual subheading body;
  >±1 = real bug.
- **Skip behavior:** mirrors `tests/test_pdf_provenance.py` — skips
  loudly when the PDF or pymupdf is absent (CI / container builds).
- **Dataset scope:** all 15 datasets with a `page` field. `lineages` is
  excluded (its records carry no `page` by design).

Result: 12 datasets pass cleanly. 3 surface real page-field drift and
ship as `xfail` (test passes today, removes the marker when fixed):

- **`skills`** — 1/5 fails. `Athletics` declared p76, body on p78.
- **`tables`** — 2/5 fail. `Ability Scores and Modifiers` declared p7
  but body on p76; `Adventure Gear` not found by name anywhere.
  Likely stale TOC-derived page numbers in the tables extractor.
- **`weapon_properties`** — 5/5 fail. All 11 records claim p147 but
  the weapon-property prose is elsewhere. Looks like a single hardcoded
  page constant.

These three drift cases are the natural follow-on backlog item
("Page-field drift in skills/tables/weapon_properties") — see below.

### Phase D follow-on — Fix page-field drift surfaced by round-trip test — ✅ DONE 2026-06-19

All three xfail datasets in `tests/test_round_trip_pdf.py` are now fixed
and ship green. `_XFAIL_DATASETS` is empty; round-trip test now covers
all 15 page-bearing datasets without exception.

- **`weapon_properties`** ✅ — all 11 records hardcoded to `page=147`
  (apparently a PHB print-page reference, not SRD PDF page). Updated to
  actual SRD locations: ammunition + finesse → p64; heavy, light,
  loading, range, reach, special, thrown, two_handed, versatile → p65.
  Module docstring corrected from "page 147" to "pages 64-65"; golden
  test `test_weapon_properties_have_required_fields` relaxed from
  `page == 147` to `page in (64, 65)`.
- **`tables`** ✅ — two fixes in `extract/table_targets.py`:
  (1) `table:ability_scores_and_modifiers` had `page=7` referencing the
  Characters chapter; the actual table is in Chapter 7 (Using Ability
  Scores) on p76. (2) `table:adventure_gear` was misnamed — PDF heading
  is "Adventur**ing** Gear" and is on p68, not "Adventure Gear" on p69.
  `id` and `simple_name` preserved as `adventure_gear` to avoid breaking
  downstream cross-references; only `name` and `page` corrected. Updated
  `tests/fixtures/expected_table_pages.json`, `raw/tables.json` (added
  `simple_name` to keep id stable through postprocess), and
  `normalized/tables.json`. `test_golden_tables.py` extended to forward
  `id`/`simple_name` from raw when present (mirrors real extraction
  where TARGET_TABLES hardcodes these).
- **`skills`** ✅ — single-line fix in `parse_skills.py`: Athletics had
  `page=76` but the skill description body is on p78. Audit confirmed
  this was an isolated typo, not endemic — the other 17 skills all
  point at their actual SRD pages (77/78/79).

`known_truths.json` updated for the affected ids (`skill:athletics`,
`weapon_property:finesse`, `weapon_property:two_handed`) so the Phase B
release gate stays consistent.

Test suite: 643 passed / 19 skipped / 0 xfailed (was 640 / 19 / 3).

---

## Active: v0.29.0 — Postprocess engine consolidation (Phase 1)

> **Status:** Planned 2026-06-19. Decision: finish the prototyped
> `postprocess/engine.py` rather than delete it. This is the same
> "config-driven dispatcher" idiom already proven in `extract/`
> (`extractor.py` + `extraction_metadata.TABLES` + `patterns.py`)
> being landed at the postprocess stage. See
> [docs/ARCHITECTURE.md § Config-Driven Engine Pattern](../docs/ARCHITECTURE.md)
> for the cross-stage architectural picture.

### Context

The 19 currently-skipped tests in
[tests/test_engine_postprocess.py](../tests/test_engine_postprocess.py)
gate an experimental config-driven postprocess engine
([src/srd_builder/postprocess/engine.py](../src/srd_builder/postprocess/engine.py)
+ [configs.py](../src/srd_builder/postprocess/configs.py)) that was
prototyped to replace the 16 per-dataset postprocess modules with one
declarative engine driven by `DATASET_CONFIGS`. The refactor was never
finished — production still calls per-dataset `clean_*_record`
functions, the engine sits idle, and the test suite gates it under a
module-level `pytestmark.skip(reason="Engine is WIP …")`.

### Why finish it (not delete it)

The 12 boilerplate-heavy postprocess modules each do the same five
things — ensure `simple_name`, ensure `id`, polish text fields, polish
text arrays, polish nested-struct fields — in ~30-50 lines apiece.
Engine + 5-line config replaces them cleanly. The other 4 modules
(`monsters`, `rules`, `spells`, `equipment`) contain real domain
logic (legendary-action parsing, ability-modifier derivation, action
structures, statblock cleanup) that doesn't reduce to declarative
config and stays custom.

Net effect of Phase 1: ~400 lines deleted from `postprocess/`,
19 skips become passes, the README/PKG-INFO architecture claim
("engine.py drives DATASET_CONFIGS for normalization") stops being
a lie, future-SRD support for the boilerplate-heavy datasets becomes
"add a config entry" instead of "write another module."

### Scope (Phase 1)

**In scope — migrate to engine via `DATASET_CONFIGS` entry:**

- `postprocess/poisons.py` (35 lines) — 4-line config
- `postprocess/diseases.py` (44 lines) — 5-line config
- `postprocess/conditions.py` (44 lines) — 5-line config
- `postprocess/features.py` (39 lines) — 4-line config
- `postprocess/lineages.py` (52 lines) — 8-line config (nested traits)
- `postprocess/tables.py` (48 lines) — config + small `_clean_table_rows`
- `postprocess/classes.py` (56 lines) — config + small `_clean_class_proficiencies`
- `postprocess/ability_scores.py` (28 lines) — 3-line config
- `postprocess/damage_types.py` (28 lines) — 3-line config
- `postprocess/skills.py` (28 lines) — 3-line config
- `postprocess/weapon_properties.py` (28 lines) — 3-line config
- `postprocess/magic_items.py` (47 lines) — config + small custom transform

**Out of scope — keep as custom modules:**

- `postprocess/monsters.py` (370 lines) — legendary parsing, ability
  modifiers, action structures, defense restructuring
- `postprocess/rules.py` (123 lines) — chapter/section custom logic
- `postprocess/spells.py` (62 lines) — takes external `spell_classes_map=`
  kwarg; non-trivial constructor
- `postprocess/equipment.py` (53 lines) — small but takes pack/description
  kwargs and applies them across record types

### Tasks

1. Audit the 12 target modules for any behavior the current engine
   config schema doesn't express. Extend `RecordConfig` only if a real
   gap exists (don't pre-emptively add knobs).
2. Add config entries to `DATASET_CONFIGS` for the 7 not yet covered
   (`ability_scores`, `damage_types`, `skills`, `weapon_properties`,
   `magic_items`, and confirm `classes`/`features` are accurate).
3. Wire engine into `build.py` for the 12 migrated datasets. Keep
   per-dataset calls for the 4 custom ones.
4. Delete the 12 migrated per-dataset postprocess modules. Update
   `__init__.py` re-exports.
5. Remove `pytestmark.skip` from
   [tests/test_engine_postprocess.py](../tests/test_engine_postprocess.py).
   Fix any fixture-format drift surfaced when the 19 tests run for real.
6. Update [README.md](../README.md) and PKG-INFO architecture section
   to accurately describe the hybrid: engine drives 12 datasets,
   custom modules drive 4 (monsters/rules/spells/equipment).
7. Run full test suite + build verification.
8. **Quality gate (acceptance criterion):** run
   `scripts/audit_dataset_quality.py` and `scripts/quality_report.py`
   on the dist output before and after the migration. Output must be
   equivalent or strictly better — no regression in record counts,
   completeness, schema validation, or quality metrics. Byte-identical
   JSON for the 12 migrated datasets is the target; any diff must be a
   documented improvement (e.g., a dead-code bug the engine fixes).
9. Ship as v0.29.0 (minor bump — consumer-visible if anyone imports
   `srd_builder.postprocess.conditions.clean_condition_record`
   directly; JSON output unchanged).

### Out of scope (Phase 2 + Phase 3 — separate decisions later)

- **Phase 2** — consider migrating `spells`/`equipment` to engine via
  richer `custom_transform`. Small wins; not urgent.
- **Phase 3** — apply the same config-driven idiom to `parse/`. Bigger
  investment (parse is where each dataset's logic differs most), higher
  risk. Do NOT start until Phase 1 has been in production for at least
  a release. See also "Parse-layer consolidation" notes in the
  Extractor-consolidation section above.
- **Per-dataset registry** — a single registry mapping
  `dataset → {schema, extract_config, parse_strategy, postprocess_config}`
  is the architectural endgame. Premature until Phase 1 + Phase 3 ship
  and we can see what the per-stage configs actually look like.
- **Cross-stage naming consistency** — ✅ DONE in **v0.29.1**.
  `extract/extractor.py` renamed to `extract/engine.py` (via `git mv`,
  history preserved) so the config-driven dispatcher has the same
  filename in every stage that uses the pattern (`extract/engine.py`,
  `postprocess/engine.py`, eventually `parse/engine.py`). Single
  import site updated (`extract/__init__.py`); README + ARCHITECTURE
  references updated.
- **Unify the two assembly code paths** — ⚠️ PARTIALLY DONE in **v0.29.2**;
  the remaining split is **historical, not principled** (corrected
  2026-06-19). Inline `poisons_doc` / `features_doc` construction in
  `build.py::build_dataset()` moved into `_write_datasets`; 14 of 16
  datasets now share one path (`clean_records → wrap_with_meta → write`).
  `conditions` and `diseases` still flow through
  `assemble.assemble_prose_dataset` and ship a richer `_meta` block
  (`dataset`, `source_pages`, `description`, `pdf_sha256`,
  `{output_key}_count`, `extraction_warnings`) that the other 14
  datasets don't get. **Initially justified as a principled split**
  ("prose datasets need the richer meta"); on review that's wrong —
  every PDF-extracted dataset (equipment, spells, monsters, magic items,
  lineages, classes, features, poisons, ability scores, damage types,
  skills, weapon properties, tables, rules) would benefit from the same
  provenance fields. The split is an artifact of which two modules
  happened to be the first ones generalized when `assemble_prose_dataset`
  was introduced; the older modules predate the pattern and never got
  migrated. **Fix:** lift the prose `_meta` shape onto all 16 datasets
  (additive, non-breaking) and collapse the two code paths once the
  shape is uniform. Tracked as the **`_meta` block normalization**
  bullet in the v0.30.0 plan below.
- **Normalize dist output keys to `items` across all 16 datasets**
  (v0.30.0 candidate) — `features.json` ships `{"_meta", "features": [...]}`
  and the two prose datasets ship `{"_meta", "conditions"|"diseases": [...]}`,
  while the other 13 simple datasets ship `{"_meta", "items": [...]}`.
  This is a consumer-visible breaking change (downstream tooling that
  reads `doc["features"]` would have to switch to `doc["items"]`), so
  it's a major-version-bump-worthy ticket rather than a silent cleanup.
  When done: drop the per-dataset `output_key` knob in
  `_write_datasets` and the special-case `"features"` branch; update
  the fixture-key handling in `tests/test_engine_postprocess.py` and
  `tests/test_validate_references.py`; bump schema versions for
  `features` and the two prose datasets.

## Active: v0.30.0 — Schema-consistency sweep (Blackmoor migration window)

> **Goal.** A single coordinated breaking-change release so downstream
> consumers (Blackmoor first) have **one migration** to absorb instead
> of three or four trickling out as patch releases. Every item below
> is consumer-visible at the dataset JSON layer; collectively they
> close the long-standing "inconsistent shape" complaint that's been
> sitting in PARKING_LOT ("JSON Field Ordering & Consistency") since
> the v0.10 era.

### Phase 1 — `_meta` block normalization (additive, safe-to-ship-first)

All 16 datasets adopt the same `_meta` shape, currently only on
`conditions` and `diseases`:

| Field                  | Source                                       | Today (14 simple) | Today (2 prose) |
| ---------------------- | -------------------------------------------- | :---------------: | :-------------: |
| `source`               | `RULESETS[ruleset].source_id`                |        ✅         |       ✅        |
| `ruleset_version`      | `RULESETS[ruleset].ruleset_version`          |        ✅         |       ✅        |
| `schema_version`       | per-dataset                                  |        ✅         |       ✅        |
| `generated_by`         | `srd-builder vX.Y.Z`                         |        ✅         |       ✅        |
| `build_report`         | `./build_report.json`                        |        ✅         |       ✅        |
| `dataset`              | dataset name                                 |        ❌         |       ✅        |
| `source_pages`         | start–end page range from `PAGE_INDEX`       |        ❌         |       ✅        |
| `description`          | from `TABLES` config                         |        ❌         |       ✅        |
| `pdf_sha256`           | hash of source PDF                           |        ❌         |       ✅        |
| `item_count`           | `len(items)`                                 |        ❌         |       ✅        |
| `extraction_warnings`  | per-record parser warnings (`[]` if clean)   |        ❌         |       ✅        |

**Why first:** purely additive at the JSON layer. Any consumer that
reads `doc["_meta"]["source"]` keeps working unchanged. Lets us validate
the shape against Blackmoor before any breaking change lands.

**Implementation:** extend `utils.metadata.wrap_with_meta` to accept the
additional kwargs and emit them when supplied; thread `pdf_sha256` /
`source_pages` / `extraction_warnings` through `_write_datasets` for
the 14 simple datasets (most already have these values available
upstream). For datasets with no extraction warnings, emit `[]`.

**Could ship alone as v0.29.3 if Blackmoor wants the provenance fields
before the breaking changes.** Otherwise bundle into v0.30.0.

### Phase 2 — Output-key normalization (breaking)

All 16 datasets ship `{"_meta": ..., "items": [...]}`. Affected files:

- `features.json`: `{"features": [...]}` → `{"items": [...]}`
- `conditions.json`: `{"conditions": [...]}` → `{"items": [...]}`
- `diseases.json`: `{"diseases": [...]}` → `{"items": [...]}`

Bumps `schemas/features.schema.json`, `schemas/condition.schema.json`,
`schemas/disease.schema.json` (top-level `items` array required).

**Migration note for Blackmoor:** the only change is the key name;
record shape inside the array is unchanged.

### Phase 3 — Duplicate-id resolution (breaking IDs)

The 22 `duplicate_id` audit findings break into two classes that need
different fixes:

**Rules (19 findings) — same name, different content. Disambiguate.**

Example: `rule:strength` collides between p78 (a one-line
`"Athletics"` skill-grouping stub under the Strength heading) and p79
(the actual Strength ability description). Fix by including section
context in the id, e.g. `rule:ability_scores/strength` and
`rule:skills/strength`. The duplicates list:

```
rule:ability_scores_and_modifiers  (2x)
rule:strength                       (2x)
rule:dexterity                      (2x)
rule:intelligence                   (2x)
rule:wisdom                         (2x)
rule:charisma                       (2x)
rule:attack_rolls_and_damage        (2x)
rule:initiative                     (2x)
rule:hit_points                     (2x)
rule:spellcasting_ability           (3x)
rule:saving_throws                  (2x)
rule:time                           (2x)
rule:movement                       (2x)
rule:speed                          (2x)
rule:travel_pace                    (4x)
rule:difficult_terrain              (2x)
rule:reactions                      (2x)
rule:attack_rolls                   (2x)
rule:range                          (2x)
```

Likely the cleanest fix is to namespace by parent section:
`rule:{section_simple_name}/{name_simple}` (mirrors how `tables/skills`
already disambiguate by category).

**Tables (3 findings) — same name, identical content extracted twice.
Deduplicate.**

`table:lifestyle_expenses`, `table:food_drink_lodging`, `table:services`
all appear once in the equipment chapter (pp72-74) and again in the
appendix (pp157-159) with byte-identical rows. Fix by suppressing the
appendix copies during extraction (the chapter copies are the
canonical source). Reduces `tables.json` from 19 to 16 records.

### Phase 4 — Code-path collapse (refactor, follows Phase 1)

Once Phase 1 makes `_meta` uniform, the only remaining difference
between the simple path and the prose path is *who extracts the
records from the PDF*. Refactor: `_write_datasets` becomes the single
write path; `assemble_prose_dataset` becomes a parser that returns
`(records, pdf_sha256, warnings)` and is called from `_write_datasets`
like any other parser. Closes the open "Unify the two assembly code
paths" bullet completely.

### Suggested ship order

1. **v0.29.3** — Phase 1 alone (additive). Lets Blackmoor consume the
   provenance fields immediately without taking the breaking changes.
2. **v0.30.0** — Phases 2 + 3 + 4 together (single breaking release).
3. **v0.30.x** — Round-trip xfail fixes (page-field drift in
   `weapon_properties` / `tables` / `skills` — already in BACKLOG),
   source-derivation marker (PARKING_LOT), and any Blackmoor feedback.

### Out of scope for v0.30.0 (already deferred / parked)

- Item Variants & Magic Items architecture (PARKING_LOT — needs second
  ruleset or real consumer pain point).
- Sentient Magic Items as Rules content (PARKING_LOT).
- Combined spell indexes (PARKING_LOT — low priority).
- `terminology.aliases` shape (PARKING_LOT — wait for second ruleset).
- Container capacity hardcoded fallback (PARKING_LOT — 5/13 records).
- Equipment table cross-references as structured field (PARKING_LOT).
- Field grouping / nested objects (the v2.0 "data model restructure"
  item on ROADMAP).

### Phase D follow-on — Original entry (kept for history)

Three datasets ship `xfail` in `tests/test_round_trip_pdf.py`. Each is
a small parser-side fix:

- **`weapon_properties`** (5/5 records misplaced) — find and replace the
  hardcoded `page = 147` in the weapon-properties extractor with the
  actual page where each property's prose appears. Likely the highest-
  impact fix of the three because it's a systematic 11-record bug.
- **`tables`** (2/5 records misplaced) — `table:ability_scores_and_modifiers`
  is recorded at p7 (lineages section) but appears on p76; investigate
  whether the table-extractor is consulting a stale TOC. `Adventure Gear`
  needs name-vs-PDF-prose investigation (the table header may differ).
- **`skills`** (1/5 records off by two) — `Athletics` at p76→p78 looks
  like the skill is on a different page than its section header. May be
  endemic to all skills (check the other 17 records, not just the first
  5 sampled).

When each is fixed, drop the `xfail` mark in
`tests/test_round_trip_pdf.py::_XFAIL_DATASETS` and re-run the test.

**Suggested order:** A → B → C → D. Ship A+B as v0.28.0; C as v0.28.1;
D as v0.28.2.

---

## Completed: Cruft cleanup (drive-by, 2026-06-19)

> **✅ DONE.** Captured during the 2026-06-19 audit, shipped as a single
> REMOVE commit alongside this BACKLOG closeout. No version bump (no
> shipped-data changes). Items closed:

- **Dead code: `TABLES_APPENDIX` + `get_tables_toc()`** in
  [src/srd_builder/utils/page_index.py](../src/srd_builder/utils/page_index.py)
  — ~30 lines of hand-curated table-name/page/category tuples + ~20-line
  formatter function. **Zero callers in the codebase.** The actual
  `dist/tables.json` is built by extraction (`TARGET_TABLES` engine
  config + `TableExtractor`), not from this hand-maintained list.
  **Deleted.**
- **Empty cruft package: `src/srd_builder/rulesets/`** — `__init__.py`
  (empty) plus `srd_5_1/__init__.py` (one-line "hardcoded targets -
  legacy tech debt" docstring on an otherwise empty module). Nothing
  imports `srd_builder.rulesets.*`. Vestigial scaffold from the v0.26.2
  multi-ruleset refactor. The actual `rulesets/` directory the build
  uses is a top-level sibling of `src/`, not this nested Python package.
  **Deleted.**
- **Stale comments in
  [src/srd_builder/constants.py](../src/srd_builder/constants.py)** —
  the `RULESETS` registry docstring referenced `srd_builder.rulesets.<id>`
  and instructed new-ruleset adders to create
  `src/srd_builder/rulesets/<id>/`. **Fixed** (references removed; step
  3 collapsed into step 2).

---

## Data integrity / extraction confidence

> **See also `## Active: v0.28.0 — Data integrity foundation` above** —
> Phases A–D crystallize the v0.28.x release shape from items below
> (`known_truths.json` becomes Phase B; the audit codes become Phase C;
> round-trip sampling becomes Phase D). The text below is the broader
> superset; the v0.28.0 plan is what is actually scheduled.

Goal: build justified confidence that what we extracted matches the PDF source,
beyond the count-based + cross-reference checks we have today.

### Round-trip / source-of-truth verification
- **Round-trip sampling** — for each dataset, sample N items, look up their
  PDF page + coords (PyMuPDF gives bounding boxes), render that PDF region as
  text, and assert the parsed `text` field is a substring (or close fuzzy
  match) of the rendered region. Catches silent parsing drift.
- **Independent reference cross-check** — spot-check ~10 items per dataset
  against an independent SRD source (Open5e API, D&D Beyond machine-readable
  dumps) to detect single-source bias. Treat mismatches as findings, not
  failures — they often surface ambiguity in the SRD itself.
- **`tests/fixtures/known_truths.json`** — hand-curated `~30` facts ("Fireball
  is 3rd level evocation, 8d6 fire damage"; "Goblin AC is 15"; "Barbarian hit
  die is d12"). One assertion per fact, run every build. Cheap, high-signal.

### Section / structural verification
- **`scripts/verify_pdf_sections.py`** — walk the PDF outline via
  `fitz.Document.get_toc()` and assert each top-level section begins on the
  expected page. Today the page numbers in `CLASS_DATA` / `LINEAGE_DATA` are
  author-curated and not verified against the source.
- **Surface TOC in `meta.json`** — we already track section provenance in
  `meta.json`. Extend it with a `toc` block keyed by section name → page
  range, populated from `doc.get_toc()`, so consumers can verify their slice.
- **Font-fingerprint regression** — record the font + size we treat as
  feature/section headers (today: `GillSans-SemiBold 13.9pt`). A test that
  re-extracts and asserts the fingerprint is unchanged catches silent
  upstream PDF or library updates.

### Text-level data sanity (the "non-English / spelling" pass)
Add as new audit codes in `scripts/audit_dataset_quality.py`:
- **`non_ascii_in_text`** — flag chars outside a known-good Unicode set
  (smart quotes `'`, em-dashes `—`, bullets `•` are OK; mojibake like
  `â€™` is not).
- **`hyphenation_artifact`** — regex `\b\w+-\s\w+\b` catches `light- ning`,
  `con- tinue` style PDF line-break artifacts.
- **`word_boundary_loss`** — flag alphabetic tokens longer than ~20 chars
  (e.g., `fireballyou` from a missing newline).
- **`unknown_word`** — run `pyspellchecker` over **item names only** (not
  body text — too many fantasy terms) with an extended dictionary that
  loads in all class / monster / spell / item names. Output for human
  review, not automated failure.

## Process / tooling

- **Automate the macOS `chflags -R nohidden .venv` workaround** — bake it
  into the `Makefile` `bundle` target so a fresh contributor doesn't hit
  the UF_HIDDEN pip bug.
- **Convert hand-curated `EXPECTED_COUNTS`** in
  `tests/test_dataset_completeness.py` into a generated `expected_counts.json`
  derived from PDF section page-count math, so it self-updates when the
  source PDF revises.

## Provenance audit (hand-curated data inventory)

Goal: every value in the published bundle must trace back to either (a) the
SRD PDF byte stream, or (b) an explicitly-declared, justified deviation.
Today several modules contain hand-curated values whose divergence from
source is *implied* by the file docstring but not formally tracked, tested,
or surfaced to downstream consumers.

### Inventory of hand-curated sources

Wiring column verified via `grep_search` on 2026-06-17 and re-verified in
v0.27.x P3 after `class_targets.py` was retired. `LIVE` = imported by
`build.py` / `parse/` / `postprocess/` / `assemble/`. `DEAD` = no callers in
`src/srd_builder/` (only archived code or tests reference it).

| Module | Wiring | Scope | Declared reason | Concerns |
| --- | --- | --- | --- | --- |
| ~~`src/srd_builder/rulesets/srd_5_1/class_targets.py`~~ | **DELETED v0.27.x P3** | (was all 12 classes, 763 lines: hit_die, primary_abilities, saving throws, proficiencies, feature lists, subclass names, page numbers, 20-level progression) | "Manually transcribed via visual inspection" (pp. 8–55) — **DISPROVEN** | Replaced by [src/srd_builder/extract/datasets/extract_classes.py](src/srd_builder/extract/datasets/extract_classes.py) — five-step pipeline (discovery → hit_die+abilities+proficiencies → features+subclasses → spellcasting → bbox-aware progression walk). Snapshot parity for all 12 classes × 20 levels = 240 rows; 4 genuinely-unextractable cells (barbarian L11, ranger L8, rogue L10, wizard L20) filled by `_PROGRESSION_FIXES`, each pinned by a `page.search_for()` reproducer. `parse_classes()` and `parse_features()` now take `class_data=` kwargs; `build.py` calls `extract_classes()` once and threads the result. Listed here for history. |
| ~~`src/srd_builder/rulesets/srd_5_1/lineage_targets.py`~~ | **DELETED v0.27.0 P1** | (was all 9 lineages + 4 subraces, 326 lines) | "PDF text is corrupted; manually transcribed" — **DISPROVEN** | Replaced by [src/srd_builder/extract/datasets/extract_lineages.py](src/srd_builder/extract/datasets/extract_lineages.py) (font-fingerprint walk over pp. 3–7, +49 test assertions). Listed here for history. |
| ~~`src/srd_builder/rulesets/srd_5_1/spell_class_targets.py`~~ | **DELETED v0.27.0 P2** | (was 917 lines, largest hand-curated surface) | "PDF text is corrupted; manually mapped" — **DISPROVEN** | Replaced by [src/srd_builder/extract/datasets/extract_spell_classes.py](src/srd_builder/extract/datasets/extract_spell_classes.py) — produced a byte-perfect 778-for-778 match against the retired `*_SPELLS` lists across all 8 caster classes. `clean_spell_record()` now takes an explicit `spell_classes_map=` kwarg. Listed here for history. |
| ~~`src/srd_builder/rulesets/srd_5_1/poison_descriptions.py`~~ | **DELETED v0.27.3** | (was full prose + DC + damage for all 14 SRD poisons, 129 lines) | "Corrupted text on pages 204–205" — **DISPROVEN v0.27.1** | Replaced by [src/srd_builder/parse/parse_poison_descriptions.py](src/srd_builder/parse/parse_poison_descriptions.py). v0.27.1 fixed the splitter (smart-quote `clean_text`, `start_marker="Sample Poisons"`, restored `Assassin's Blood` header, renamed `assassin's_blood` key). v0.27.3 extended the damage-formula regex from `takes?` to `tak(?:es?\|ing)` (covers `midnight_tears`, `purple_worm_poison`, `serpent_venom`, `wyvern_poison`), stripped the leading `"Name (Type). "` section header, and emitted `type_id`. 14/14 byte-perfect parity vs. legacy `POISON_DESCRIPTIONS`. Listed here for history. |
| ~~`src/srd_builder/extraction/reference_data.py`~~ | **DELETED v0.26.0** | (was `REFERENCE_TABLES` lookup) | — | Removed in v0.26.0; −625 net lines. Listed here for history. |
| [src/srd_builder/assemble/equipment_extended.py](src/srd_builder/assemble/equipment_extended.py) | **LIVE** — `assemble_equipment.py:1081` | 9 items "referenced in equipment packs (8) or monster stat blocks (1) but not in SRD equipment tables" with *inferred* costs/weights (or placeholder cost for natural_armor) | "Estimated costs/weights based on similar items to maintain referential integrity" | These items are **not in the SRD** at all — they are author-invented to keep equipment-pack and monster cross-references resolvable. Legitimate augmentation. Each record carries a typed `_provenance` block (`{source, reason, referenced_by, module, estimates}`) since v0.27.7, pinned by `ExtendedProvenance` TypedDict + `equipment.schema.json` 2.2.0 `_provenance` property + [tests/test_equipment_extended_provenance.py](tests/test_equipment_extended_provenance.py). |
| ~~[src/srd_builder/assemble/equipment_packs.py](src/srd_builder/assemble/equipment_packs.py)~~ | **DELETED v0.27.5 P6** | (was 7 equipment packs with item-by-item contents — item_id, quantity — plus costs and prose, 323 lines) | "Extracted from SRD 5.1 page 70" — actually transcribed into a Python literal; **DISPROVEN** (page 70 prose fully extractable). Replaced by [src/srd_builder/extract/datasets/extract_equipment_packs.py](src/srd_builder/extract/datasets/extract_equipment_packs.py). 7-for-7 byte-perfect parity (name, cost_gp, description, contents item_id + quantity) vs. retired literal. Pinned by [tests/test_pdf_provenance.py](tests/test_pdf_provenance.py) `test_equipment_packs_pdf_page_70_*` (15 assertions) and [tests/test_equipment_packs.py](tests/test_equipment_packs.py) (11 tests including end-to-end integration). Listed here for history. |
| ~~[src/srd_builder/assemble/equipment_descriptions.py](src/srd_builder/assemble/equipment_descriptions.py)~~ | **DELETED v0.27.6 P7** | (was 4 hand-curated TypedDict lists: `ADVENTURE_GEAR_DESCRIPTIONS` (42 entries, pp. 66–68), `TOOLS_DESCRIPTIONS` (9 entries, pp. 70–71), `ARMOR_DESCRIPTIONS` (12 entries, p. 63), `LIFESTYLE_DESCRIPTIONS` (6 entries, p. 73). 69 entries / ~398 lines total) | "Documented in the SRD" — actually transcribed not extracted; **DISPROVEN** by v0.27.5 reproducer ([tests/test_pdf_provenance.py](tests/test_pdf_provenance.py) `test_equipment_descriptions_section_anchor_extractable[×4]` + `test_equipment_descriptions_item_signature_extractable[×13]`). Replaced by [src/srd_builder/extract/datasets/extract_equipment_descriptions.py](src/srd_builder/extract/datasets/extract_equipment_descriptions.py) — section-aware concatenation + Title-Case heading regex with lowercase-glue alternation + 69-entry `_HEADING_TO_ITEM_ID` dispatch + subsection-terminator slicing + soft-hyphen / curly-apostrophe / page-footer / em-dash normalization. 69-for-69 recovery; surfaced 6 silently-stripped description phrases and 2 incorrect curated `page` fields (`item:antitoxin-vial`, `item:arcane-focus` are p. 66, not p. 67). Pinned by [tests/test_extract_equipment_descriptions.py](tests/test_extract_equipment_descriptions.py) (73 assertions, 69 of which are parametrized per-item snapshots). `assemble_equipment_from_tables` now takes an `equipment_descriptions=` kwarg; `build.py` calls `extract_equipment_descriptions()` once via the `_extract_equipment_pdf_data` helper that also wraps the v0.27.5 packs extractor. Listed here for history. |
| [src/srd_builder/extract/datasets/extract_equipment.py](src/srd_builder/extract/datasets/extract_equipment.py) (lines 30–35) | **FIXED v0.27.4** | (was `EQUIPMENT_START_PAGE = 61`, `EQUIPMENT_END_PAGE = 72` — 0-indexed; end-1 silently dropped PDF page 74) | Harmonized to 1-indexed `62`–`74` matching `PAGE_INDEX["equipment"]`. Pinned by [tests/test_pdf_provenance.py::test_extractor_page_constants_agree_with_page_index](tests/test_pdf_provenance.py) (parametrized across all 4 extractors). | Listed here for history. |

### Spectrum of legitimate exceptions vs. pollution

The user noted there's a spectrum between "pure source" and "useful augmentation."
Captured here as a mental model for the proposed `reason_code` enum:

- **Pure extracted** — bytes in PDF → record in JSON. Default; no `_provenance`.
- **`pdf_corruption`** — PDF bytes exist but unreadable (poisons pp. 204–205).
  *Permanent exception until upstream fix.* Reproducer test required.
- **`pdf_missing`** — concept exists in SRD prose but no structured source
  (some equipment_descriptions, possibly some traits).
  *Permanent exception, transcription faithful to prose.*
- **`cross_reference_glue`** — author-invented to keep refs resolvable
  (EXTENDED_EQUIPMENT items not in any SRD table).
  *Justified augmentation; must be flagged in record + meta.json.*
- **`derived_lookup_table`** — calculated from game rules, not extracted
  (spell-slots-by-level if it were live).
  *Justified; should live in rules dataset, not equipment/spell datasets.*
- **`alias` / `common_name`** — user-mentioned future case. Layer on top
  without overwriting source field. *Augmentation, not exception.*
- **`homebrew_overlay`** — user's future vision: independent dataset that
  augments srd_5_1 via the same `_provenance` mechanism.
  *Out of scope for v0.26.0; informs the design now.*

Anything that doesn't fit these codes is data pollution from earlier rounds
where extraction was bypassed for convenience. The v0.26.0 audit must
distinguish the two.

### Proposed provenance process

1. **Per-deviation declaration file** — `docs/PROVENANCE.md` (new) listing
   every hand-curated source above, with required fields:
   - `path`, `scope`, `reason_code` (enum: `pdf_corruption`, `pdf_missing`,
     `cross_reference_glue`, `derived_lookup_table`),
   - `pdf_pages`, `last_verified_date`, `reproducer` (one-line shell command
     or test that demonstrates why extraction fails),
   - `downstream_datasets` (which `dist/srd_5_1/*.json` files this data
     ends up in).

2. **Provenance metadata in records** — add an optional `_provenance` block
   to schemas for records that come from non-PDF sources. E.g., the 12
   inferred items in `EXTENDED_EQUIPMENT` should emit
   `"_provenance": {"source": "inferred", "reason": "pack_cross_reference", "module": "equipment_extended.py"}`
   so consumers can filter or flag them in UIs.

3. **`meta.json` surfacing** — every build emits a `provenance` block
   listing record counts by source: `{"pdf_extracted": 1685, "manually_transcribed": 12, "inferred": 12}` per dataset.
   Today this distinction is invisible to downstream consumers.

4. **Reproducer tests** — for each `reason_code = pdf_corruption` entry,
   a test that opens the PDF, calls the named extraction code, and asserts
   the output is in fact corrupted (mojibake regex, byte-count anomaly, etc.).
   If a future PyMuPDF or PDF revision *fixes* the corruption, the test fails
   loudly — that's the signal to delete the manual override.

5. **PR template gate** — any change touching files in the inventory must
   tick a checkbox: "I have updated `docs/PROVENANCE.md` and bumped
   `last_verified_date`."

6. **Audit code** — new `audit_dataset_quality.py` check
   `unverified_provenance`: scan source for `Final[list[dict]]` or
   `: list[...] = [` literals in `src/srd_builder/` and require each one
   to appear in `PROVENANCE.md`. Catches new hand-curated data added
   without registration.

### Smaller follow-ups uncovered while looking at this
- ~~`EXTENDED_EQUIPMENT` items currently emit `_note` (free text). Promote to
  structured `_provenance` block per (2) above.~~ **DONE in v0.27.7** —
  `ExtendedProvenance` TypedDict + `equipment.schema.json` 2.2.0
  `_provenance` property, pinned by
  [tests/test_equipment_extended_provenance.py](tests/test_equipment_extended_provenance.py).
- `equipment_extended.py` / `equipment_packs.py` originally contained
  hyphenated IDs (`item:foo-bar`). Fixed in v0.25.0 via regex sweep — but
  the underlying risk (hand-edited IDs drifting from the canonical
  generator in `postprocess/ids.py`) is the real lesson. Should not be
  possible at all: pack contents should reference items by `simple_name`
  and have IDs synthesized at assembly time.
- ~~`extract_equipment.py` `EQUIPMENT_START_PAGE` / `_END_PAGE` constants
  should be replaced with TOC lookup once `verify_pdf_sections.py` lands.~~
  **DONE in v0.27.4** — the SRD PDF's `Document.get_toc()` only exposes
  two file-level entries (no section anchors), so the TOC-lookup angle
  was a dead end. Instead, constants are now pinned to
  `PAGE_INDEX["equipment"]` via the parametrized
  `test_extractor_page_constants_agree_with_page_index` audit, which
  covers all four per-dataset extractors. Future drift fails CI.
- **`docs/templates/` is incomplete and hand-maintained.** Only 5
  templates exist (equipment, lineage, monster, spell, table) vs. 16
  schemas in `schemas/`. The header comment says they're for "extraction
  scripts" but they're really homebrew authoring exemplars. Two issues:
  (a) they duplicate information already in the schemas, drifting silently
  (e.g. spell template still says `v1.3.0`); (b) the missing 11 templates
  mean homebrew authors have no exemplar for ability_score, class,
  condition, damage_type, disease, features, magic_item, poison, rule,
  skill, weapon_property. **Fix: generate templates from schemas at build
  time** (`scripts/generate_templates.py`), drop the hand-written
  versions, ship the generated set in the bundle next to `schemas/`.
  Single source of truth = schema; template is a derived view.
  - **Three-for-one win.** One generated exemplar per schema serves three
    independent needs at once: (1) homebrew authoring template; (2) the
    `tests/fixtures/known_truths.json` baseline mentioned under "Data
    integrity / extraction confidence" above — exemplars *are* the known
    patterns; (3) schema smoke test — every schema must round-trip
    through its own exemplar via `jsonschema.validate`. Build once,
    consume thrice. Plan v0.26.0 work so these three threads land
    together, not separately.

### Re-extraction candidates (remove the crutch, don't just declare it)

> **✅ ALL DONE.** All three candidates below shipped during v0.27.x:
> `spell_class_targets.py` retired v0.27.0 P2 (778-for-778 byte-perfect
> parity); `class_targets.py` retired v0.27.2 P3 (5-step pipeline, 240
> rows × 12 classes); `lineage_targets.py` retired v0.27.0 P1
> (font-fingerprint walk). Section retained for history.

Some hand-curated sources may exist because *earlier* extraction tooling
couldn't handle them, not because the PDF is genuinely unreadable. With
the newer PyMuPDF capabilities (font/coord-aware extraction, table-rect
detection) it's worth re-attempting extraction and retiring the manual
data wherever it succeeds.

- **`spell_class_targets.py` (pp. 105–113 spell lists)** — comment says
  "PDF text is corrupted." Verify with a focused reproducer:
  1. `fitz.Document.load_page(104..112).get_text("dict")` and inspect.
  2. If text is genuinely mojibake → keep manual + write reproducer test.
  3. If text is fine but layout-driven (multi-column lists per class)
     → write a real parser. Layout-driven extraction is what tripped up
     equipment originally; same fix pattern likely applies here.
- **`class_targets.py` features list** — features have known section
  headers and a stable font fingerprint (`GillSans-SemiBold 13.9pt`,
  per Phase D research). The feature *names* should be extractable; only
  the class→feature *grouping* needs verification against the PDF cursor
  walk we already do in `parse_features._resolve_owners()`.
- **`lineage_targets.py`** — same question as classes. The traits text is
  already extracted into `features.json` (lineage-owned features); the
  *table* fields (ability_modifiers, size, speed) may be extractable from
  the "Racial Traits" sidebar layout.

Process: for each candidate, the verification is cheap (one notebook
or scratch script per file). Outcome is either (a) retire the manual
source, or (b) upgrade its declaration from vague "PDF corrupted" to a
specific reproducer-backed exception. Either result is a win.

## Structural cleanup (proposed v0.26.2)

> **✅ SHIPPED in v0.26.2** (commit `22ad820`, tag `v0.26.2`). All
> Phase A–F items below landed. See
> [docs/releases/v0.26.2.md](releases/v0.26.2.md) for the consolidated
> change list. The text below is retained as historical context for
> what "attempt #3" set out to do; not a forward-looking ticket.

Discovered while auditing the extraction layer for the v0.26.1 spell-class
probe. None of these are bugs; all are organizational debt that makes the
codebase harder to navigate and extend. **Defer until after v0.26.1 ships
so the probe work doesn't get tangled with rename noise.**

### Important framing: this is attempt #3 at standardization

Two prior efforts at "configurable input model → shared parser engine"
left artifacts in the codebase:

- **Attempt 1** — false start, scrubbed before producing live code. Some
  schema design choices (the 2.0.0 versioning round) carry its
  fingerprints, but no live source code remains.
- **Attempt 2** — produced the surviving `src/srd_builder/extraction/`
  table engine (`extractor.py` + `patterns.py` + `extraction_metadata.py`)
  and the postprocess engine (`postprocess/engine.py` + `configs.py`).
  Real, working, but only finished for *tables* and *record cleanup*. The
  per-dataset body extractors (`extract/extract_*.py`) never made the
  jump.
- **Attempt 3** — **this is what v0.26.2 + v0.27.0 are.** The
  `utils/pdf_probe.py` shared primitive (landed v0.26.1) is the first
  rail. The structural moves below consolidate the existing artifacts
  rather than design a new system from scratch.

> **Operational consequence.** v0.26.2 is *not* greenfield. The job is
> to finish what attempt #2 started: get the existing engine patterns
> consistently named and wired, and move every per-dataset body
> extractor onto them as feature work allows. The risk this attempt
> repeats the prior pattern is real \u2014 capturing it here so the scope
> stays bounded and we ship the consolidation, not a fresh redesign.

### Naming inconsistency: `extract/` vs `extraction/`

> **PARTIALLY SHIPPED v0.26.2; superseded by `## Active: Extractor
> consolidation (attempt #4)` above.** Step 1 of the cutover (rename
> `extraction/` → `extract/`) shipped. Steps 2–4 (`_legacy/` directory,
> deprecation notes, forced migration of bespoke extractors) **did NOT
> ship and should not**. The bespoke extractors in `extract/datasets/`
> are LIVE, not legacy — five new ones were added there during v0.27.x
> retirement work. The replacement plan is the attempt #4 framing above:
> gradual migration to the existing 7-pattern-type engine, one extractor
> per release, with new pattern types added as needed. Original text
> retained below for history.

Two sibling directories at the same pipeline layer with confusingly similar
names, doing different shapes of the same job:

- `src/srd_builder/extract/` — 9 bespoke per-dataset extractors
  (`extract_spells.py`, `extract_equipment.py`, etc.). Each opens the PDF
  directly with `fitz.open()`, hardcodes its own page constants, and picks
  its own text-extraction mode.
- `src/srd_builder/extraction/` — generic config-driven table-extraction
  engine (`extractor.py` + `patterns.py` + `extraction_metadata.py`). The
  mature pattern: metadata-driven, one engine per `pattern_type`.

Neither is "raw" vs. "cleaned" — both are PDF→raw structures. The split
is *shape of work* (per-dataset module vs. config-driven engine), not
pipeline phase.

**Proposed cutover (v0.26.2, one commit per move):**

1. Rename `extraction/` → `extract/` (the generic engine becomes the
   primary `extract/` namespace).
2. Move existing `extract/extract_*.py` → `extract/_legacy/` (or
   `extract/datasets/`) with a deprecation note in each file's docstring.
3. New extractors (e.g., `extract_lineages.py`, `extract_spell_classes.py`)
   land directly under `extract/` using the engine pattern.
4. Migrate the legacy bespoke extractors to the engine pattern one
   dataset at a time as opportunity arises (during normal feature work,
   not as a forced refactor).

### Misplaced data and config files

> **OUTCOME (2026-06-19 audit).** Most rows of the original 7-home table
> below are now resolved by v0.27.x retirements:
>
> - `CLASS_DATA`, `LINEAGE_DATA`, `SPELL_CLASSES` — modules **DELETED**
>   (extracted live in v0.27.0–v0.27.2).
> - `poison_descriptions_manual.py` — **DELETED** (v0.27.3).
> - `EQUIPMENT_PACKS`, `EQUIPMENT_DESCRIPTIONS` — **DELETED**
>   (v0.27.5–v0.27.6).
> - `EXTENDED_EQUIPMENT` — still in `assemble/equipment_extended.py`,
>   now carries typed `_provenance` (v0.27.7) and is the single
>   remaining LIVE PROVENANCE entry. Documented, not misplaced.
> - `TARGET_TABLES` — moved from `scripts/` to `extract/table_targets.py`
>   in v0.26.2 (correct location: engine config alongside engine).
> - `DATASET_CONFIGS`, `PATTERN_TYPES`, `PAGE_INDEX` — unchanged,
>   correct locations.
>
> The per-ruleset directory layout proposal (`rulesets/<id>/data/` +
> `rulesets/<id>/config/`) did **NOT** ship. Not needed yet: there is
> only one ruleset. When SRD 5.2.1 lands, revisit — but the audit above
> shows the actual data has consolidated, so the per-ruleset split may
> be smaller than originally feared. Original 7-home framing retained
> below for history.

Hand-curated data and engine config are scattered across **five**
different homes with no organizing principle:

| What | Currently lives at | Type |
| --- | --- | --- |
| `DATASET_CONFIGS` | `postprocess/configs.py` | engine config |
| `PATTERN_TYPES` + table metadata | `extraction/extraction_metadata.py` | engine config |
| `TARGET_TABLES` (16 tables) | `scripts/table_targets.py` | engine config (**wrong place** — `scripts/` is for CLIs) |
| `PAGE_INDEX` | `utils/page_index.py` | ruleset config |
| `CLASS_DATA`, `LINEAGE_DATA`, `SPELL_CLASSES` | `srd_5_1/*.py` | ruleset data |
| Manual poison descriptions | `data/poison_descriptions_manual.py` | ruleset data (single-file orphan) |
| Equipment packs / descriptions / extended | `assemble/equipment_*.py` | ruleset data (mixed in with assembly code) |

**Proposed target shape:**

```
src/srd_builder/
  extract/        # engine + per-dataset extractors (post-rename)
  parse/
  postprocess/
  assemble/
  utils/
  build.py
rulesets/
  srd_5_1/
    SRD_CC_v5.1.pdf
    raw/          # extraction working dir (already exists)
    data/         # class_data.json, lineage_data.json, spell_classes.json,
                  # poison_descriptions.json, equipment_packs.json,
                  # equipment_descriptions.json, equipment_extended.json
    config/       # page_index.yaml, target_tables.yaml,
                  # extraction_metadata.yaml, dataset_configs.yaml
  srd_5_2_1/
    ...
```

Engine code is then *ruleset-agnostic* — `srd_builder/` contains zero
ruleset-specific data. Adding SRD 5.2.1 / Pathfinder / homebrew rulesets
becomes purely a `rulesets/` sibling directory, not a `srd_builder/` fork.

### Why defer

- v0.26.1 (now) ships actionable user value (spell-class probe + shared
  PDF probe utility) without polluting commits with renames.
- Each item above can land in its own commit during v0.26.2, reviewable
  in isolation, with test suite green between each move.
- The ruleset-data move is a strict additive then a strict removal — no
  ambiguity, no behavior change, easy to verify.

### Hardcoded values / config-vs-constant inventory

`src/srd_builder/constants.py` is small (3 values) but each value has a
different real lifetime, which the file currently hides:

| Symbol | Real meaning | Right home |
| --- | --- | --- |
| `EXTRACTOR_VERSION = "0.4.0"` | Fingerprint of how *we* extract — describes raw output format | **Stays global.** Belongs next to whatever code it fingerprints (likely under `extract/` after the rename). |
| `DATA_SOURCE = "SRD_CC_v5.1"` | Identifies the source PDF and SRD edition | **Per-ruleset.** Becomes wrong the moment SRD 5.2.1 lands. Move to `rulesets/srd_5_1/config/source.yaml` (or similar). |
| `RULESETS_DIRNAME = "rulesets"` | The string "rulesets" | Either deletes (just inline the string) or moves alongside whatever defines what a ruleset *is*. |

The same shape exists for the **dist directory** (verified):

- `build.py:537` — `default="dist"` for the CLI `--target`
- `utils/validate.py:15` — `DIST_DIR = Path(...) / "dist"` module-level

`dist/` is structurally identical to `rulesets/` — a top-level workspace
directory. Treat it the same way.

> Broader audit: while doing v0.26.2, sweep `src/srd_builder/` for
> remaining magic strings and hardcoded paths and decide for each one
> whether it is (a) a true constant that belongs alongside the code it
> describes, (b) per-ruleset config that belongs in
> `rulesets/<ruleset>/config/`, or (c) a workspace-shape constant
> (like `dist/`, `rulesets/`) that probably belongs in a single
> `paths.py` module or — better — a `pyproject.toml`-driven settings
> object.

#### Resolution rule (avoid over-engineering)

The instinct to "fix" `constants.py` by inventing a multi-layer settings
system (env vars → user file → ruleset file → defaults) makes things
*less* visible, not more. The current `constants.py` is a useful
**visible debt counter** — three lines that tell you "these three values
matter and aren't yet properly homed."

Rule for v0.26.2: **a value graduates from `constants.py` only when it
has a real reason to live somewhere else, driven by a real use case.**

| Value | Action | Why |
| --- | --- | --- |
| `EXTRACTOR_VERSION` | Keep in `constants.py` | True constant, no second value coming |
| `DATA_SOURCE` | Move to `rulesets/srd_5_1/config/` | Forced by SRD 5.2.1 needing a different value |
| `RULESETS_DIRNAME` | Keep in `constants.py` | Workspace fact, no per-ruleset variant |
| `"dist"` (currently scattered in 2 files) | **Move INTO `constants.py`** as `DIST_DIRNAME` | Workspace fact, surface it for visibility |
| Other magic strings (`"raw"`, etc.) | Sweep into `constants.py` if workspace-level | Same reason |

End state: `constants.py` is *more* populated than today, not less.
Only genuinely per-ruleset values graduate to the per-ruleset config dir.
Boring, visible, easy to grep — beats clever every time.

### Configuration UX (must not get lost)

The proposed multi-ruleset structure is technically right but creates
a real risk: the user wants to set a couple of values and run the
engine; we must not force them to edit YAML files spread across three
directories.

**Constraint for v0.26.2 / v0.27.0 implementation:**

- Default behavior with zero config edits: `make build` against the
  default ruleset (`srd_5_1`) just works.
- Per-ruleset config files exist for *us* (the engine maintainers) to
  declare facts about the source — page indexes, edition strings,
  source filenames. They should not be where users put their
  preferences.
- User-level overrides (output dir, ruleset selection, schema strict
  mode, etc.) belong on the CLI / Make target / a single root-level
  config file the user can edit, not buried per-ruleset.
- The split is: **engine config** (per-ruleset, declarative facts about
  the source — checked in) vs. **user settings** (per-invocation,
  preferences — flags or one settings file). Keep these separate or
  the simplicity-of-use goal evaporates.

If we can't articulate "to add SRD 5.2.1, copy `rulesets/srd_5_1/` to
`rulesets/srd_5_2_1/`, edit two files, run `make build RULESET=srd_5_2_1`"
in one paragraph, the design isn't done.

### Duplication signal (consolidate during the move, don't migrate twice)

Two pairs of modules that look like the same job done twice — flagged
during v0.26.2 planning so the relocation pass would pick a better
implementation rather than moving both.

- **Cross-reference index building — AUDITED v0.26.2 Phase B, no
  consolidation needed:**
  - `src/srd_builder/utils/validate_references.py` (`ReferenceValidator`)
    performs build-time **integrity checks** — raises errors when one
    entity references an ID that doesn't exist (broken `damage_type_id`,
    missing `spell_id`, etc.). Output: pass/fail + error list.
  - `src/srd_builder/assemble/indexer.py::build_cross_reference_indexes`
    builds the **public lookup tables shipped in the bundle**
    (`spells_by_damage_type`, `monsters_immune_to_condition`,
    `magic_items_by_granted_spell`, etc.) for downstream consumers.
    Output: structured dict that becomes part of the dataset.
  - The only overlap is the one-line idiom
    `{x["id"] for x in xs if "id" in x}` (validator builds 8 sets
    eagerly from the bundle structure; indexer builds 4 inline from
    pre-extracted lists, using `fallback_id()` instead of `["id"]`).
    Extracting a shared helper would *add* indirection rather than
    remove duplication. **Decision:** keep both, distinct purposes.
- **Validation utilities — RESOLVED v0.26.2 Phase A:**
  - `utils/validate.py`, `utils/validate_monsters.py` — schema-level
    validation (always lived under `utils/`).
  - `validate_references.py` — moved into `utils/` alongside them
    (commit `e7e3331`). Different but related job: schema validators
    check shape, reference validator checks ID existence. Co-located
    is enough.

### Constraint while v0.26.1 is in flight

> Do not extend the technical debt in the old code.

New code added in v0.26.1 (the `pdf_probe.py` utility) lives under
`utils/` rather than the about-to-be-renamed `extract/`, and consumes
`PAGE_INDEX` rather than introducing new hardcoded page constants. New
test code uses `pdf_probe` rather than inline whitespace helpers. This
keeps the v0.26.2 cutover small.

## Pre-v1.0 code-health audit

Before locking v1.0 and starting SRD 5.2.1, do a single full-repo pass
focused on *removal* and *standards*, not new features. Goal: the leanest
codebase that can produce the bundle.

### Scope
- **Dead code** — modules with no importers in `src/srd_builder/`
  (`reference_data.py` already identified). Use `vulture` or grep on each
  top-level symbol to enumerate; delete or move to `archive/code/`.
- **Cruft accumulation** —
  - `archive/dist_versions/` retention policy (keep last N? keep tagged
    only?). Currently grows unbounded.
  - `scripts/archive/` — same question.
  - `docs/archive/`, `docs/planning/` — confirm nothing still actively
    referenced from live docs.
  - `*.json` artifacts at repo root (`build_output.txt`, `tables.json`,
    `tables_raw.json`, `table_metadata.json`, `discovery_report.json`) —
    are these generated, checked-in by mistake, or intentional? Move to
    `dist/` or `.gitignore` as appropriate.
- **Module boundary leaks** — `parse/` modules should not do I/O;
  `postprocess/` should be pure; `assemble/` should not parse. Verify
  with a grep for `open(` / `Path(...).read_*` / `json.load(` inside
  `parse/` and `postprocess/`. Each violation is a real bug or a
  refactor candidate.
- **Standards pass** —
  - All new code uses `from __future__ import annotations`? Consistent?
  - Type-hint coverage — run `mypy --strict` once and see how bad it is.
  - Docstring style — pick one (Google / NumPy / plain) and apply.
  - No bare `except:`; no `print()` outside CLI entry points; no
    `# type: ignore` without explanation.
- **Test surface** —
  - Tests skipped (19 today) — each one needs a reason or removal.
  - Tests marked `xfail` — same.
  - Golden tests: confirm every dataset has one and every golden uses
    real fixtures, not inline literals.
- **Dependencies** — `pyproject.toml` audit: anything in `[dev]` or
  `[project.dependencies]` that's no longer imported?
- **Schema hygiene** — every schema in `schemas/` should have at least
  one record in `dist/` that validates against it; orphan schemas
  (no producer) should be deleted.
- **Doc consolidation** — `docs/` has grown to ~10 active files plus
  archive. A v1.0 doc structure should be: README, ARCHITECTURE,
  CONTRIBUTING, PROVENANCE, SCHEMAS, CHANGELOG. Everything else either
  consolidates in or archives out.

### Output
A single `docs/PRE_V1_AUDIT.md` checklist (created during the work,
not before) with measured findings. Each finding → ticket → fix or
intentional defer. Land all fixes in one or two release waves, then cut
v1.0.

### Why now (before SRD 5.2.1)
Every line of cruft we carry into the multi-ruleset era doubles in cost.
SRD 5.2.1 will be the first real test of the ruleset abstraction —
anything sloppy in `src/srd_builder/srd_5_1/` will get copy-pasted into
`src/srd_builder/srd_5_2_1/`. Audit *before* the copy.

## Notes
- Items here are *aspirational*, not blockers for the Blackmoor bundle.
- Add to this list freely; promote to a release plan (`docs/V0.x.0_PLAN.md`)
  when scheduling work.
