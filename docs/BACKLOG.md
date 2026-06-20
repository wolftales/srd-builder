# Backlog

Active and planned work only. Shipped work lives in [ROADMAP.md](ROADMAP.md)
(per-version summaries) and git history (per-commit detail). Drain this
list; do not let it accumulate history.

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
| Modern (full `pdf_probe`) | `extract_equipment_descriptions.py`, `extract_equipment_packs.py`, `extract_pdf_metadata.py`, `extract_rules.py`, `extract_equipment.py` | ✅ `open_pdf` + `page_text` / `page_dict` (lifecycle managed; `find_tables` calls still ride on managed pages) | v0.27.5–v0.27.6, v0.31.0, v0.32.0, v0.33.0 |
| Mixed | `extract_lineages.py`, `extract_classes.py`, `extract_spell_classes.py` | ⚠️ `normalize_whitespace` only; still raw `fitz.open()` | v0.27.0–v0.27.2 |
| `ProseExtractor` framework | `extract_conditions.py` | ✅ (via `utils.prose`) | Higher abstraction |
| Pre-`pdf_probe` (legacy) | `extract_magic_items.py`, `extract_features.py`, `extract_monsters.py`, `extract_spells.py` | ❌ raw `fitz.open()` | **4 files violating AGENTS.md rule** |

All 4 raw-`fitz` files legitimately extract from PDF (walk pages, produce
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

**Suggested order (cheapest → hardest):** ~~`extract_pdf_metadata.py`~~
(✅ shipped v0.31.0 — pdf_probe migration only; doc-level metadata
shape does not fit the table-shaped engine, kept as a slim pdf_probe
consumer) → ~~`extract_rules.py`~~ (✅ shipped v0.32.0 — pdf_probe
migration only; emits font-stamped span blocks for downstream parser
consumption, not a `RawTable`, so engine binding deferred. Added
`pdf_probe.page_dict()` helper as the shared primitive for any future
extractor that needs font/bbox metadata) → ~~`extract_equipment.py`~~
(✅ shipped v0.33.0 — pdf_probe lifecycle migration only; existing
engine `pattern_type`s don't model the font-anchored section tracking
required here, deferred until 1–2 more table extractors land and a
shared `font_anchored_table_walk` pattern is obvious) →
`extract_magic_items.py` → `extract_features.py` → `extract_spells.py` →
`extract_monsters.py` (largest, most unique shape, do last).

### Parse-layer consolidation (forward-looking)

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

## Active: Data integrity follow-ups

The v0.28.0 four-phase release (exemplar generator, `known_truths.json`
release gate, three audit codes, round-trip PDF sampling) closed the
biggest items. These remain:

- **Independent reference cross-check** — spot-check ~10 items per
  dataset against an independent SRD source (Open5e API, D&D Beyond
  machine-readable dumps) to detect single-source bias. Treat
  mismatches as findings, not failures — they often surface ambiguity
  in the SRD itself.
- **Font-fingerprint regression** — record the font + size we treat as
  feature/section headers (today: `GillSans-SemiBold 13.9pt`). A test
  that re-extracts and asserts the fingerprint is unchanged catches
  silent upstream PDF or library updates.
- **`unknown_word` audit code** — run `pyspellchecker` over **item
  names only** (not body text — too many fantasy terms) with an
  extended dictionary that loads in all class / monster / spell / item
  names. Output for human review, not automated failure.

> The `verify_pdf_sections.py` / `meta.json` TOC ideas captured in the
> original v0.28.0 plan were proven dead-ends in v0.27.4 — the SRD PDF's
> `Document.get_toc()` only exposes two file-level entries with no
> section anchors, so `PAGE_INDEX` is the canonical source of truth.

---

## Active: Provenance follow-ups

[PROVENANCE.md](PROVENANCE.md) registry exists, `_provenance` blocks
exist on the one remaining hand-curated source
(`assemble/equipment_extended.py`, pinned by
[tests/test_equipment_extended_provenance.py](../tests/test_equipment_extended_provenance.py)),
and the reproducer-test framework in
[tests/test_pdf_provenance.py](../tests/test_pdf_provenance.py) is the
gate for "PDF corruption" claims. These items remain:

- **`meta.json` provenance summary** — emit a per-dataset `provenance`
  block listing record counts by source:
  `{"pdf_extracted": 1685, "manually_transcribed": 0, "inferred": 12}`.
  Today this distinction is invisible to downstream consumers.
- **`unverified_provenance` audit code** — scan source for
  `Final[list[dict]]` or `: list[...] = [` literals in
  `src/srd_builder/` and require each one to appear in `PROVENANCE.md`.
  Catches new hand-curated data added without registration.
- **PR template gate** — any change touching files in the provenance
  inventory must tick a checkbox: "I have updated `docs/PROVENANCE.md`
  and bumped `last_verified_date`."
- **Generate `docs/templates/` from schemas** — current state: 5 of 16
  templates exist (equipment, lineage, monster, spell, table),
  hand-maintained, drift silently from schemas (spell template still
  says `v1.3.0`). Fix: `scripts/generate_templates.py` at build time,
  ship the generated set in the bundle next to `schemas/`. Three-for-one
  win: homebrew authoring template + `known_truths` exemplar baseline +
  per-schema round-trip smoke test.
- **`EXTENDED_EQUIPMENT` ID synthesis** — pack contents currently
  reference items by hard-coded `item:foo-bar` IDs. The architectural
  risk (hand-edited IDs drifting from `postprocess/ids.py`) was fixed
  in v0.25.0 by regex sweep but should not be possible at all: pack
  contents should reference items by `simple_name` and have IDs
  synthesized at assembly time.

---

## Active: Process / tooling

- **Automate the macOS `chflags -R nohidden .venv` workaround** — bake
  it into the `Makefile` `bundle` target so a fresh contributor doesn't
  hit the UF_HIDDEN pip bug.
- **Convert hand-curated `EXPECTED_COUNTS`** in
  [tests/test_dataset_completeness.py](../tests/test_dataset_completeness.py)
  into a generated `expected_counts.json` derived from PDF section
  page-count math, so it self-updates when the source PDF revises.

---

## Planned: Pre-v1.0 code-health audit

Before locking v1.0 and starting SRD 5.2.1, do a single full-repo pass
focused on *removal* and *standards*, not new features. Goal: the
leanest codebase that can produce the bundle.

### Scope

- **Dead code** — modules with no importers in `src/srd_builder/`. Use
  `vulture` or grep on each top-level symbol to enumerate; delete or
  move to `archive/code/`.
- **Cruft accumulation** —
  - `archive/dist_versions/` retention policy (keep last N? keep
    tagged only?). Currently grows unbounded.
  - `scripts/archive/` — same question.
  - `docs/archive/`, `docs/planning/` — confirm nothing still actively
    referenced from live docs.
  - `*.json` artifacts at repo root (`build_output.txt`, `tables.json`,
    `tables_raw.json`, `table_metadata.json`, `discovery_report.json`)
    — are these generated, checked-in by mistake, or intentional? Move
    to `dist/` or `.gitignore` as appropriate.
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
  - Tests skipped (~19 today) — each one needs a reason or removal.
  - Tests marked `xfail` — same.
  - Golden tests: confirm every dataset has one and every golden uses
    real fixtures, not inline literals.
- **Dependencies** — `pyproject.toml` audit: anything in `[dev]` or
  `[project.dependencies]` that's no longer imported?
- **Schema hygiene** — every schema in `schemas/` should have at least
  one record in `dist/` that validates against it; orphan schemas (no
  producer) should be deleted.
- **Doc consolidation** — `docs/` has grown to ~10 active files plus
  archive. A v1.0 doc structure should be: README, ARCHITECTURE,
  CONTRIBUTING, PROVENANCE, SCHEMAS, CHANGELOG. Everything else either
  consolidates in or archives out.

### Output

A single `docs/PRE_V1_AUDIT.md` checklist (created during the work,
not before) with measured findings. Each finding → ticket → fix or
intentional defer. Land all fixes in one or two release waves, then
cut v1.0.

### Why now (before SRD 5.2.1)

Every line of cruft we carry into the multi-ruleset era doubles in
cost. SRD 5.2.1 will be the first real test of the ruleset abstraction
— anything sloppy in `src/srd_builder/srd_5_1/` will get copy-pasted
into `src/srd_builder/srd_5_2_1/`. Audit *before* the copy.

---

## Notes

- Items here are *aspirational*, not blockers for any specific
  consumer.
- Add to this list freely; promote to a release plan (e.g.
  `docs/V0.x.0_PLAN.md`) when scheduling work.
- When an item ships, **remove it from this file** — its history
  belongs in [ROADMAP.md](ROADMAP.md) and the commit log, not here.
