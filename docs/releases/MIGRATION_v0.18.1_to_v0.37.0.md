# Integration Migration Guide — v0.18.1 → v0.37.0

**Audience:** downstream consumers of `dist/srd_5_1/` (Blackmoor, VTTs, campaign
tools) who last integrated against srd-builder **v0.18.1** (Dec 2025) and are
adopting **v0.37.0** (Jun 2026).

**Scope:** consumer-visible changes only — shape of `meta.json`, per-dataset
envelopes, ID contracts, and new datasets. Internal refactors are linked but
not enumerated here.

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

> If your code uses the conceptual name "inventory" anywhere (it appears in
> internal helpers and older docs), the live key is `datasets`. The name
> "inventory" was never a real `meta.json` key — it has always been either
> `files` (≤ v0.23.x) or `datasets` (≥ v0.24.0).

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

39 duplicate feature IDs eliminated. See [v0.25.0.md](v0.25.0.md) for full
migration.

### Equipment IDs are now underscore-only

| v0.18.1 | v0.37.0 |
|---|---|
| `item:battle-axe` | `item:battle_axe` |
| `item:hand-crossbow` | `item:hand_crossbow` |

126 equipment IDs renamed. The hyphen → underscore rewrite is purely lexical;
no other equipment fields changed shape.

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

Generated exemplars ship under `dist/srd_5_1/schemas/exemplars/*.exemplar.json`
(added v0.26.0) — one minimal valid instance per schema. Use them as the
ground-truth shape for your loaders.

---

## 6. New datasets (5)

Five new atomic-reference datasets shipped between v0.18.1 and v0.37.0. All
are pure references (no PDF prose, just vocabulary):

| Dataset | Count | Schema | First shipped |
|---|---:|---|---|
| `ability_scores.json` | 6 | 1.0.0 | v0.19.x |
| `damage_types.json` | 13 | 1.0.0 | v0.19.x |
| `skills.json` | 18 | 1.0.0 | v0.19.x |
| `weapon_properties.json` | 11 | 1.0.0 | v0.19.x |
| `rules.json` | 167 | 3.0.0 | v0.17.0 (was previously partial) |

Loaders that iterate `meta["datasets"]` will pick these up automatically.
Loaders that hard-coded the 11-dataset list need updating to 16.

---

## 7. New bundle artifacts

Files shipped under `dist/srd_5_1/` that did not exist in v0.18.1:

| File / directory | Added in | Purpose |
|---|---|---|
| `quality_report.json` | v0.24.0 | Output of `scripts/audit_dataset_quality.py` |
| `schemas/exemplars/*.exemplar.json` | v0.26.0 | Generated minimal valid instances |
| `docs/DATA_DICTIONARY.md` | v0.26.x | Field-level reference |
| `docs/SCHEMAS.md` | v0.26.x | Schema-version policy |

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
