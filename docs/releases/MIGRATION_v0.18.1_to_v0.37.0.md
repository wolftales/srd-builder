# Integration Migration Guide — v0.18.1 → v0.37.0

**Audience:** downstream consumers of `dist/srd_5_1/` (Blackmoor, VTTs, campaign
tools) who last integrated against srd-builder **v0.18.1** (Dec 2025) and are
adopting **v0.37.0** (Jun 2026).

**Scope:** consumer-visible changes only — shape of `meta.json`, per-dataset
envelopes, ID contracts, and new datasets. Internal refactors are linked but
not enumerated here.

> **Revision history.** First published alongside v0.37.0. Revised in v0.39.0
> against the archived v0.18.1, v0.23.0, and v0.37.0 bundles after Blackmoor's
> consumer-integration review caught nine factual drifts between this guide
> and the artifacts. Inline corrections are marked with **(corrected
> v0.39.0)**; the omitted changes Blackmoor identified are appended in
> [§ 10. Changes this guide previously omitted](#10-changes-this-guide-previously-omitted).

---

## TL;DR — the smallest change that prevents silent breakage

```python
# v0.18.1
manifest = meta["files"]                  # {"monsters": "monsters.json", ...}
count    = len(json.load(open("monsters.json"))["monsters"])
status   = meta["extraction_status"]["monsters"]

# v0.37.0
manifest = meta["datasets"]               # {"monsters": {"file": "...", "count": N, "status": "..."}, ...}
count    = manifest["monsters"]["count"]  # now in meta directly
status   = manifest["monsters"]["status"]
items    = json.load(open("monsters.json"))["items"]   # was ["monsters"] for 3 legacy datasets
```

Every other consumer-facing change is enumerated below.

---

## 1. `meta.json` shape — manifest consolidation (v0.24.0)

Three parallel blocks collapsed into one. Full migration table is in
[docs/releases/v0.24.0.md](v0.24.0.md):

| v0.18.1 | v0.37.0 |
|---|---|
| `meta["files"][ds]` (filename) | `meta["datasets"][ds]["file"]` |
| `meta["files"]` (also listed `meta.json`, `build_report.json`, `index.json`) | dropped — these are well-known |
| `meta["extraction_status"][ds]` | `meta["datasets"][ds]["status"]` |
| (no per-dataset count in meta) | `meta["datasets"][ds]["count"]` |

Top-level keys removed: `files`, `extraction_status`.
Top-level key added: `datasets`.

> **(corrected v0.39.0)** The manifest key has gone through three names, not
> two. The archived intermediate bundle v0.23.0 carried a real top-level
> `inventory` key alongside `files` and `extraction_status` (the per-dataset
> count map). `inventory` was retired together with the consolidation into
> `datasets` in v0.24.0. If your loader was last touched between v0.20.0 and
> v0.23.x it may still reference `meta["inventory"]`; that path is also gone
> in v0.37.0. The full progression is `files` (≤ v0.19.x) → `files` +
> `inventory` + `extraction_status` (v0.20.x – v0.23.x) → `datasets`
> (≥ v0.24.0).

---

## 2. Per-dataset array key — full normalization (v0.30.0)

Three datasets used the dataset name as the array key in v0.18.1. They now
all use `items`:

| File | v0.18.1 array key | v0.37.0 array key |
|---|---|---|
| `conditions.json` | `conditions` | `items` |
| `diseases.json` | `diseases` | `items` |
| `features.json` | `features` | `items` |
| (all other 13 datasets) | already `items` | `items` |

```python
# v0.18.1 reader pattern
items = doc.get("items") or doc[dataset_name]

# v0.37.0 — single shape, no fallback needed
items = doc["items"]
```

---

## 3. Per-dataset `_meta` envelope changes

Every dataset's `_meta` block was tightened. Concrete diff on `conditions.json`:

| Field | v0.18.1 | v0.37.0 |
|---|---|---|
| `source` | `"SRD 5.1"` | `"SRD_CC_v5.1"` |
| `game_system` | *(absent)* | `"dnd5e"` (new) |
| `description` | `"Standard game conditions from Appendix PH-A"` | dropped |
| `<dataset>_count` (e.g. `conditions_count`) | `15` | renamed to `item_count` |
| `item_count` | *(absent)* | `15` (replaces per-dataset count name) |
| `schema_version` | `"1.4.0"` | reflects current schema |

`schema_version` inside `_meta` always matches `meta.json.schemas[<schema_name>]`
for that dataset.

---

## 4. ID-contract changes (v0.25.0)

Two breaking ID rewrites landed together so they could be reviewed as a single
pass.

### Feature IDs are now owner-qualified

| v0.18.1 | v0.37.0 |
|---|---|
| `feature:rage` | `feature:barbarian:rage` |
| `feature:ability_score_improvement` (appeared on 12 classes) | `feature:fighter:ability_score_improvement`, etc. |

> **(corrected v0.39.0)** Counting terms matter here:
>
> - v0.18.1 features.json: **246 records, 160 unique IDs**, 16 distinct IDs
>   were repeated across multiple classes (e.g. `feature:ability_score_improvement`
>   on all 12 classes counts as 1 distinct repeated ID and 12 records); the
>   16 repeated IDs accounted for **86 duplicate records**.
> - v0.37.0 features.json: **245 unique owner-qualified IDs, 245 records**.
> - The often-repeated "39 duplicate feature IDs eliminated" figure conflates
>   different counts. The accurate consumer-visible facts are: total record
>   count moved 246 → 245; every ID is now unique; the `feature:rage`-style
>   bare IDs are gone in favor of `feature:<class>:<feature>`.

See [v0.25.0.md](v0.25.0.md) for full migration.

### Equipment IDs are now underscore-only

| v0.18.1 | v0.37.0 |
|---|---|
| `item:battle-axe` | `item:battle_axe` |
| `item:hand-crossbow` | `item:hand_crossbow` |

> **(corrected v0.39.0)** "126 equipment IDs renamed" was imprecise. Compared
> against archived v0.18.1: **125 existing IDs** map through the
> hyphen-to-underscore rewrite, and **1 equipment record was added** in the
> intervening releases. v0.37.0 therefore presents 126 IDs that are
> "newly seen" relative to v0.18.1, but only 125 of those are renames; the
> 126th is genuinely new content. The hyphen → underscore rewrite itself is
> purely lexical; no other equipment fields changed shape because of it.

---

## 5. Schema major bumps — every surviving schema

All 11 schemas present in v0.18.1 were major-bumped at least once. Audit each
field your consumer reads against the current schema in `schemas/`:

| Schema | v0.18.1 | v0.37.0 | Major bumps |
|---|---|---|---:|
| `monster` | 1.5.0 | 2.0.0 | 1 |
| `spell` | 1.5.0 | 2.0.0 | 1 |
| `equipment` | 1.4.0 | 2.2.0 | 1 |
| `class` | 1.4.0 | 2.1.0 | 1 |
| `lineage` | 1.4.0 | 2.0.0 | 1 |
| `table` | 1.4.0 | 3.0.0 | 2 |
| `condition` | 1.4.0 | 3.0.0 | 2 |
| `disease` | 1.4.0 | 3.0.0 | 2 |
| `poison` | 1.4.0 | 2.0.0 | 1 |
| `features` | 1.4.0 | 4.0.0 | 3 |
| `magic_item` | 1.1.0 | 2.0.0 | 1 |

> **(corrected v0.39.0)** The v0.18.1 *manifest* declared all 11 schema
> versions in `meta.json.schemas`, but the v0.18.1 *bundle* only shipped 8
> schema files inside `schemas/`. Missing files were
> `disease.schema.json`, `poison.schema.json`, and `magic_item.schema.json`;
> consumers wanting to validate those datasets in v0.18.1 had no schema
> available locally. v0.37.0+ ships all 16 schema files alongside their
> manifest declarations.

Generated exemplars ship under `dist/srd_5_1/schemas/exemplars/*.exemplar.json`
(added v0.26.0) — one minimal valid instance per schema. Use them as a
shape reference for your loaders.

> **(corrected v0.39.0)** Exemplars are SHAPE references, not proof of
> bundle conformance. Use the actual shipped data (`<dataset>.json`) +
> schema (`schemas/<name>.schema.json`) for strict validation. As of
> v0.38.1, all 1,687 emitted records validate against their shipped
> schemas (closing the 491 invalid items reported during v0.37.0 review).

---

## 6. New datasets (4 new files, 1 newly manifest-declared)

Four new atomic-reference dataset *files* shipped between v0.18.1 and v0.37.0,
and one previously-shipped dataset (`rules.json`) was added to the manifest:

| Dataset | Count | Schema | Status relative to v0.18.1 |
|---|---:|---|---|
| `ability_scores.json` | 6 | 1.0.0 | New file (first shipped v0.19.x) |
| `damage_types.json` | 13 | 1.0.0 | New file (first shipped v0.19.x) |
| `skills.json` | 18 | 1.0.0 | New file (first shipped v0.19.x) |
| `weapon_properties.json` | 11 | 1.0.0 | New file (first shipped v0.19.x) |
| `rules.json` | 167 | 3.1.0 | **File already shipped in v0.18.1 with 172 items** but was omitted from `meta.json`'s manifest; first manifest-declared in v0.20.0 and substantially revised since (172 → 167 records with new hierarchical `rule:section/subsection` IDs landed in v0.30.0) |

> **(corrected v0.39.0)** The earlier version of this table characterized
> `rules.json` as a "new dataset (first shipped v0.17.0)." The archived
> v0.18.1 bundle *does* contain `rules.json` with 172 items; what was
> missing was its declaration in `meta.files`. Consumers iterating only
> `meta["files"]` in v0.18.1 would not have seen the file even though it
> existed on disk. Newly-manifest-declared is not the same as new content.

Loaders that iterate `meta["datasets"]` will pick up all of these
automatically. Loaders that hard-coded the 11-dataset list need updating to
16.

---

## 7. New bundle artifacts

Files shipped under `dist/srd_5_1/` that did not exist in v0.18.1:

| File / directory | Added in | Purpose | Status |
|---|---|---|---|
| `schemas/exemplars/*.exemplar.json` | v0.26.0 | Generated minimal valid instances | Ships in v0.37.0+ |
| `index.json` | v0.21.0 (cross-references added v0.22.0) | Pre-built search + xref index | Ships in v0.37.0+ |
| `schemas/meta.schema.json`, `schemas/build_report.schema.json` | v0.38.0 | Envelope contract | Ships in v0.38.0+ |
| `docs/COMPATIBILITY.md` | v0.39.0 | Pre-1.0 contract policy | Ships in v0.39.0+ |

> **(corrected v0.39.0)** Two previously-listed entries have been removed
> from this table:
>
> - `docs/DATA_DICTIONARY.md` and `docs/SCHEMAS.md` were already present in
>   the archived v0.18.1 bundle. They are not new artifacts; the earlier
>   version of this guide listed them in error.
> - `quality_report.json` was claimed to ship in v0.37.0 but it is **not
>   present** in the archived v0.37.0 bundle inventory, nor in the v0.38.x /
>   v0.39.x bundles. The `scripts/audit_dataset_quality.py` audit is a
>   development tool whose output is not part of the consumer-visible
>   bundle. Loaders that referenced `quality_report.json` must drop the
>   reference.

None of these break existing consumers; they are additive.

---

## 8. Migration cheat sheet for Blackmoor's test helpers

Common patterns and their v0.37.0 equivalents:

```python
# Manifest discovery
- inventory = meta["files"]
+ inventory = {ds: spec["file"] for ds, spec in meta["datasets"].items()}

# Count check
- assert len(items) == meta["inventory"][ds]
+ assert len(items) == meta["datasets"][ds]["count"]

# Status check
- if meta["extraction_status"][ds] == "complete":
+ if meta["datasets"][ds]["status"] == "complete":

# Items array
- items = doc.get("items") or doc[ds]
+ items = doc["items"]

# Iterating all datasets (now includes 5 new ones)
- for ds in HARDCODED_LIST_OF_11:
+ for ds in meta["datasets"]:
```

---

## 9. Where to look for finer-grain details

Per-release notes between v0.18.1 and v0.37.0 live under
[docs/releases/](.). The releases most likely to matter to a downstream
consumer:

| Release | Why a consumer cares |
|---|---|
| [v0.19.0](v0.19.0.md) | First atomic reference datasets |
| [v0.24.0](v0.24.0.md) | `meta.json` consolidation (`files` → `datasets`) |
| [v0.25.0](v0.25.0.md) | Feature + equipment ID contracts |
| [v0.26.0](v0.26.0.md) | Schema exemplars added to bundle |
| [v0.27.0](v0.27.0.md) | Live spell-class extractor (callable signature change for direct consumers of `clean_spell_record`) |
| [v0.27.4](v0.27.4.md) | +8 equipment rows (page 74 fix) |

Releases v0.28.0–v0.37.0 did not ship per-release notes; the changes they
introduced are reflected in the live `dist/srd_5_1/meta.json` and the
generated `dist/srd_5_1/README.md`. The doc-table sync (`make sync-docs`,
landed post-v0.37.0) ensures repo docs always match the shipped `meta.json`.

---

## 10. Changes this guide previously omitted

The original v0.37.0 publication of this guide did not enumerate the
consumer-visible deltas below. They are added in v0.39.0 after the Blackmoor
consumer-integration review caught them by diffing the archived v0.18.1 and
v0.37.0 bundles directly.

### 10.1 Removed `summary` fields

The `summary` field that v0.18.1 attached to several dataset records was
removed during the v0.20.x–v0.30.x refactors in favor of section-keyed
`description` / structured prose blocks. Datasets affected: conditions,
diseases, magic items, rules, features, lineages. If your loader displayed
`record["summary"]` as a short blurb, it must now either fall back to
`record["description"]` (or its dataset-specific equivalent) or render
nothing.

### 10.2 Lineage ID rename: `lightfoot_halfling` → `lightfoot`

The Halfling subrace previously published as `lineage:lightfoot_halfling`
(v0.18.1) is now `lineage:lightfoot` in v0.37.0+. The PDF heading reads
"Lightfoot" (not "Lightfoot Halfling"); the v0.27.0 lineage extractor
produced the PDF-faithful name and the legacy ID was retired. Lookups by
the old ID will fail. See [docs/PROVENANCE.md](../PROVENANCE.md#lineage_targetspy--lineage_data-retired-in-v0270)
for the full provenance.

### 10.3 Rules count and ID shape changes

- **Count.** `rules.json` went from 172 items (v0.18.1, undeclared in
  manifest) to 167 items (v0.37.0). The 5-record net delta is the
  combination of v0.30.0 hierarchical dedup + content revision.
- **ID shape.** Rule IDs went from flat `rule:<simple_name>` to
  `rule:<section>/<subsection>` hierarchical IDs in v0.30.0 (e.g.
  `rule:ability_checks/strength`). The `rule.schema.json` pattern was
  relaxed in v0.37.2 to permit the `/` separator. Loaders that pattern-match
  rule IDs against `^rule:[a-z0-9_]+$` will reject every v0.30.0+ ID.

### 10.4 Tables count and ID changes

- **Count.** `tables.json` went from 11 tables (v0.18.1) to 35 tables
  (v0.37.0) as the table extractor was wired up to additional
  `TARGET_TABLES`. **(corrected v0.39.0)** v0.39.0 raises the count to 41
  by adding 6 reference tables that previously had dangling cross-references
  from class and lineage records: `table:proficiency_bonus`,
  `table:spell_slots_full_caster`, `table:paladin_spell_slots`,
  `table:ranger_spell_slots`, `table:warlock_spell_slots`, and
  `table:draconic_ancestry`.
- **ID shape.** Table IDs stabilized as `table:<simple_name>` (no further
  shape changes since v0.18.1).

### 10.5 New `index.json` cross-reference structure

v0.37.0 ships `dist/srd_5_1/index.json` (introduced v0.21.0, cross-reference
block expanded in v0.22.0) which v0.18.1 did not have. Consumers don't need
to load it — it is an optimization for reverse lookups ("which spells deal
fire damage?") and is regenerated on every build. If your loader builds the
same indexes from scratch, you can keep doing so and ignore `index.json`.

v0.39.0 fixes the `stats.total_entities` math (previously dropped
`creatures`, `npcs`, and `weapon_properties` from the count) and adds the
`by_name_all: dict[str, list[str]]` sibling on the `features` and `rules`
indexes so consumers can resolve ambiguous display names to the full set of
matching IDs instead of just the first one seen.

---
