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

8 historical hand-curated sources. 6 retired in the v0.27.x line.
1 active augmentation (`equipment_extended.py`, no SRD source).
1 structural drift fixed and pinned by audit test in v0.27.4.

| Source | Lines | Status | Reproducer | Live extractor | Quality vs. legacy | Blocker |
| --- | ---: | --- | --- | --- | --- | --- |
| `lineage_targets.py` | 326 | ✅ **RETIRED v0.27.0 P1** | ✓ | [`extract_lineages.py`](../src/srd_builder/extract/datasets/extract_lineages.py) | **Better** — caught one transcription error (`Lightfoot Halfling` → `Lightfoot`) | — |
| `spell_class_targets.py` | 917 | ✅ **RETIRED v0.27.0 P2** | ✓ | [`extract_spell_classes.py`](../src/srd_builder/extract/datasets/extract_spell_classes.py) | **Equivalent** — 778-for-778 byte-perfect parity across all 8 caster classes | — |
| `class_targets.py` | 763 | ✅ **RETIRED v0.27.2 P3** | ✓ | [`extract_classes.py`](../src/srd_builder/extract/datasets/extract_classes.py) | **Better** — caught one transcription error (Monk L4 ordering); 4 silently-fabricated cells now reproducer-pinned overrides | — |
| `poison_descriptions.py` | 129 | ✅ **RETIRED v0.27.3** | ✓ | [`parse_poison_descriptions.py`](../src/srd_builder/parse/parse_poison_descriptions.py) returns clean 14/14 with byte-perfect description/save/damage parity | **Equivalent** — 14/14 perfect match against legacy POISON_DESCRIPTIONS dict | — |
| `equipment_extended.py` | 167 | ✅ **LIVE** (augmentation, structured provenance since v0.27.7) | N/A (not in SRD) | N/A — items are author-invented to keep pack and monster cross-references resolvable | Every record now carries a typed `_provenance` block (`source`, `reason`, `referenced_by`, `module`, `estimates`) instead of free-text `_note`; schema bumped to `equipment.schema.json` 2.2.0 | — |
| `equipment_packs.py` | 323 | ✅ **RETIRED v0.27.5 P6** | ✓ | [`extract_equipment_packs.py`](../src/srd_builder/extract/datasets/extract_equipment_packs.py) | **Equivalent** — 7-for-7 byte-perfect parity (name, cost_gp, description, contents item_id + quantity) against the retired EQUIPMENT_PACKS literal | — |
| `equipment_descriptions.py` | 398 | ✅ **RETIRED v0.27.6 P7** | ✓ | [`extract_equipment_descriptions.py`](../src/srd_builder/extract/datasets/extract_equipment_descriptions.py) | **Better** — 69/69 items recovered with PDF-truth corrections: 2 page-attribution fixes (`item:antitoxin-vial` p.67→p.66, `item:arcane-focus` p.67→p.66) and 6 description-content additions (parenthetical cross-references and table mentions that the curated literal had editorially stripped, now restored) | — |
| `extract_equipment.py` page constants | 2 | ✅ **RESOLVED v0.27.4** | ✓ | Constants harmonized to 1-indexed; PDF page 74 (Services / Lifestyle tables) now extracted | Bug-fix — 8 dropped rows recovered | — |

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
| Scope | 9 items referenced in equipment packs (8) or monster stat blocks (1) but not in any SRD equipment table; *inferred* costs/weights for pack-referenced items, placeholder cost (0 gp) for the monster-referenced `item:natural_armor` |
| Reason | `cross_reference_glue` |
| PDF pages | (none — items are not in SRD) |
| Last verified | 2026-06-18 (v0.27.7) |
| Provenance block | Every record carries a typed `_provenance` block per BACKLOG proposal 2: `{source: "inferred", reason: "pack_cross_reference" \| "monster_cross_reference", referenced_by: <pack name or surface>, module: "equipment_extended.py", estimates: ["cost", "weight"] \| []}`. The `ExtendedProvenance` TypedDict pins the shape statically; the `equipment.schema.json` 2.2.0 `_provenance` property pins it at the JSON layer. Pinned by [tests/test_equipment_extended_provenance.py](../tests/test_equipment_extended_provenance.py) (5 tests: uniform shape, valid reasons, pack-items estimate cost+weight, natural_armor estimates nothing, `get_extended_equipment` preserves provenance). |
| Downstream | `dist/srd_5_1/equipment.json` (9 records with `_provenance`) |

### `equipment_packs.py` — EQUIPMENT_PACKS  *(retired in v0.27.5)*

| Field | Value |
| --- | --- |
| Status | **RETIRED** in v0.27.5 — replaced by [src/srd_builder/extract/datasets/extract_equipment_packs.py](../src/srd_builder/extract/datasets/extract_equipment_packs.py) |
| Scope (was) | 7 equipment packs, item-by-item contents (item_id, quantity), pack costs, descriptive prose (~323 lines) |
| Original reason | `pdf_missing` — **disproven** in v0.27.x reproducer (PDF page 70 prose fully extractable: all 7 pack headers and their comma-separated `Includes …` contents clauses recovered cleanly under standard whitespace normalization) |
| PDF pages | 70 |
| Reproducer | [tests/test_pdf_provenance.py::test_equipment_packs_pdf_page_70_section_header_extractable](../tests/test_pdf_provenance.py), [tests/test_pdf_provenance.py::test_equipment_packs_pdf_page_70_pack_header_extractable](../tests/test_pdf_provenance.py) (parametrized × 7), [tests/test_pdf_provenance.py::test_equipment_packs_pdf_page_70_contents_extractable](../tests/test_pdf_provenance.py) (parametrized × 7 with distinctive multi-word signature phrases) |
| Live extractor tests | [tests/test_equipment_packs.py](../tests/test_equipment_packs.py) (11 tests: 7-for-7 byte-perfect parity on `(item_id, quantity)` lists, pack-summary snapshot, meta block, description shape, and integration check against built `equipment.json`) |
| Notes | Parser walks page 70 with `_PACK_HEADER_RE` (`{Name}’s Pack (N gp).`) and `_SECTION_END_RE` ("Tools\nA tool helps"), then splits each `Includes …` clause on `, ` / ` and ` boundaries. Each token is resolved via a small typed `_PHRASE_TO_ITEM` table that maps the SRD's exact prose phrase (e.g., `"a backpack"`, `"5 candles"`, `"a bag of 1,000 ball bearings"`) to a stable `item_id` and a quantity rule (parsed leading digit, or `qty_override=1` for N-bound phrases like "10 feet of string" where the digit is part of item identity). The trailing "The pack also has 50 feet of hempen rope strapped to the side of it" sentence (Burglar’s, Dungeoneer’s, Explorer’s) is handled by appending `("item:rope_hempen_50_feet", 1)` after the `Includes` list. The U+2019 curly apostrophe in the SRD is normalized to ASCII `'` at the extractor output boundary so the assembler keys (`Burglar's Pack`) match the rest of the dataset. `assemble_equipment_from_tables(parsed_tables, ruleset, *, equipment_packs=None)` now takes the extracted packs as a kwarg; `_assemble_equipment_packs` iterates the parameter list and contains inline private `_calculate_pack_weight` and `_validate_pack_contents` helpers. `build.py` calls `extract_equipment_packs(pdf_files[0])["packs"]` once and threads the result through. |
| Downstream | `dist/srd_5_1/equipment.json` (7 pack records under `sub_category == "equipment_pack"`) |

### `equipment_descriptions.py` — *_DESCRIPTIONS  *(retired in v0.27.6)*

| Field | Value |
| --- | --- |
| Status | **RETIRED** in v0.27.6 — replaced by [src/srd_builder/extract/datasets/extract_equipment_descriptions.py](../src/srd_builder/extract/datasets/extract_equipment_descriptions.py) |
| Scope (was) | 4 hand-curated TypedDict lists — `ADVENTURE_GEAR_DESCRIPTIONS` (42 entries, pp. 66–68), `TOOLS_DESCRIPTIONS` (9 entries, pp. 70–71), `ARMOR_DESCRIPTIONS` (12 entries, p. 63), `LIFESTYLE_DESCRIPTIONS` (6 entries, p. 73). 69 entries / ~398 lines total. |
| Original reason | `pdf_missing` — **disproven** in v0.27.5 reproducer (every section's first heading and 13 representative item signatures all recovered cleanly under standard whitespace normalization) |
| PDF pages | 63 (armor), 66–68 (adventure_gear), 70–71 (tools), 73 (lifestyle) |
| Reproducer | [tests/test_pdf_provenance.py::test_equipment_descriptions_section_anchor_extractable](../tests/test_pdf_provenance.py) (parametrized × 4 sections), [tests/test_pdf_provenance.py::test_equipment_descriptions_item_signature_extractable](../tests/test_pdf_provenance.py) (parametrized × 13 — heading + distinctive content-phrase probe per item) |
| Live extractor tests | [tests/test_extract_equipment_descriptions.py](../tests/test_extract_equipment_descriptions.py) (73 assertions: 69 parametrized per-item snapshots `(item_id, page, prefix, suffix)`, plus PDF-order, meta block, four-section breakdown, and "ends-with-period" invariants) |
| Notes | Parser walks the four sections by concatenating each section’s pages into one normalized string, finds heading candidates with `_HEADING_RE` (Title-Case + lowercase glue words `and`/`or`/`of` + period), filters via a 69-entry `_HEADING_TO_ITEM_ID` table, and slices each item’s body up to the next resolving heading or a known subsection terminator (`Heavy Armor`, `Medium Armor`, `Self-Sufficiency`, `Mounts and Vehicles`, `Adventuring Gear`). Normalization handles four PDF artifacts: (1) soft-hyphen runs (`-\xad‐‑` → `-`) inside compound words like `15-foot`, (2) curly U+2019 → ASCII `'`, (3) page-footer text (`System Reference Document 5.1 N`) stripped to keep cross-page descriptions clean, (4) line-wrap em-dashes (`item— an` → `item—an`). Two of the curated module’s `page` fields were wrong (`Antitoxin` and `Arcane Focus` are on p. 66, not p. 67) and six descriptions had editorially stripped phrases (`book` lost `(described later in this section)`, `holy_symbol` lost the Appendix PH-B reference, etc.); the new extractor restores all six and corrects both pages — the data is strictly better than what was retired. `assemble_equipment_from_tables(..., equipment_descriptions=None)` now takes the extracted descriptions as a kwarg; `_add_item_descriptions` builds a lookup from the parameter list (no module-level imports). `build.py` calls `extract_equipment_descriptions(pdf_files[0])["descriptions"]` once via the `_extract_equipment_pdf_data` helper (which also wraps the v0.27.5 packs extractor). |
| Downstream | `dist/srd_5_1/equipment.json` (description fields on adventure-gear / tools / armor / lifestyle records) |

### `derive_reference_tables.py` — DRACONIC_ANCESTRY + 5 derived tables  *(added in v0.39.0)*

| Field | Value |
| --- | --- |
| Status | **LIVE** (one hand-curated literal; five derived from already-extracted class progressions) |
| Path | [src/srd_builder/postprocess/derive_reference_tables.py](../src/srd_builder/postprocess/derive_reference_tables.py) |
| Scope | Six reference tables that close Blackmoor's 21 dangling cross-references (`table:proficiency_bonus`, `table:spell_slots_full_caster`, `table:paladin_spell_slots`, `table:ranger_spell_slots`, `table:warlock_spell_slots`, `table:draconic_ancestry`) |
| Reason codes | Five tables: `derived_lookup_table` (aggregated from existing class progressions; pure transformation, no PDF re-extraction). One table (`table:draconic_ancestry`): `pdf_missing` — the table exists as a standalone PDF table on page 5 (Dragonborn section) but is not yet listed in [src/srd_builder/extract/table_targets.py](../src/srd_builder/extract/table_targets.py), so the live extractor never pulls it. |
| Removal trigger | Derived five: never (they remain useful cross-reference aggregations even after extraction improves). `draconic_ancestry`: add an entry to `TARGET_TABLES` and confirm extracted content matches the hand-curated literal byte-for-byte. |
| Reproducer | TODO — add a derivation parity test (`tests/test_derive_reference_tables.py`) that asserts the proficiency bonus column is identical across all 12 class progressions, and the full-caster slot columns are identical across bard/cleric/druid/sorcerer/wizard. |
| Notes | The class progression tables represent "no slot" as the digit `0` or `1` overprinted with U+0336 (combining long stroke overlay) which renders as strikethrough; the derivation strips the overlay and normalizes empty cells to em-dash (`\u2014`). The `draconic_ancestry` literal is faithful to the SRD 5.1 CC-BY content (10 dragon types × 3 columns: Dragon, Damage Type, Breath Weapon). |
| Downstream | `dist/srd_5_1/tables.json` (6 added rows raise table count from 35 to 41) |

### `extract_equipment.py` — page constants  *(resolved in v0.27.4)*

| Field | Value |
| --- | --- |
| Status | **RESOLVED** in v0.27.4 — constants harmonized to the same 1-indexed PDF page convention used by `extract_spells.py`, `extract_magic_items.py`, and `extract_conditions.py`. End constant corrected from `72` (which dropped PDF page 74) to `74` (matching `PAGE_INDEX["equipment"]`). |
| Path | [src/srd_builder/extract/datasets/extract_equipment.py](../src/srd_builder/extract/datasets/extract_equipment.py) (lines 30–35) |
| Scope (was) | `EQUIPMENT_START_PAGE = 61`, `EQUIPMENT_END_PAGE = 72` (0-indexed; iteration `range(start, end+1)` covered PyMuPDF pages 61–72 = PDF pages 62–73, silently dropping PDF page 74 with the Services / Lifestyle / Spellcasting Services tables) |
| Scope (now) | `EQUIPMENT_START_PAGE = 62`, `EQUIPMENT_END_PAGE = 74` (1-indexed; iteration `range(start - 1, end)` covers PyMuPDF pages 61–73 = PDF pages 62–74) |
| PDF pages | 62–74 (matches `PAGE_INDEX["equipment"]`) |
| Reason for original drift | The other three per-dataset extractors were written to a 1-indexed convention and pulled their range from a `dataclass` config; `extract_equipment.py` was written earlier against module-level 0-indexed constants and never reconciled. The off-by-one on the end constant was invisible at the time because the dropped page's content was hand-curated in `assemble/equipment_descriptions.py` `LIFESTYLE_DESCRIPTIONS` (since retired in v0.27.6). |
| Audit test | [tests/test_pdf_provenance.py::test_extractor_page_constants_agree_with_page_index](../tests/test_pdf_provenance.py) — parametrized across all four extractors; fails if any extractor's `(START, END)` constants drift from `PAGE_INDEX`. |
| Newly captured | 8 additional rows from PDF page 74 (Bread loaf, Inn-stay tiers, Skilled hireling, Messenger, Ship's passage, etc.). At the time of v0.27.4 the curated `LIFESTYLE_DESCRIPTIONS` was left in place; the broader `assemble/equipment_descriptions.py` was subsequently retired in v0.27.6 by [`extract_equipment_descriptions.py`](../src/srd_builder/extract/datasets/extract_equipment_descriptions.py). |
| Downstream | All equipment extraction |

## Process

- Any change touching a registered file must update `Last verified`.
- New hand-curated source → new entry here before merge.
- Reproducer-backed entries (`pdf_corruption`) should each have a test in
  `tests/test_pdf_provenance.py`. The test skips gracefully when the PDF
  is not present (CI / container builds).
- Records emitted from `cross_reference_glue` or `pdf_missing` sources
  carry a structured `_provenance` block (`source`, `reason`,
  `referenced_by`, `module`, `estimates`). Pinned for
  `equipment_extended.py` in v0.27.7 via the `ExtendedProvenance`
  TypedDict + `equipment.schema.json` 2.2.0 `_provenance` property.

## Cumulative finding (v0.26.0 → v0.27.5)

Four "PDF text is corrupted" claims and one "PDF missing" claim were
made by the original hand-curated modules. All five have been
disproven by mechanical reproducer tests under pymupdf 1.27.x with
standard whitespace normalization (see
[`utils.pdf_probe`](../src/srd_builder/utils/pdf_probe.py)):

| Claim | Original reason | Disproven in | Outcome |
| --- | --- | --- | --- |
| Lineages corrupted (pp. 3–7) | `pdf_corruption` | v0.26.0 | Retired in v0.27.0 P1 |
| Spell-lists corrupted (pp. 105–113) | `pdf_corruption` | v0.26.1 | Retired in v0.27.0 P2 |
| Class pages corrupted (pp. 8–55) | `pdf_missing` | v0.27.0 P3 (probe) | Retired in v0.27.2 P3 (cutover) |
| Poison pages corrupted (pp. 204–205) | `pdf_corruption` | v0.27.1 | Retired in v0.27.3 (damage-formula parser extended; 14/14 byte-perfect parity) |
| Equipment packs missing (p. 70) | `pdf_missing` | v0.27.5 reproducer | Retired in v0.27.5 P6 (7-for-7 byte-perfect parity) |
| Equipment descriptions missing (pp. 63, 66–68, 70–71, 73) | `pdf_missing` | v0.27.5 reproducer (×4 sections + ×13 item probes) | Retired in v0.27.6 P7 (69/69 items recovered; 2 page corrections + 6 PDF-truth content additions surfaced as drift in the curated literal) |

In addition, v0.27.4 closed a sixth, structural finding: the equipment
extractor was silently dropping PDF page 74 due to an inherited
0-indexed `EQUIPMENT_END_PAGE = 72` constant. Harmonized to 1-indexed
and pinned by `test_extractor_page_constants_agree_with_page_index`
(parametrized across equipment, spells, magic_items, conditions).

Net result of the v0.27.x line: ~2,856 lines of hand-curated Python
data deleted (326 lineages + 917 spell_classes + 763 classes + 129
poisons + 323 equipment_packs + 398 equipment_descriptions), 2 silent
transcription errors corrected, 4 silently-fabricated cell values now
pinned by reproducer tests, 1 silent page-drop bug (8 rows / PDF page
74) recovered, and 6 silently-stripped description phrases plus 2
incorrect `page` attributions caught and corrected by the
equipment-descriptions extractor in v0.27.6.
The "PDF corrupted" / "PDF missing" rationales should be treated as
hypotheses until a reproducer fails — see `AGENTS.md` § *PDF extraction
discipline*.

## Data quality — session-level summary (v0.27.x line)

This section captures the *measurable* quality difference between the
start of the v0.27.x line and the close of v0.27.6, for use as
release-note input and as evidence that the "declare corrupted,
transcribe by hand" pattern was a quiet correctness liability.

| Axis | Before v0.27.0 | After v0.27.6 |
| --- | --- | --- |
| Hand-curated `*_targets.py` / `*_descriptions.py` / `EQUIPMENT_PACKS` lines on the source-of-truth path | ~2,856 (lineages 326 + spell_classes 917 + classes 763 + poisons 129 + equipment_packs 323 + equipment_descriptions 398) | 0 |
| "PDF corrupted/missing" claims in the codebase | 6 unverified | 0 — all disproven by reproducers |
| Silent transcription errors | unknown (not detectable without a reproducer) | 2 corrected (`Lightfoot Halfling` → `Lightfoot`; Monk L4 feature ordering) |
| Silently-stripped description phrases | unknown (not detectable without a reproducer) | 6 restored in v0.27.6 (book "described later in this section", gaming-set "Tools table examples", holy-symbol "Appendix PH-B", musical-instrument "Tools table", pouch "described earlier", artisans-tools "table shows examples") |
| Silently-incorrect `page` fields | unknown (not detectable without a reproducer) | 2 corrected in v0.27.6 (`item:antitoxin-vial` p.67→p.66, `item:arcane-focus` p.67→p.66) |
| Silently-fabricated dataset cells | 4 (class progression) | 0 — all 4 pinned by `_PROGRESSION_FIXES` reproducer-backed overrides |
| Silently-dropped PDF rows | 8 (entire PDF page 74 of equipment) | 0 — recovered in v0.27.4, audit test parametrized across all four per-dataset extractors |
| Audit infrastructure | None — page constants, transcription, and "corruption" claims were unchecked | Parametrized cross-extractor page-constants test pinning all 4 extractors to `PAGE_INDEX`; per-region reproducer tests in [tests/test_pdf_provenance.py](../tests/test_pdf_provenance.py); per-item snapshot tests for live extractors |
| Test count | 460 (v0.27.0 baseline) | 558 (v0.27.6) |
| Source of truth for PDF page ranges | Module-level constants, mixed 0-/1-indexed conventions across 4 extractors | `PAGE_INDEX` ([src/srd_builder/utils/page_index.py](../src/srd_builder/utils/page_index.py)) is the sole source; constants in extractors are pinned by audit test |
| TOC-based page lookup | Considered as alternative | Abandoned — SRD PDF's `Document.get_toc()` returns only 2 file-level entries, so it is unusable as a region map |

The headline trade is favorable: ~2,856 lines of opaque hand-curated
Python replaced by ~1,540 lines of reproducer-pinned extractors and
parsers (see `extract_lineages.py`, `extract_spell_classes.py`,
`extract_classes.py`, `parse_poison_descriptions.py`,
`extract_equipment_packs.py`, `extract_equipment_descriptions.py`),
every one of which fails loudly on upstream PDF drift. That is the
property the legacy literals never had.
