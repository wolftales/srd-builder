# Backlog

Active and planned work only. Shipped work lives in [ROADMAP.md](ROADMAP.md)
(per-version summaries) and git history (per-commit detail). Drain this
list; do not let it accumulate history.

---

## Active: Extractor consolidation (attempt #4)

> **Status (2026-06-22).** 3/13 bound — `extract_features` and
> `extract_magic_items` on `font_fingerprint_walk`; `extract_spells`
> on `font_stateful_walk`. The other 10 are bespoke by deliberate
> choice. Full narrative of work landed (3 bindings, 3-phase
> architecture refactor, 11-commit primitive-lift continuation,
> font-fingerprint regression test, `unknown_word` audit code):
> [ROADMAP.md](ROADMAP.md) § "post-v0.37.0".

### End state (the goal)

[extract/datasets/](../src/srd_builder/extract/datasets/) becomes the
**pattern registry** — one file per dataset, declarative, easy to
diff. The directory having 13–20 files is a *feature*, not a smell,
because each file is ~30–60 lines of config binding to
`extract_by_config()` / `extract_records_by_config()` rather than
~300–800 lines of bespoke PDF-walking logic. When SRD 5.2.1 lands as
a second ruleset, the per-dataset config changes (page numbers,
section headers, table targets, font fingerprints) but engine code
does not. If we cannot articulate that in one paragraph, the design
is not done.

### Open: 10 remaining extractors

Future bindings need their own design-pass entry, not a presumed
extension of the three already landed. The 2-caller threshold is the
gate — below it, bespoke is honest; above it, the pattern type pays
for itself.

- **`extract_monsters`** — bespoke by deliberate choice. A
  `font_columnar_walk` pattern type would have one caller;
  `lookahead_validation` engine action ("confirm header X only if a
  span matching fingerprint Y appears within N points of Y-distance")
  is a 1-caller need and the binding cannot work without it. The
  bbox/column-aware primitives it does need are already lifted to
  [utils/pdf_layout.py](../src/srd_builder/utils/pdf_layout.py) so
  any future second caller starts at a much lower binding cost.
- **`extract_pdf_metadata`, `extract_rules`, `extract_equipment`,
  `extract_equipment_descriptions`, `extract_equipment_packs`,
  `extract_classes`, `extract_lineages`, `extract_spell_classes`,
  `extract_conditions`** — no claim here about whether they would
  benefit; they have not been inspected at the same depth as the
  three that bound.

### Open: chip-away-able structural targets

No clean 2+ caller shared primitives remain in the bespoke
extractors. These are *structural* per-extractor cleanups, single
caller today, kept here so a future session doesn't re-discover them:

- **`extract_classes`** (628 lines) — each phase still emits 4-tuples
  `(text, size, font, bbox)` hand-decoded inside helpers like
  `_extract_field_labels` and `_extract_progression`. Replace with a
  typed dataclass.
- **`extract_lineages._classify_span`** 5-way role dispatch
  generalises to the same shape as `extract_spell_classes`' inline
  predicate stack. A generic dispatcher returning role enums is
  possible; payoff is modest because each caller's branch logic is
  still bespoke.
- **`extract_rules._extract_page_text_blocks`** carries its own block /
  line / span walk that intentionally tracks `(block_idx, line_idx,
  span_idx)` for downstream provenance — information
  `iter_page_spans` discards. Could parameterise the iterator to
  optionally yield indices.

### Forward-looking: parse-layer consolidation

The same framework lesson should apply to
[parse/](../src/srd_builder/parse/): ~15 modules each doing
record-walking, prose-normalizing, id-synthesizing,
cross-reference-resolving in their own shape. Possible pattern types
for a parse engine: `record_walker`, `table_row_mapper`,
`prose_narrator_stripper`, `cross_reference_resolver`,
`schema_stamp_normalizer`, `id_synthesizer`.

Do NOT start parse consolidation until extract consolidation has
migrated at least 3–4 datasets and the pattern is proven. The hard
part is not the design; it is resisting "this one is different, I
will just write it bespoke" for every dataset.

### Bottom line

We do not want multiple different approaches to extracting and later
parsing SRD sections. One approach (config-driven engine + pattern
types). Treat every new bespoke file as a regression on that goal.

---

## Active: Data integrity follow-ups

- **Independent reference cross-check** — spot-check ~10 items per
  dataset against an independent SRD source (Open5e API, D&D Beyond
  machine-readable dumps) to detect single-source bias. Treat
  mismatches as findings, not failures — they often surface ambiguity
  in the SRD itself.

> Guard rail (do not re-investigate): the `verify_pdf_sections.py` /
> `meta.json` TOC ideas captured in the original v0.28.0 plan were
> proven dead-ends in v0.27.4 — the SRD PDF's `Document.get_toc()`
> only exposes two file-level entries with no section anchors, so
> `PAGE_INDEX` is the canonical source of truth.

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
