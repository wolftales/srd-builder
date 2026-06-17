# Backlog

Captured ideas not yet scheduled. Pull items into a release plan as priorities allow.

## Data integrity / extraction confidence

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

## Notes
- Items here are *aspirational*, not blockers for the Blackmoor bundle.
- Add to this list freely; promote to a release plan (`docs/V0.x.0_PLAN.md`)
  when scheduling work.
