# Integration Guide (Consumers)

This document is written for **downstream consumers** of the srd-builder bundle (campaign tools, VTTs, LLM applications, analysis pipelines). It describes the shape of `dist/srd_5_1/`, the conventions consumers should rely on, and how to react when our schemas change.

> Looking for *producer-side* build verification? See [docs/VERIFICATION_CHECKLIST.md](docs/VERIFICATION_CHECKLIST.md).

---

## Producer / Consumer split

**srd-builder** (upstream) extracts structured JSON from the SRD 5.1 PDF and ships a self-contained bundle. It guarantees:

- Reproducible, deterministic output (same PDF → identical bundle)
- Schema-validated datasets
- Full provenance back to the source PDF (page numbers, hash)
- Stable IDs, stable file shapes within a MAJOR schema version

**Consumers** load the bundle and build the application. The goal is that you never need to re-parse the PDF or maintain your own extraction pipeline.

---

<!-- AUTO-SYNC:int:bundle-header START -->
## Bundle Layout (v0.38.0)
<!-- AUTO-SYNC:int:bundle-header END -->

The full bundle lives under `dist/srd_5_1/`:

<!-- AUTO-SYNC:int:bundle-tree START -->
```
dist/srd_5_1/
├── README.md                  # Generated dynamically from meta.json
├── meta.json                  # Source of truth for inventory + schema manifest
├── index.json                 # Cross-dataset lookup maps
├── build_report.json          # Per-stage parse/postprocess counts
│
├── ability_scores.json        # 6     (schema v1.0.0)
├── classes.json               # 12    (schema v2.1.0)
├── conditions.json            # 15    (schema v3.0.0)
├── damage_types.json          # 13    (schema v1.1.0)
├── diseases.json              # 3     (schema v3.0.0)
├── equipment.json             # 259   (schema v2.3.0)
├── features.json              # 245   (schema v4.0.0)
├── lineages.json              # 13    (schema v2.0.0)
├── magic_items.json           # 240   (schema v2.0.0)
├── monsters.json              # 317   (schema v2.1.0)
├── poisons.json               # 14    (schema v2.1.0)
├── rules.json                 # 167   (schema v3.1.0)
├── skills.json                # 18    (schema v1.0.0)
├── spells.json                # 319   (schema v2.0.0)
├── tables.json                # 35    (schema v3.1.0)
├── weapon_properties.json     # 11    (schema v1.0.0)
│
├── schemas/                   # All 16 JSON Schema files (copies of /schemas/)
└── docs/                      # DATA_DICTIONARY.md, SCHEMAS.md (shipped to consumers)
```
<!-- AUTO-SYNC:int:bundle-tree END -->

<!-- AUTO-SYNC:int:totals START -->
**Totals shipped:** 16 datasets, 1,687 items.
<!-- AUTO-SYNC:int:totals END -->

---

## `meta.json` is the source of truth

When a new bundle drops, read `meta.json` first. It tells you everything that shipped without your code having to guess:

```python
import json
meta = json.loads(open("dist/srd_5_1/meta.json").read())

builder_version = meta["build"]["builder_version"]   # e.g. "0.24.0"
datasets        = meta["datasets"]                   # {"monsters": {"file": "monsters.json", "count": 317, "status": "complete"}, ...}
schemas         = meta["schemas"]                    # {"monster": "2.0.0", ...}
```

**Use `datasets` for sanity checks and discovery.** Each entry has `{file, count, status}`. Don't hard-code per-dataset counts in your loader — iterate the manifest and compare against what you actually parsed. If we add a dataset in a future release, your loader picks it up automatically.

**Use `schemas` to gate features.** If you depend on a schema field that's only present at v2.0.0, branch on the version here.

---

## Dataset shape

Two shapes ship today:

### Shape A — `items` wrapper (most datasets)

```json
{
  "_meta": {
    "source": "SRD_CC_v5.1",
    "schema_version": "2.0.0",
    "format": "unified_items_array",
    "entity_count": 317,
    "generated_at": "2026-06-17T00:00:00Z",
    "builder_version": "0.23.0"
  },
  "items": [ ... ]
}
```

Used by: `ability_scores`, `classes`, `damage_types`, `equipment`, `lineages`, `magic_items`, `monsters`, `poisons`, `rules`, `skills`, `spells`, `tables`, `weapon_properties`.

### Shape B — dataset-named array key (legacy)

```json
{
  "_meta": { ... },
  "conditions": [ ... ]
}
```

Used by: `conditions`, `diseases`, `features`.

Normalizing this is on the roadmap (see [docs/PARKING_LOT.md](docs/PARKING_LOT.md) → "JSON Field Ordering"). Until then, treat the items-array key as either `items` or the dataset's basename. A simple helper:

```python
def load_items(path: str, dataset: str) -> list[dict]:
    doc = json.loads(open(path).read())
    return doc.get("items") or doc[dataset]
```

---

## ID conventions

Every entity has a `{id, name, simple_name}` triple:

| Field | Purpose | Example |
|-------|---------|---------|
| `id` | Stable, namespaced identifier — what cross-references point at | `"monster:aboleth"` |
| `name` | Display name | `"Aboleth"` |
| `simple_name` | Lowercase, snake_case, ASCII-only — what indexes key on | `"aboleth"` |

**Namespaces shipped:** `ability:`, `class:`, `condition:`, `creature:`, `damage_type:`, `disease:`, `feature:`, `item:`, `lineage:`, `magic_item:`, `monster:`, `npc:`, `poison:`, `rule:`, `skill:`, `spell:`, `table:`, `weapon_property:`.

> **Monster note:** `monsters.json` uses three prefixes — `monster:` (main bestiary, pages 261–365), `creature:` (Appendix MM-A, pages 366–394), `npc:` (Appendix MM-B, pages 395–403). Code that only checked `id.startswith("monster:")` will miss creatures and NPCs. Filter on prefix only when you actually want that subset; otherwise iterate `items`.

---

## Cross-references

The v2.0.0 schemas use `*_id` fields to point between datasets:

- `spell.damage_type_id` → `damage_type:fire`
- `equipment.weapon_property_ids[]` → `weapon_property:versatile`
- `skill.ability_id` → `ability:strength`
- `rule.related_spells[]` → `spell:fireball`

Resolve them with `index.json`'s `by_name` maps or by building your own `{id: entity}` dict at load time.

---

## Indexes (`index.json`)

`index.json` ships with cross-dataset lookup maps so you don't have to build them. Typical contents:

- `by_name` for every dataset (entity aliases auto-expanded)
- `by_type` / `by_category` / `by_cr` where it makes sense per dataset
- Top-level `terminology` aliases (e.g. `"races" → "lineages"`) for backwards-compatible category names

If you need an index we don't ship, it's safe to build one in your loader — just don't write it back into our files.

---

## Schema validation

Every dataset ships with a corresponding JSON Schema under `schemas/`. To validate in your CI:

```python
import json
import jsonschema

meta    = json.loads(open("dist/srd_5_1/meta.json").read())
dataset = "monsters"

schema  = json.loads(open(f"dist/srd_5_1/schemas/monster.schema.json").read())
data    = json.loads(open(f"dist/srd_5_1/{meta['datasets'][dataset]['file']}").read())

jsonschema.validate(instance=data, schema=schema)
```

Or shell out to `check-jsonschema`:

```bash
check-jsonschema --schemafile dist/srd_5_1/schemas/monster.schema.json \
                 dist/srd_5_1/monsters.json
```

---

## Versioning contract

Three versions matter to consumers:

| Version | Where it lives | What it tracks |
|---------|----------------|----------------|
| **Bundle / package version** | `meta.json.build.builder_version`, dataset `_meta.builder_version` | "Which release of srd-builder produced this bundle?" |
| **Per-schema version** | `meta.json.schemas.<dataset>.version`, dataset `_meta.schema_version`, schema file `version` | "What data contract should I validate against?" |
| **Extractor version** | `*_raw.json _meta.extractor_version` (only in source repo, not in the bundle) | Internal — tracks raw PDF extraction format |

**Compatibility rules** (semver):

- A **patch** bump (e.g. `2.0.0 → 2.0.1`) is doc/clarification — no consumer changes needed.
- A **minor** bump (e.g. `2.0.0 → 2.1.0`) is additive — new optional fields, new enum values. Existing consumers keep working.
- A **major** bump (e.g. `1.x → 2.0.0`) is breaking — renamed/removed fields, type changes. Read the release notes and migrate.

---

## Upgrade workflow

1. Pull the new bundle (`pip install srd-builder==X.Y.Z` or `git pull`)
2. Read `meta.json` — check `build.builder_version`, `inventory`, and `schemas`
3. Run your loader against the new bundle in CI; any schema-validation failure tells you which dataset's contract moved
4. For any schema whose **major** version bumped, consult that release's notes and migrate
5. Re-run your test suite

---

## Provenance and licensing

Every entity preserves source provenance:

- `page: int` — SRD 5.1 page number the entity was extracted from
- `source: "SRD 5.1"` — source document identifier
- `meta.json.license` — full license text
- `meta.json.build.pdf_sha256` — hash of the source PDF used to build this bundle

This is enough for downstream attribution and for verifying you and the producer parsed the same PDF.

---

## Where to file issues

| Type of problem | Where |
|-----------------|-------|
| Extraction bug (wrong value, missing entity) | GitHub Issues with the `data` label |
| Schema feedback or proposed field | GitHub Issues with the `schema` label |
| Performance, loader patterns | GitHub Discussions |

When reporting an issue, please include the bundle's `builder_version` and the dataset's `schema_version` — both are in the file's `_meta` block.
