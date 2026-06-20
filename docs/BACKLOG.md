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

### Current state (audit 2026-06-20)

13 files in [extract/datasets/](../src/srd_builder/extract/datasets/),
all LIVE (12 imported by `build.py`; `extract_conditions` wired through
`parse_conditions` + tests). **Zero are bound to the engine.** Calling
`pdf_probe.open_pdf()` vs `fitz.open()` is a lifecycle convention; it
is NOT engine binding and does not move any extractor toward the slim
`DATASET_CONFIG + extract_by_config()` end state above.

#### Lifecycle convention (cosmetic)

| Uses `pdf_probe` for `open()` | Files |
| --- | --- |
| ✅ | `extract_pdf_metadata` (v0.31.0), `extract_rules` (v0.32.0), `extract_equipment` (v0.33.0), `extract_magic_items` (v0.34.0), `extract_features` (v0.35.0), `extract_spells` (v0.36.0), `extract_monsters` (v0.37.0), `extract_equipment_descriptions` (v0.27.6), `extract_equipment_packs` (v0.27.5) |
| ⚠️ raw `fitz.open()` but uses `normalize_whitespace` | `extract_lineages` (v0.27.0), `extract_classes` (v0.27.x), `extract_spell_classes` (v0.27.0) |
| ✅ via `utils.prose` framework | `extract_conditions` |

#### Engine binding (substantive — the actual goal)

| Bound to `extract_by_config()` | Files |
| --- | --- |
| ❌ | **all 13** |

The v0.31–v0.37 release series moved the lifecycle column for 7 files
and left the binding column unchanged. The v0.27.x retirements
(`class_targets`, `lineage_targets`, `spell_class_targets`,
`poison_descriptions`, `equipment_packs`, `equipment_descriptions`)
replaced hand-curated data with new bespoke extractors, also unbound.
**The engine has had zero new bindings since the original 7 pattern
types were built.**

#### Shape inventory (input to engine-binding design)

| Shape | Files | Engine fit |
| --- | --- | --- |
| Doc-level regex | `extract_pdf_metadata` | None — would need `document_metadata` pattern type |
| Font-stamped span dump | `extract_rules` | None — needs `font_span_section` pattern type |
| PyMuPDF `find_tables()` + section tracking | `extract_equipment` | Closest to `standard_grid` but needs font-anchored section state |
| Font-fingerprint walk over single-page items | `extract_magic_items`, `extract_features` | None — needs `font_fingerprint_walk` pattern type *(see design-pass finding below)* |
| Regex walk over pre-concatenated section text | `extract_equipment_descriptions` | Closer to `prose_section` than to the font-fingerprint walks above |
| Font-fingerprint walk + cross-page state | `extract_spells`, `extract_monsters` | Extension of font-fingerprint walk (not yet inspected in depth) |
| `normalize_whitespace`-only PDF read | `extract_lineages`, `extract_classes`, `extract_spell_classes` | Possibly `prose_section` with target-list config |
| Packs-config + ID synthesis | `extract_equipment_packs` | Possibly `reference` |
| `ProseExtractor` framework | `extract_conditions` | Already abstracted (different framework) |

### Design-pass finding (2026-06-20)

Read `extract_magic_items`, `extract_features`, and
`extract_equipment_descriptions` side-by-side. Earlier framing called
all three candidates for a shared `font_fingerprint_walk` pattern
type. Reality:

- **`extract_magic_items`** and **`extract_features`** share the
  font-fingerprint shape. Both iterate page → block → line → span,
  detect headers by font name + size (+ optional flags), close the
  current record on the next header, and emit per-record dicts.
- **`extract_equipment_descriptions` does not.** It pre-concatenates
  all pages in a section into one normalized string, then walks
  regex matches (`_HEADING_RE`) over that string, filtered by a
  dict lookup (`_HEADING_TO_ITEM_ID`). No font matching, no
  span/block traversal. Its closer engine sibling is `prose_section`,
  not a font-fingerprint walk.

**What the two real candidates actually share:**

- Page iteration → `block / line / span` traversal.
- Header detection by `(font_substring, font_size, tolerance)` on the
  first span of a line.
- Record boundary = next header (with end-of-page or
  end-of-range as terminators).

**What differs even between those two:**

| Dimension | `extract_magic_items` | `extract_features` |
| --- | --- | --- |
| Header fingerprints | 1 (GillSans-SemiBold 12pt) | 2 (GillSans-SemiBold 13.9pt class-feature + Cambria-BoldItalic 9.8pt lineage-trait) |
| Body grouping | Font-split into `metadata_blocks` (Cambria-Italic) + `description_blocks` (rest); spans preserved, not concatenated | Single bucket, concatenated string with `clean_text()` pass |
| Multi-line header continuation | Yes (joins lines ending in "and"/"or"/"of"/...) | No |
| Cross-page record merging | Yes, post-pass: merges item if `len(description) < 20` and no metadata | No (each page independent) |
| Structural-text filter | No | Yes (`_is_structural_text()` drops page numbers, table headers, etc.) |

**Engine return-type problem.** `extract_by_config()` returns
`RawTable` (row/column shape: `headers`, `rows: list[list[...]]`).
Font-fingerprint walks emit **lists of records** (per-item dicts), not
table rows. A binding requires either (a) widening
`extract_by_config()` to a `RawTable | RawRecordList` union, or
(b) adding a sibling `extract_records_by_config()` and routing the new
pattern types through it. Decision belongs in the pattern design.

**Sketch of minimum config schema** (not yet implemented):

```python
DATASET_CONFIG = {
    "pattern_type": "font_fingerprint_walk",
    "pages": (206, 253),  # inclusive; or {"start_const": ..., "end_const": ...}
    "header_fingerprints": [
        {
            "font_substring": "GillSans-SemiBold",
            "size": 12.0,
            "size_tolerance": 0.5,
            "role": "record_name",
        },
        # second fingerprint optional (features has two; magic_items has one)
    ],
    "body_grouping": "single_bucket",      # or "font_split"
    "body_split_fingerprints": {           # only if body_grouping == "font_split"
        "metadata": {"font_substring": "Cambria-Italic"},
    },
    "merge_partial_records": False,        # magic_items=True, features=False
    "filter_structural_text": False,       # features=True, magic_items=False
    "multi_line_header": False,            # magic_items=True, features=False
}
```

**Honest ROI assessment.** A `font_fingerprint_walk` pattern type would
have **two confirmed callers** (`extract_magic_items`,
`extract_features`), not the 3–5 that earlier BACKLOG framing implied.
`extract_spells` and `extract_monsters` are *probable* additional
callers under cross-page extension but neither has been inspected at
this depth. **Two callers is the ROI threshold** — below it, bespoke
is honest; above it, the pattern type pays for itself. This is right
at the edge.

**Recommended next step (single release, real work).** Pick ONE of:

1. **Prototype path.** Implement `font_fingerprint_walk` against
   `extract_features` first (simpler — one entry point, no cross-page
   merge, no font-split body). If the binding is clean, do
   `extract_magic_items` as the second binding and learn whether the
   config schema generalizes. If it doesn't, revert and document why.
   *Estimated scope: design + 1 binding + parity test in one focused
   session. NOT a release; the release is the second binding when the
   schema is proven.*
2. **Defer path.** Accept that 2 confirmed callers is below the
   pattern-type threshold for now. Mark the design pass complete, file
   the config sketch for reference, and move on to other v1.0 work.
   Revisit if/when `extract_spells` or `extract_monsters` get inspected
   at the same depth and add 1–2 more confirmed callers.

The "shared font-anchored pattern emerges" hand-waving in v0.33–v0.37
is now closed: the pattern was specified above, and the answer to
"does it justify a pattern type yet?" is "marginally — pick path 1 or
path 2 deliberately."

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

**Honest framing.** Of the seven `pdf_probe` lifecycle migrations in
v0.31.0–v0.37.0, only v0.31.0 (`extract_pdf_metadata`) and v0.32.0
(`extract_rules` + new `page_dict()` helper) had any structural value;
v0.33.0–v0.37.0 were one-line `fitz.open` → `open_pdf` swaps with
byte-identical output and no engine binding work. Each of those five
commit messages wrote "engine binding deferred until a shared
font-anchored pattern emerges" while never actually looking for that
pattern. The pattern is right there in the shape inventory above:
three extractors (`extract_magic_items`, `extract_features`,
`extract_equipment_descriptions`) share single-page font-fingerprint
walks; two more (`extract_spells`, `extract_monsters`) extend that
shape with cross-page state. That is what the proposed
`font_fingerprint_walk` pattern type would absorb.

**Concrete first step (not yet scheduled — design pass needed).** Read
`extract_magic_items`, `extract_features`, and `extract_equipment_descriptions`
side-by-side and write down the actual common shape:

1. What configuration does each extractor's font walk need? (header
   font + size + page range + record-end signal)
2. What is the shared record envelope? (`name`, `page` / `pages`,
   `description_blocks`, optional `metadata_blocks` / `header_blocks`)
3. What does the new `pattern_type` config look like? Sketch in
   [extraction_metadata.py](../src/srd_builder/extract/extraction_metadata.py).
4. What return type does the engine need to support? Today's
   `RawTable` is row/column-shaped; this pattern produces lists of
   records. Either widen `extract_by_config` or give it a sibling.

Output is a design doc + one proof binding (probably
`extract_equipment_descriptions` — the smallest of the three). Only
*then* ship it, and only as one release.

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
