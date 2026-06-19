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
  positives. **FIXED 2026-06-19** in `postprocess/text.py`: same regex (with
  suspended-hyphen guard for `and`/`or`/`but`/`nor`) applied in both
  `clean_text()` and `polish_text()` after whitespace normalization. Covers
  all four affected datasets (spells via `clean_text`; features, monsters,
  rules via `polish_text`). Post-fix audit: 0 hyphenation findings. Residual:
  digit-letter line-stitching like `15- foot- radius` (now `15- foot-radius`)
  is not addressed by this fix; it's a smaller follow-up requiring a
  broader pattern that handles number-letter boundaries.
- ✅ `word_boundary_loss` — `\b[A-Za-z]{21,}\b` for run-on tokens
  (`fireballyou`). 0 findings on current dist (clean).
- ⏳ `unknown_word` — deferred. Needs `pyspellchecker` dep + extended
  dictionary built from all dataset names to avoid noise. Standalone task.

The 151 hyphenation findings are the next backlog item — fix the extractor's
line-stitching pass, not the audit. **✅ DONE 2026-06-19** — see fix note
on the `hyphenation_artifact` line above. Open follow-up: digit-letter
line-stitching (e.g. `15- foot- radius`) not covered by this pass.

### Phase D — Round-trip PDF sampling (independent, lower priority)

- New `tests/test_round_trip_pdf.py`: for each dataset, sample 5 records,
  look up their `page` field, render that page via
  `pdf_probe.get_page_text()`, assert the parsed `name` or `text` field
  appears as substring.
- Catches silent parser drift where extractor produces output not
  actually in the PDF.

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
