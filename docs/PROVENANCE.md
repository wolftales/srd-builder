# Provenance Registry

Source-of-truth declaration for every dataset value shipped in `dist/srd_5_1/`
that does **not** come directly from PDF byte extraction. Each entry must
either justify its deviation with a reproducer (preferred) or carry a
`TODO` to add one.

This registry is the operational form of the inventory captured in
[docs/BACKLOG.md](BACKLOG.md). The BACKLOG describes the *aspiration*;
this file is the *current state*.

> **Operational lesson (v0.26.0 → v0.26.1).** Two of the eight
> registered claims have already been disproved by mechanical probes
> ([tests/test_pdf_provenance.py](../tests/test_pdf_provenance.py)).
> Treat any future "PDF corrupted" rationale as a hypothesis until a
> reproducer test fails. See `AGENTS.md` § *PDF extraction discipline*.

## Reason codes

| Code | Meaning | Removal trigger |
| --- | --- | --- |
| `pdf_corruption` | PDF bytes exist on the page but extraction returns garbled / unreadable text. Reproducer test required. | Reproducer test starts failing (PyMuPDF or PDF revision fixed the corruption). |
| `pdf_missing` | Concept exists in SRD prose but no structured source. Transcription must be faithful to prose. | New structured source upstream. |
| `cross_reference_glue` | Author-invented to keep cross-references resolvable. Not in SRD at all. | Underlying cross-reference removed or reworked. |
| `derived_lookup_table` | Calculated from game rules; not extracted. Belongs in rules dataset, not the dataset it currently lives in. | Migrated to rules dataset. |
| `alias` / `common_name` | Augmentation layer on top of source. Does not overwrite source field. | (No removal — permanent augmentation.) |

## Status at a glance

8 historical hand-curated sources. 4 retired in the v0.27.x line.
3 awaiting reproducer (low-priority — equipment-related, structural).

| Source | Lines | Status | Reproducer | Live extractor | Quality vs. legacy | Blocker |
| --- | ---: | --- | --- | --- | --- | --- |
| `lineage_targets.py` | 326 | ✅ **RETIRED v0.27.0 P1** | ✓ | [`extract_lineages.py`](../src/srd_builder/extract/datasets/extract_lineages.py) | **Better** — caught one transcription error (`Lightfoot Halfling` → `Lightfoot`) | — |
| `spell_class_targets.py` | 917 | ✅ **RETIRED v0.27.0 P2** | ✓ | [`extract_spell_classes.py`](../src/srd_builder/extract/datasets/extract_spell_classes.py) | **Equivalent** — 778-for-778 byte-perfect parity across all 8 caster classes | — |
| `class_targets.py` | 763 | ✅ **RETIRED v0.27.2 P3** | ✓ | [`extract_classes.py`](../src/srd_builder/extract/datasets/extract_classes.py) | **Better** — caught one transcription error (Monk L4 ordering); 4 silently-fabricated cells now reproducer-pinned overrides | — |
| `poison_descriptions.py` | 129 | ✅ **RETIRED v0.27.3** | ✓ | [`parse_poison_descriptions.py`](../src/srd_builder/parse/parse_poison_descriptions.py) returns clean 14/14 with byte-perfect description/save/damage parity | **Equivalent** — 14/14 perfect match against legacy POISON_DESCRIPTIONS dict | — |
| `equipment_extended.py` | 167 | ⬜ **LIVE** (augmentation) | N/A (not in SRD) | N/A — items are author-invented to keep pack cross-references resolvable | — | Promote `_note` → structured `_provenance` block per BACKLOG proposal 2 |
| `equipment_packs.py` | 323 | ⬜ **LIVE** | **TODO** | none | (Unverified — p. 70 pack table likely extractable; pre-v1.0 audit) | No reproducer yet |
| `equipment_descriptions.py` | 398 | ⬜ **LIVE** | **TODO** | none | (Unverified — pp. 66–68 prose likely extractable like other prose sections) | No reproducer yet |
| `extract_equipment.py` page constants | 2 | ⬜ **LIVE** (constants) | **TODO** | N/A — would be replaced by TOC lookup | — | `scripts/verify_pdf_sections.py` + `Document.get_toc()` adoption |

### What "Better" means here

For each retired module the new extractor is **higher quality** than the
legacy constant on every axis we can measure:

| Axis | Legacy `*_targets.py` | Live `extract_*.py` |
| --- | --- | --- |
| Reproducibility against new PDF revisions | Manual re-transcription | Re-runs automatically |
| Audit trail for PDF ↔ dataset deltas | None (silent) | Reproducer-pinned (`page.search_for()`) per override |
| Detection of upstream PDF changes | Drifts silently | Tests fail loudly |
| Drift between legacy data and PDF source | 2 confirmed transcription errors found during retirement (`Lightfoot Halfling`, Monk L4 order); 4 cells in `class_targets` silently filled in letters the PDF doesn't contain | Each deviation lives in a typed override dict (`_PROGRESSION_FIXES`) backed by a failing-on-mismatch reproducer |
| Schema-shape parity | (was the source of truth) | Byte-for-byte equivalent shape consumed by the same downstream `parse_*`/`postprocess_*` modules; verified by snapshot tests |

For `poison_descriptions.py` the prose extractor and the damage-formula
parser both reach the same parity bar (14/14 byte-perfect on
description, save, and damage) once the damage regex was extended in
v0.27.3 to handle the delayed-damage `"taking X (NdM) poison damage on
a failed save"` phrasing.

## Registry

### `class_targets.py` — CLASS_DATA  *(retired in v0.27.x P3)*

| Field | Value |
| --- | --- |
| Status | **RETIRED** in v0.27.x — replaced by [src/srd_builder/extract/datasets/extract_classes.py](../src/srd_builder/extract/datasets/extract_classes.py) |
| Scope (was) | All 12 classes: hit_die, primary_abilities, saving throws, proficiencies, feature lists, subclass names, pages, 20-level progression (~763 lines) |
| Original reason | `pdf_missing` / "manually transcribed via visual inspection" — **disproven** (v0.27.0 P3 reproducer confirmed all class-page text extractable after whitespace normalization) |
| PDF pages | 8–55 |
| Reproducer | [tests/test_pdf_provenance.py::test_class_pages_are_extractable_after_whitespace_normalization](../tests/test_pdf_provenance.py) |
| Live extractor tests | [tests/test_extract_classes.py](../tests/test_extract_classes.py) (72 assertions across discovery + 5 field groups + 20-level progression coverage) |
| Snapshot fixture | [tests/fixtures/srd_5_1/class_targets_snapshot.json](../tests/fixtures/srd_5_1/class_targets_snapshot.json) — preserved as a deterministic reference for the extractor; built from the retired CLASS_DATA with PDF-fidelity corrections applied (e.g., Monk L4 features reordered to PDF order) |
| Notes | Five-step extractor (discovery → hit_die + abilities + proficiencies → features + subclasses → spellcasting → progression). The progression step uses a bbox-aware Features column walk that locates the Calibri-Bold header, clusters level cells by x (handles barbarian's two-column newspaper layout), filters out warlock's "Slot Level" duplicate column, and post-processes cells with hyphen/apostrophe heals. Four genuinely-unextractable cells (barbarian L11 "Relentless Rage", ranger L8 "Land's Stride", rogue L10 "Ability Score Improvement", wizard L20 "Signature Spells") are filled by `_PROGRESSION_FIXES`, each pinned by a `page.search_for()` reproducer in `test_class_progression_truncations_are_real`. `parse_classes()` and `parse_features()` now take `class_data=` parameters; `build.py` calls `extract_classes(pdf_files[0])["classes"]` once and threads the result into both. |
| Downstream | `dist/srd_5_1/classes.json`, `dist/srd_5_1/features.json` (owner resolution) |

### `lineage_targets.py` — LINEAGE_DATA  *(retired in v0.27.0)*

| Field | Value |
| --- | --- |
| Status | **RETIRED** in v0.27.0 — replaced by [src/srd_builder/extract/datasets/extract_lineages.py](../src/srd_builder/extract/datasets/extract_lineages.py) |
| Scope (was) | All 9 base lineages + subraces: ability_modifiers, size, speed, traits, languages, pages (~326 lines) |
| Original reason | `pdf_corruption` (disproven 2026-06-17 — text is fully extractable once whitespace is normalized) |
| PDF pages | 3–7 |
| Reproducer | [tests/test_pdf_provenance.py::test_lineage_pages_are_extractable_after_whitespace_normalization](../tests/test_pdf_provenance.py) |
| Live extractor tests | [tests/test_extract_lineages.py](../tests/test_extract_lineages.py) (49 assertions across 9 races + 4 subraces) |
| Notes | The SRD PDF uses `\t\r\xa0` (tab + CR + non-breaking space) sequences as word separators; the original "manually transcribed via visual inspection" claim was likely true against an older PyMuPDF, but under pymupdf 1.27.x the data was readable. Extractor walks pages 3–7 by font fingerprint (18pt = race, 12pt G-SB = subrace, 9.8pt Cambria-BoldItalic + period = trait header). One deliberate PDF-fidelity correction: the legacy data called the Halfling subrace "Lightfoot Halfling" but the PDF heading literally reads "Lightfoot". |
| Downstream | `dist/srd_5_1/lineages.json`, `dist/srd_5_1/features.json` (lineage-owned features) |

### `spell_class_targets.py` — *_SPELLS lists  *(retired in v0.27.0)*

| Field | Value |
| --- | --- |
| Status | **RETIRED** in v0.27.0 — replaced by [src/srd_builder/extract/datasets/extract_spell_classes.py](../src/srd_builder/extract/datasets/extract_spell_classes.py) |
| Scope (was) | Spell→class mapping for all 8 caster classes (~917 lines, wired into every spell record) |
| Original reason | `pdf_corruption` (disputed 2026-06-17, disproven during v0.27.0 cutover — 778-for-778 byte-perfect match between extractor and the hand-curated `*_SPELLS` lists across all 8 classes) |
| PDF pages | 105–113 |
| Reproducer | [tests/test_pdf_provenance.py::test_spell_lists_pages_class_headers_are_extractable](../tests/test_pdf_provenance.py) |
| Live extractor tests | [tests/test_extract_spell_classes.py](../tests/test_extract_spell_classes.py) (12 assertions; per-class set equality pinned against snapshot) |
| Snapshot fixture | [tests/fixtures/srd_5_1/spell_class_targets_snapshot.json](../tests/fixtures/srd_5_1/spell_class_targets_snapshot.json) — preserved as a deterministic reference for `bump_version.py` and `test_golden_spells.py` (avoids forcing them to re-run the live extractor on every fixture refresh) |
| Notes | Detection rules: 13.9pt GillSans-SemiBold = class header (`Bard Spells`, …, `Wizard Spells`); 12pt G-SB = level header (skipped); 9.8pt Cambria = spell name (`normalize_id` applied). 18pt G-SB "Spell Lists" and 10.5–11.0pt page-number/footer runs are skipped. `clean_spell_record()` now takes an explicit `spell_classes_map=` keyword (default `None` → no `classes` field attached) instead of importing a module-level lookup. |
| Downstream | `dist/srd_5_1/spells.json` (every record's `classes` field, attached by `postprocess/spells.py`) |

### `poison_descriptions.py` — POISON_DESCRIPTIONS  *(retired in v0.27.3)*

| Field | Value |
| --- | --- |
| Status | **RETIRED** in v0.27.3 — replaced by [src/srd_builder/parse/parse_poison_descriptions.py](../src/srd_builder/parse/parse_poison_descriptions.py) |
| Scope (was) | Prose + DC + damage for all 14 SRD poisons (~129 lines) |
| Original reason | `pdf_corruption` — **disproven** in v0.27.1 (pages 204–205 fully extractable after whitespace normalization) |
| PDF pages | 204–205 |
| Reproducer | [tests/test_pdf_provenance.py::test_poison_pages_are_extractable_after_whitespace_normalization](../tests/test_pdf_provenance.py), [tests/test_pdf_provenance.py::test_poison_descriptions_extract_all_14_sections_cleanly](../tests/test_pdf_provenance.py) |
| Live extractor tests | [tests/test_parse_poison_descriptions.py](../tests/test_parse_poison_descriptions.py), [tests/test_golden_poisons.py](../tests/test_golden_poisons.py) |
| Notes | Fourth "PDF corruption" claim in the codebase; fourth to fail under reproducer scrutiny. v0.27.1 fixed the splitter (smart-quote `clean_text`, `start_marker="Sample Poisons"`, restored `Assassin's Blood` header, renamed `assassin's_blood` key). v0.27.3 finished the job by extending the damage-formula regex from `takes?` to `tak(?:es?\|ing)` (covers the four delayed-damage poisons — `midnight_tears`, `purple_worm_poison`, `serpent_venom`, `wyvern_poison`), stripping the leading `"Name (Type). "` section header from the description body, and emitting the `type_id` field. Manual diff confirms 14/14 byte-perfect parity against the retired `POISON_DESCRIPTIONS` dict on description, save, and damage. `parse_poisons_table.py` no longer imports the manual dict; the merge consumes the extracted `descriptions_map` only. |
| Downstream | `dist/srd_5_1/poisons.json` |

### `equipment_extended.py` — EXTENDED_EQUIPMENT

| Field | Value |
| --- | --- |
| Path | [src/srd_builder/assemble/equipment_extended.py](../src/srd_builder/assemble/equipment_extended.py) |
| Scope | ~12 items referenced in equipment packs but not in any SRD equipment table; *inferred* costs/weights |
| Reason | `cross_reference_glue` |
| PDF pages | (none — items are not in SRD) |
| Last verified | 2026-06-17 |
| Reproducer | N/A (records flagged in source by `_note` field; should be promoted to structured `_provenance` block per BACKLOG.md proposal 2) |
| Downstream | `dist/srd_5_1/equipment.json` (12 records with `_note`) |

### `equipment_packs.py` — EQUIPMENT_PACKS

| Field | Value |
| --- | --- |
| Path | [src/srd_builder/assemble/equipment_packs.py](../src/srd_builder/assemble/equipment_packs.py) |
| Scope | 7 equipment packs, item-by-item contents (item_id, quantity) |
| Reason | `pdf_missing` |
| PDF pages | 70 |
| Last verified | 2026-06-17 |
| Reproducer | **TODO** — pack table on p. 70 should be extractable; revisit during pre-v1.0 audit |
| Downstream | `dist/srd_5_1/equipment.json` (pack records) |

### `equipment_descriptions.py` — *_DESCRIPTIONS

| Field | Value |
| --- | --- |
| Path | [src/srd_builder/assemble/equipment_descriptions.py](../src/srd_builder/assemble/equipment_descriptions.py) |
| Scope | Adventure gear / tools / armor / lifestyle prose descriptions |
| Reason | `pdf_missing` |
| PDF pages | 66–68 |
| Last verified | 2026-06-17 |
| Reproducer | **TODO** — prose is in SRD body text, should be extractable like other prose sections |
| Downstream | `dist/srd_5_1/equipment.json` (description fields on adventure-gear records) |

### `extract_equipment.py` — page constants

| Field | Value |
| --- | --- |
| Path | [src/srd_builder/extract/datasets/extract_equipment.py](../src/srd_builder/extract/datasets/extract_equipment.py) (lines 31–32) |
| Scope | `EQUIPMENT_START_PAGE = 61`, `EQUIPMENT_END_PAGE = 72` |
| Reason | `cross_reference_glue` (anchors for extraction range) |
| PDF pages | 62–73 (1-indexed SRD labels — note constants use 0-indexed PyMuPDF) |
| Last verified | 2026-06-17 |
| Reproducer | **TODO** — replace with TOC lookup via `fitz.Document.get_toc()` once `scripts/verify_pdf_sections.py` lands (BACKLOG.md "Section / structural verification") |
| Downstream | All equipment extraction |

## Process

- Any change touching a registered file must update `Last verified`.
- New hand-curated source → new entry here before merge.
- Reproducer-backed entries (`pdf_corruption`) should each have a test in
  `tests/test_pdf_provenance.py`. The test skips gracefully when the PDF
  is not present (CI / container builds).
- Records emitted from `cross_reference_glue` or `pdf_missing` sources
  should carry an optional `_provenance` block (TODO: promote
  `equipment_extended.py`'s `_note` field per BACKLOG proposal 2).

## Cumulative finding (v0.26.0 → v0.27.3)

Four "PDF text is corrupted" claims were made by the original
hand-curated modules. All four have been disproven by mechanical
reproducer tests under pymupdf 1.27.x with standard whitespace
normalization (see [`utils.pdf_probe`](../src/srd_builder/utils/pdf_probe.py)):

| Claim | Disproven in | Outcome |
| --- | --- | --- |
| Lineages corrupted (pp. 3–7) | v0.26.0 | Retired in v0.27.0 P1 |
| Spell-lists corrupted (pp. 105–113) | v0.26.1 | Retired in v0.27.0 P2 |
| Class pages corrupted (pp. 8–55) | v0.27.0 P3 (probe) | Retired in v0.27.2 P3 (cutover) |
| Poison pages corrupted (pp. 204–205) | v0.27.1 | Retired in v0.27.3 (damage-formula parser extended; 14/14 byte-perfect parity) |

Net result of the v0.27.x line: ~2,135 lines of hand-curated Python
data deleted (326 lineages + 917 spell_classes + 763 classes + 129
poisons), 2 silent transcription errors corrected, 4 silently-
fabricated cell values now pinned by reproducer tests. The "PDF
corrupted" rationale should be treated as a hypothesis until a
reproducer fails — see `AGENTS.md` § *PDF extraction discipline*.
