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

## Provenance audit (hand-curated data inventory)

Goal: every value in the published bundle must trace back to either (a) the
SRD PDF byte stream, or (b) an explicitly-declared, justified deviation.
Today several modules contain hand-curated values whose divergence from
source is *implied* by the file docstring but not formally tracked, tested,
or surfaced to downstream consumers.

### Inventory of hand-curated sources

| Module | Scope | Declared reason | Concerns |
| --- | --- | --- | --- |
| [src/srd_builder/srd_5_1/class_targets.py](src/srd_builder/srd_5_1/class_targets.py) | All 12 classes: hit_die, primary_abilities, saving throws, proficiencies, feature lists, subclass names, page numbers | "Manually transcribed via visual inspection" (pp. 8–55) | Drives `classes.json` AND `features.json` owner resolution. Page numbers are author-curated, not verified against PDF TOC. No round-trip test ensures `CLASS_DATA[i].features` actually appears on `CLASS_DATA[i].page`. |
| [src/srd_builder/srd_5_1/lineage_targets.py](src/srd_builder/srd_5_1/lineage_targets.py) | All 9 base lineages + subraces: ability_modifiers, size, speed, traits, languages, pages | "PDF text is corrupted; manually transcribed" (pp. 3–7) | Same as above. The "PDF corrupted" claim is plausible but not documented with a reproducer (which page, which extraction call, what was returned). |
| [src/srd_builder/srd_5_1/spell_class_targets.py](src/srd_builder/srd_5_1/spell_class_targets.py) | Spell→class mapping for all 6 caster classes (~300 spells × 6 classes) | "PDF text is corrupted; manually mapped" (pp. 105–113) | Largest hand-curated surface in the project. Errors here silently propagate to every spell record. No independent cross-check. |
| [src/srd_builder/data/poison_descriptions_manual.py](src/srd_builder/data/poison_descriptions_manual.py) | Full prose + DC + damage for all 14 SRD poisons | "Corrupted text on pages 204–205" (TODO: replace when better PDF source available) | Only file that names a specific PDF defect. Good model for documenting deviations. |
| [src/srd_builder/extraction/reference_data.py](src/srd_builder/extraction/reference_data.py) | `REFERENCE_TABLES` (spell-slots-by-level, etc.) | "Cannot be reliably extracted from PDF due to formatting issues" | Vague reason — same wording used for fundamentally different table types. No per-table justification. |
| [src/srd_builder/assemble/equipment_extended.py](src/srd_builder/assemble/equipment_extended.py) | `EXTENDED_EQUIPMENT`: ~12 items "referenced in equipment packs but not in SRD equipment tables" with *inferred* costs/weights | "Estimated costs/weights based on similar items to maintain referential integrity" | These items are **not in the SRD** at all — they are author-invented to keep equipment-pack cross-references resolvable. Critical to flag in `meta.json` so consumers know which items are inferred. Currently only the `_note` field hints at this. |
| [src/srd_builder/assemble/equipment_packs.py](src/srd_builder/assemble/equipment_packs.py) | All 7 equipment packs with item-by-item contents (item_id, quantity) | "Extracted from SRD 5.1 page 70" — but actually transcribed into a Python literal | Hardcoded `item:foo` IDs (now `item:foo_bar`) embedded in source. If the equipment ID scheme changes again, these silently break. |
| [src/srd_builder/assemble/equipment_descriptions.py](src/srd_builder/assemble/equipment_descriptions.py) | Prose descriptions for adventure-gear items with special rules (pp. 66–68) | "Documented in the SRD" — but transcribed not extracted | Same pattern as packs. No assertion the prose actually appears verbatim in the PDF. |
| [src/srd_builder/extract/extract_equipment.py](src/srd_builder/extract/extract_equipment.py) (lines 31–32) | `EQUIPMENT_START_PAGE = 61`, `EQUIPMENT_END_PAGE = 72` | Implicit | Magic numbers without TOC verification. Same risk for other extract_*.py page constants. |

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
- `EXTENDED_EQUIPMENT` items currently emit `_note` (free text). Promote to
  structured `_provenance` block per (2) above.
- `equipment_extended.py` / `equipment_packs.py` originally contained
  hyphenated IDs (`item:foo-bar`). Fixed in v0.25.0 via regex sweep — but
  the underlying risk (hand-edited IDs drifting from the canonical
  generator in `postprocess/ids.py`) is the real lesson. Should not be
  possible at all: pack contents should reference items by `simple_name`
  and have IDs synthesized at assembly time.
- `extract_equipment.py` `EQUIPMENT_START_PAGE` / `_END_PAGE` constants
  should be replaced with TOC lookup once `verify_pdf_sections.py` lands.

## Notes
- Items here are *aspirational*, not blockers for the Blackmoor bundle.
- Add to this list freely; promote to a release plan (`docs/V0.x.0_PLAN.md`)
  when scheduling work.
