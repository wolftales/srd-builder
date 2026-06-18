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

## Registry

### `class_targets.py` — CLASS_DATA

| Field | Value |
| --- | --- |
| Path | [src/srd_builder/rulesets/srd_5_1/class_targets.py](../src/srd_builder/rulesets/srd_5_1/class_targets.py) |
| Scope | All 12 classes: hit_die, primary_abilities, saving throws, proficiencies, feature lists, subclass names, pages, 20-level progression (~763 lines) |
| Reason | **DISPUTED** — original claim was `pdf_missing` / "manually transcribed via visual inspection," but verification (v0.27.0) shows pages 8–55 are fully extractable after whitespace normalization |
| PDF pages | 8–55 |
| Last verified | v0.27.0 |
| Reproducer | [tests/test_pdf_provenance.py::test_class_pages_are_extractable_after_whitespace_normalization](../tests/test_pdf_provenance.py) |
| Notes | Same finding as lineages (retired v0.27.0 P1) and spell_class_targets (retired v0.27.0 P2): all 12 class names, 15 sampled well-known features (Rage, Spellcasting, Sneak Attack, Action Surge, Wild Shape, Lay on Hands, Divine Sense, Favored Enemy, Cunning Action, Sorcerous Origin, Pact Magic, Arcane Recovery, Bardic Inspiration, Channel Divinity), and the standard section headers (Hit Points, Proficiencies, Equipment, Primal Path, Bard College, Divine Domain) are all present in pages 8–55. **Retirement is more involved than spell lists** — CLASS_DATA's structured payload (proficiencies dict with armor/weapons/tools/skills, feature-ID lists, subclass mapping, 20-level progression) is significantly richer than a flat spell list, so a real `extract_classes.py` will need a larger font-fingerprint + table walk. The probe only confirms the text is present; it does not yet replace the module. |
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

### `poison_descriptions.py` — POISON_DESCRIPTIONS

| Field | Value |
| --- | --- |
| Path | [src/srd_builder/rulesets/srd_5_1/poison_descriptions.py](../src/srd_builder/rulesets/srd_5_1/poison_descriptions.py) |
| Scope | Prose + DC + damage for all 14 SRD poisons (~109 lines) |
| Reason | **DISPUTED** — original claim was `pdf_corruption`, but verification (v0.27.1) shows pages 204–205 are fully extractable after whitespace normalization |
| PDF pages | 204–205 |
| Last verified | v0.27.1 |
| Reproducer | [tests/test_pdf_provenance.py::test_poison_pages_are_extractable_after_whitespace_normalization](../tests/test_pdf_provenance.py) |
| Notes | Fourth "PDF corruption" claim in the codebase, fourth to fail under reproducer scrutiny. Same era/author as lineage_targets (retired v0.27.0 P1), spell_class_targets (retired v0.27.0 P2), and class_targets (DISPUTED v0.27.0 P3). All 14 poison names, all 5 DC values, and standard mechanic keywords appear in pages 204–205 after whitespace normalization. **However, retirement is gated on fixing the prose section splitter, not on PDF readability.** The live `parse_poison_description_records` pipeline already exists and runs, but produces three concrete bugs: (1) the `assassin's blood` entry is dropped entirely — the U+2019 fancy apostrophe in the heading defeats the section detector; (2) the `malice` description absorbs ~2000 extra characters from neighboring sections; (3) the `torpor` description absorbs ~3700 extra characters. Until the section splitter is fixed, the hand-curated POISON_DESCRIPTIONS map remains the correct production behavior. `parse_poisons_table.py` already prefers manual descriptions and falls back to extracted ones, so the moment the splitter is fixed the manual file can be deleted with no other code change. |
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

## Status snapshot (2026-06-17, v0.26.1)

- 8 registered sources
- 2 reproducer-backed (lineages, spell_class_targets — both **dispute**
  the original corruption claim; both retire-able in v0.27.0)
- 6 awaiting reproducer
- 0 fully retired

### Cumulative finding (v0.26.0 → v0.26.1)

The lineage reproducer (v0.26.0) and the spell-class reproducer
(v0.26.1) **both** disprove the "PDF text is corrupted" claim under
pymupdf 1.27.x with standard whitespace normalization (see
`utils.pdf_probe`). That covers two of the three hand-curated modules
that used the corruption rationale. The implicit corruption rationale
on `class_targets.py` is the next candidate to probe — once verified,
the registry shrinks from 8 sources to 5 in v0.27.0 by writing real
parsers on top of `utils.pdf_probe` + `PAGE_INDEX`.
