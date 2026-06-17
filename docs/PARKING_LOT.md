# Parking Lot — Deferred Work

Tracks features and improvements that have been discussed but not yet scheduled.
Items here are **live and still relevant**; completed/resolved items live in
`archive/docs/PARKING_LOT_2025-pre-v0.23.md`.

> Last review: v0.23.0 (2026-06-17). Sharpened during the pre-v1.0 audit pass.

---

## Architecture & Data Model

### Item Variants & Magic Items Architecture

**Date raised:** 2025-10-30 · **Status:** Research needed

How should we model variant items (e.g. `+1 longsword`, `+2 longsword`, `flame
tongue longsword`) without duplicating the base equipment entry? Magic items
currently sit in their own dataset; variant relationships are implicit.

**Options under consideration:**

1. Keep magic items separate, add an explicit `base_item_id` reference back to
   `equipment`.
2. Promote a generic `variants` array on the base item with per-variant overrides.
3. Hybrid: keep separate datasets but add an `index.json` cross-reference block.

Picks affect Blackmoor (and any other consumer) — defer until we have a second
ruleset or a real consumer pain point to anchor the decision.

### Sentient Magic Items as Rules Content

**Date raised:** 2025-12-21 · **Status:** Architectural question

The "Sentient Magic Items" rules text describes a system, not an item. Today it
lives as a rule entry. Question: should it move to a `systems` dataset or get a
new `rules.sentient_items` sub-key with structured fields (alignment table,
purpose table, conflict mechanics)?

Pair with the Item Variants decision above — both are about where the schema
boundary lies between data and game systems.

### Combined Spell Indexes

**Status:** Idea — low priority

Pre-build nested indexes for common combined queries like "ritual spells
available to wizards" so consumers don't have to JOIN at runtime. Doable from
`spells.json` + `classes.json`; ship inside `index.json`.

### terminology.aliases Field in meta.json

**Status:** Deferred until second ruleset or naming conflict

We currently ship a single `terminology.aliases` entry (`race → lineage`).
Re-evaluate the API shape once we have multiple rulesets (5.2.1, ORC material,
Pathfinder) where naming actually diverges.

---

## Data Quality

### Container Capacity Hardcoded Values

**Date raised:** 2025-11-02 · **Status:** Technical debt — works but not ideal

8 of 13 containers have parsed capacity; 5 are filled from a hardcoded fallback
table in the equipment parser. Long-term fix is to extract capacity from PDF
table footnotes (currently dropped on the floor). Low priority while the values
stay correct.

### Equipment Table Cross-References

**Status:** Documented limitation

Equipment tables reference other tables (e.g. tools → "see Mounts and Vehicles
section"). These cross-references are captured as plain text in table footers,
not as structured `references` metadata. Add a `cross_references: [...]` field
once a consumer asks for it.

### Equipment Name Aliases

**Date raised:** 2025-11-02 · **Status:** Identified, deferred

PDF uses "Adventuring Gear" and "gear" interchangeably; we normalize to "gear".
A future alias layer in `index.json` could let consumers query by either label.

### Poison Descriptions — PDF Corruption

**Status:** Known limitation, documented in archived release notes

Some poison descriptions have garbled bytes in the SRD PDF source. Current
parser preserves the corrupt text; a manual override table would fix it but
introduces a maintenance burden.

### Class Progression Tables — Cosmetic Issues

**Status:** Functionally complete (v0.9.8+)

Minor formatting artifacts remain in a handful of class progression tables
(extra whitespace in cells, occasional cell-merge mis-detection). All values
are correct; only display is affected.

---

## Tooling & Process

### Code Complexity Technical Debt

**Date raised:** 2025-11-02 · **Status:** Bypassed with `# noqa: PLR0913` etc.

Several parser functions exceed Ruff's complexity / argument-count thresholds
and carry suppression comments. Worth a focused refactor pass before v1.0 —
particularly around `build()` in [build.py](../src/srd_builder/build.py) and
the larger parsers.

### Ruff Configuration Migration

**Status:** Deprecated config format still in use

`pyproject.toml` still uses the older Ruff `[tool.ruff]` style for some
settings. Migrate to the newer `[tool.ruff.lint]` layout when convenient.

### DATA_DICTIONARY.md: Auto-Generation vs Manual Curation

**Status:** Open question

Two approaches coexist: `scripts/generate_data_dictionary.py` auto-generates
basic field docs from schemas; the manual `docs/DATA_DICTIONARY.md` adds
narrative context. Pick one (or formalize the split) before v1.0.

### Test Fixture Refactoring

**Date raised:** 2025-12-21 · **Status:** Nice-to-have

Several golden tests embed fixtures inline rather than under `tests/fixtures/`.
Inconsistent. Worth normalizing during the v1.0 polish pass.

### JSON Field Ordering & Consistency

**Status:** Low priority

Dataset shapes are inconsistent: most use `{"_meta": ..., "items": [...]}` but
`conditions`, `diseases`, and `features` use the dataset name as the array key
(e.g. `{"conditions": [...]}`). The inventory builder handles both. Worth
standardizing on `items` everywhere as a v1.0 polish item — but it's a
breaking change for any consumer that hardcodes the legacy keys.

### Index.json Quality Enhancements

**Date raised:** 2025-12-21 · **Status:** Functional, could be improved

Open items: tighter alias scoring, ranked search results, per-dataset
sub-indexes for very large datasets (monsters, spells). All optional.

---

## Adding to This List

Keep entries short and use the structure above:

```markdown
### <Topic>

**Date raised:** YYYY-MM-DD · **Status:** <one-line>

Why it matters in ~2 paragraphs. Optional bullet list of options.
```

When an item is completed, move its full history block into
`archive/docs/PARKING_LOT_2025-pre-v0.23.md` (or a new archive file) and delete
it from this document. The point of this file is "what's still on deck", not
"everything we've ever thought about."
