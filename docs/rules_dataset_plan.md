# Rules Dataset Planning (Design-Only)

## Section 1 – Quick Repo Fit Summary
- Follows existing unified dataset pattern with `_meta` and `items[]`, preserving namespaced IDs (`rule:*`, `condition:*`, etc.) and `simple_name` normalization described in schema guidance.【F:docs/SCHEMAS.md†L17-L35】
- Slots into the established extract → parse → postprocess → index → validate pipeline used across datasets and expected by downstream consumers.【F:docs/ROADMAP.md†L10-L20】【F:docs/INTEGRATION.md†L60-L79】
- Ships alongside other bundle artifacts (`data/*.json`, schemas, index) to keep packaging consistent for consumers pulling the dist bundle.【F:docs/BUNDLE_README.md†L57-L80】
- Targets roadmap milestone for `rules.json` while keeping conditions as their own dataset and linking via namespaced IDs for cross-reference durability.【F:docs/ROADMAP.md†L61-L103】

## Section 2 – Codex’s Rules Plan
### Data Model (proposed schema skeleton)
- **Namespace:** `rule:*` with `_meta.schema_version` bump to 1.3.x minor if new optional fields are added; additive and backward compatible with existing patterns.
- **Core fields per item:** `{id, name, simple_name, category, subcategory?, parent_id?, page, src, text[], tags?, aliases?}` to mirror current entity consistency (`id`/`name`/`simple_name`, provenance fields, optional aliases) while keeping text as structured paragraphs.
- **Hierarchy:** `category` maps to chapter (e.g., Combat), `subcategory` to section (e.g., Actions in Combat); optional `parent_id` captures nesting without forcing deep trees in the consumer schema.
- **Cross-references:** Optional arrays of namespaced IDs (`related_conditions`, `related_spells`, `related_features`, `related_tables`) to link out rather than embed, aligning with existing dataset separation.
- **Mechanics (v1 scope):** No structured mechanics objects yet; preserve prose and lightweight tags (`action`, `bonus_action`, `movement`, `saving_throw`, `advantage`) to enable search without over-modeling.

### Files & Intermediate Products
- `rules_raw.json`: verbatim text blocks with font metadata (size, name, bold flag, page, bbox) extracted from SRD chapters slated for coverage.
- `rules_outline.json`: hierarchical outline recovered from header stack and relative font tiers; chapter → section → leaf topics with ordering and page anchors.
- `rules_postprocessed.json`: flattened, normalized entities with IDs, simple names, tags, cross-refs, and cleaned text arrays.
- `rules.json`: final distribution file with `_meta` and `items[]`, versioned alongside other datasets.

### Pipeline Responsibilities
- **extract_rules.py:** reuse PDF text extraction approach capturing font data to enable header tier reconstruction; limit scope to rules chapters to keep noise low.
- **parse_rules.py:** build outline tree using relative font levels and indentation/spacing; detect paragraphs vs headers; attach page provenance.
- **postprocess_rules.py:** normalize names, generate deterministic IDs/simple names, assign categories/subcategories, dedupe whitespace, inject light tags, and resolve cross-refs to existing datasets when available.
- **indexer.py:** extend existing index builder to add `rules` maps (by_name, by_category, by_tag) without altering other datasets.
- **validate.py:** add `rules.schema.json` and ensure deterministic outputs stay schema-compliant (no timestamps, stable ordering).

### Scope & Deferrals
- **Phase 1 (v0.16.0 target):** Core mechanics chapters: Using Ability Scores (ability checks/saves, proficiency bonus), Adventuring basics (resting, time, movement summaries), Combat (actions, attacks, advantage/disadvantage), Spellcasting fundamentals (casting steps, concentration).
- **Phase 2:** Integrate existing `conditions.json` cross-refs; add Appendix A conditions only via links, not embedding.
- **Phase 3:** Environment/Travel/Interaction rules and derived reference tables (mark `source: "calculated"` when not PDF-sourced).
- **Deferred:** Rich mechanics objects (action costs, speed modifiers), variant/optional rules, and automated cross-links to class/feature mechanics pending consumer feedback.

### ID & Naming Conventions
- IDs use `rule:<simple_name>` with hyphen/underscore normalization matching existing datasets; `simple_name` derived from lowercased, delimiter-normalized names.
- `category`/`subcategory` values mirror SRD headings; `parent_id` only used where SRD nesting is material to interpretation.
- `aliases` reserved for legacy/alternate terminology (e.g., “second wind” vs “Second Wind (fighter feature)” when context arises).

### Cross-Dataset Link Strategy
- Use namespaced IDs to reference conditions, spells, features, and tables; tolerate missing targets in early phases but structure fields now for later resolution.
- Indexer extends `entities` catalog so `rule:*` entries surface in unified lookups alongside existing entity metadata maps.

## Section 3 – Comparison Table
| Aspect | Gemini Proposal | ChatGPT (gAIa) Proposal | Codex Plan |
| --- | --- | --- | --- |
| Schema shape | Flattened `rules_postprocessed.json` with slugs/tags/mechanics; hierarchy implied | New `rule:*` namespace with `_meta` + `items[]`, category/subcategory/parent_id, tags, cross-refs | `rule:*` namespace with `_meta` + `items[]`, category/subcategory/parent_id, tags, cross-refs; mechanics deferred |
| Use of font metadata | Extracts font size/bold/page to rebuild header stack | Uses relative font tiers and header stack to build tree | Same: rely on font metadata with relative tiers to build `rules_outline.json` |
| Treatment of conditions | Allows condition embedding/cross-refs in rules | Conditions split into `conditions.json`; rules reference `condition:*` IDs | Keep `conditions.json` separate; rules reference via namespaced IDs |
| Mechanics modeling v1 | Optional mechanics objects per rule | Tags only; optional future mechanics | Tags only in v1; mechanics objects deferred |
| Phasing/priorities | Core chapters (abilities, time/movement, environment, resting, combat, spellcasting, conditions) | Phase 1: Combat & Spellcasting focus; Phase 2: conditions dataset; Phase 3: Adventuring/Environment | Phase 1: core mechanics (abilities, adventuring basics, combat, spellcasting); Phase 2: condition cross-links; Phase 3: environment/travel and derived tables |

## Section 4 – Final Recommendation
The project should adopt the Codex plan with a `rule:*` namespace, adhering to the existing `_meta` + `items[]` schema and the standard extraction→parsing→postprocess pipeline. Initial focus should capture high-value mechanical chapters (ability checks/saves, movement/resting basics, combat flow, spellcasting) with prose-first representation plus lightweight tags. Conditions remain a standalone dataset, referenced via IDs, keeping schemas loosely coupled and consumer-friendly.

**Implementation checklist:**
- Add `schemas/rule.schema.json` aligned with `{id, name, simple_name, category, subcategory?, parent_id?, page, src, text[], tags?, aliases?, related_*?}`.
- Implement `extract_rules.py`, `parse_rules.py`, and `postprocess_rules.py` to produce `rules_raw.json`, `rules_outline.json`, and `rules_postprocessed.json` ahead of final `rules.json` export.
- Extend `indexer.py` to generate rule lookups and register entities in unified indexes.
- Stage phased coverage (core mechanics → condition linking → environment/derived rules) while keeping mechanics modeling minimal until consumer signals demand richer structures.
