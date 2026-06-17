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
| Path | [src/srd_builder/srd_5_1/class_targets.py](../src/srd_builder/srd_5_1/class_targets.py) |
| Scope | All 12 classes: hit_die, primary_abilities, saving throws, proficiencies, feature lists, subclass names, pages |
| Reason | `pdf_missing` (preliminary — verify) |
| PDF pages | 8–55 |
| Last verified | 2026-06-17 |
| Reproducer | **TODO** — re-attempt extraction; comment claims visual transcription but no defect documented |
| Downstream | `dist/srd_5_1/classes.json`, `dist/srd_5_1/features.json` (owner resolution) |

### `lineage_targets.py` — LINEAGE_DATA

| Field | Value |
| --- | --- |
| Path | [src/srd_builder/srd_5_1/lineage_targets.py](../src/srd_builder/srd_5_1/lineage_targets.py) |
| Scope | All 9 base lineages + subraces: ability_modifiers, size, speed, traits, languages, pages |
| Reason | **DISPUTED** — original claim was `pdf_corruption`, but verification (2026-06-17) shows the text is fully extractable once whitespace is normalized |
| PDF pages | 3–7 |
| Last verified | 2026-06-17 |
| Reproducer | [tests/test_pdf_provenance.py::test_lineage_pages_are_extractable_after_whitespace_normalization](../tests/test_pdf_provenance.py) |
| Notes | The SRD PDF uses `\t\r\xa0` (tab + CR + non-breaking space) sequences as word separators. The original "manually transcribed via visual inspection" claim was likely true against an older PyMuPDF, but under pymupdf 1.27.x all 10 tested lineage keywords (Dwarf, Hill Dwarf, High Elf, Halfling, Lightfoot, Dragonborn, Gnome, Half-Elf, Half-Orc, Tiefling) extract cleanly. **This manual override is a strong candidate for retirement.** A real lineage parser is in scope for v0.27.0. |
| Downstream | `dist/srd_5_1/lineages.json`, `dist/srd_5_1/features.json` (lineage-owned features) |

### `spell_class_targets.py` — *_SPELLS lists

| Field | Value |
| --- | --- |
| Path | [src/srd_builder/srd_5_1/spell_class_targets.py](../src/srd_builder/srd_5_1/spell_class_targets.py) |
| Scope | Spell→class mapping for all 8 caster classes (~888 lines, wired into every spell record) |
| Reason | **DISPUTED** — original claim was `pdf_corruption`, but verification (2026-06-17) shows pages 105–113 are fully extractable after whitespace normalization |
| PDF pages | 105–113 |
| Last verified | 2026-06-17 |
| Reproducer | [tests/test_pdf_provenance.py::test_spell_lists_pages_class_headers_are_extractable](../tests/test_pdf_provenance.py) |
| Notes | Same finding as lineages: under pymupdf 1.27.x with the standard `\t\r\xa0` whitespace normalization (see `utils.pdf_probe`), all 8 class section headers (Bard Spells, Cleric Spells, Druid Spells, Paladin Spells, Ranger Spells, Sorcerer Spells, Warlock Spells, Wizard Spells) AND a sampling of well-known spells (Vicious Mockery, Sacred Flame, Druidcraft, Eldritch Blast, Fire Bolt) appear in the page range. **This is the largest hand-curated surface in the project (~888 lines) and a strong retirement candidate for v0.27.0.** A real `extract_spell_classes.py` on top of `utils.pdf_probe` + `PAGE_INDEX["spell_lists"]` should replace it. |
| Downstream | `dist/srd_5_1/spells.json` (every record's `classes` field, set by `postprocess/spells.py`) |

### `poison_descriptions_manual.py` — POISON_DESCRIPTIONS

| Field | Value |
| --- | --- |
| Path | [src/srd_builder/data/poison_descriptions_manual.py](../src/srd_builder/data/poison_descriptions_manual.py) |
| Scope | Prose + DC + damage for all 14 SRD poisons |
| Reason | `pdf_corruption` |
| PDF pages | 204–205 |
| Last verified | (in-file TODO; no reproducer yet) |
| Reproducer | **TODO** — promote in-file comment to a runtime test (good template — wiring already supports extraction fallback) |
| Downstream | `dist/srd_5_1/poisons.json` |
| Notes | Already wired with the right shape: `parse_poisons_table.py` prefers manual descriptions but falls back to extracted ones, so dropping the manual file the moment extraction works requires no other change. |

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
| Path | [src/srd_builder/extract/extract_equipment.py](../src/srd_builder/extract/extract_equipment.py) (lines 31–32) |
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
