# srd-builder v0.37.0 Consumer Integration Review

## Outcome

The imported bundle is a complete, content-equivalent copy of the archived
`srd-builder` v0.37.0 bundle. Blackmoor can load it and serve its existing SRD
API surfaces successfully.

The bundle is structurally consistent: all 16 datasets exist, all 1,687
manifest entries are present, dataset envelope counts agree with the manifest,
IDs are unique within and across datasets, and every dataset advertises
`srd-builder v0.37.0`.

The canonical consumer location and loading behavior are documented in the
[ruleset README](../../../rulesets/srd_5_1/README.md). Bundle metadata is
defined by [`meta.json`](../../../rulesets/srd_5_1/data/meta.json).

## Blackmoor Integration Change

The [producer migration guide](../MIGRATION_v0.18.1_to_v0.37.0.md) confirms that
the normalized `items` envelope, owner-qualified feature IDs, underscore-only
equipment IDs, and consolidated `datasets` manifest are intentional breaking
changes.

Blackmoor's immediately preceding bundle was v0.23.0, whose `meta.json`
contained a real top-level `inventory` count map in addition to `files` and
`extraction_status`. Version 0.37.0 replaces those blocks with per-dataset
records under `datasets`. Blackmoor's loader and API behavior did not depend on
the removed keys, but two test helpers did. Those helpers now read
`datasets.<name>.count`.

The consumer contract test in
[`tests/test_srd_bundle_contract.py`](../../../tests/test_srd_bundle_contract.py)
now checks:

- declared dataset files and completion status;
- manifest, envelope, and actual item counts;
- manifest and envelope schema versions;
- builder and ruleset identity;
- unique IDs within and across datasets.

## Migration Guide Reconciliation

The guide usefully explains the intended direction, but it is not yet a
complete or artifact-verified consumer manifest. Direct comparison of the
archived v0.18.1 and v0.37.0 bundles found these discrepancies:

| Guide claim | Archived artifact evidence | Consumer feedback |
| --- | --- | --- |
| `inventory` was never a real `meta.json` key. | The Blackmoor v0.23.0 bundle contains `inventory`. | Describe intermediate manifest versions, not only the two endpoints. |
| 39 duplicate feature IDs were eliminated. | v0.18.1 has 16 distinct repeated IDs representing 86 duplicate records; features change from 246 records/160 unique IDs to 245 unique owner-qualified IDs. | Define whether a count means repeated names, duplicate records, renamed IDs, or resulting IDs. |
| 126 equipment IDs were renamed. | 125 existing IDs map through the hyphen-to-underscore rewrite; v0.37.0 also adds one equipment record, producing 126 newly seen IDs. | Separate renames from additions. |
| Five new datasets shipped after v0.18.1. | Four files are new: ability scores, damage types, skills, and weapon properties. `rules.json` already exists in v0.18.1 with 172 items but is omitted from that manifest; v0.37.0 declares 167 rules. | Characterize rules as newly manifest-declared and revised, not as a new file. |
| All 11 v0.18.1 schemas were present and survived. | The v0.18.1 manifest declares 11 schema versions, but the archive contains only eight schema files; disease, poison, and magic-item schemas are absent. | Distinguish manifest declarations from shipped files and report missing artifacts. |
| `quality_report.json` ships in the v0.37.0 bundle. | It is absent from the archived and imported v0.37.0 file inventories. | Generate the artifact or remove the claim. |
| `docs/DATA_DICTIONARY.md` and `docs/SCHEMAS.md` are new bundle artifacts after v0.18.1. | Both files are already present in the archived v0.18.1 bundle. | Derive the added-file list from the archived bundles. |
| Every other consumer-facing change is enumerated. | The guide omits removed `summary` fields, the `lineage:lightfoot_halfling` to `lineage:lightfoot` rename, rule count/ID changes, and table count/ID changes. | Generate field, ID, and count deltas from release artifacts. |
| Exemplars are the ground-truth loader shape. | Exemplars validate, but 491 real emitted items fail the same shipped schemas. | Validate the complete datasets; exemplars are examples, not proof of bundle conformance. |

The guide's relative release-note links also do not resolve from its downstream
location in Blackmoor. A consumer migration artifact should use portable links
to canonical release notes or include the referenced material in the bundle.

## Upstream Schema Gaps

Strict validation of every item against the JSON Schemas shipped in the same
bundle finds 491 invalid items across seven datasets. This is an upstream bundle
issue, not a copy or Blackmoor transformation issue.

| Dataset | Invalid items | Primary contradictions |
| --- | ---: | --- |
| Classes | 8 | Abbreviated spellcasting abilities are rejected by the schema enum. |
| Damage types | 13 | Data uses `damage:` IDs; the schema requires `damage_type:`. |
| Equipment | 257 | Common emitted fields and categories are rejected; many `simple_name` values fail the schema pattern. |
| Monsters | 8 | Empty description fragments and a negative damage modifier fail schema constraints. |
| Poisons | 14 | Required/type rules disagree with emitted poison fields, page arrays, and damage IDs. |
| Rules | 167 | Hierarchical rule IDs containing `/` are rejected by the ID pattern. |
| Tables | 24 | Emitted categories and metadata are rejected by the schema. |

The bundle README's statement that all datasets are validated against the
shipped schemas is therefore not currently true for v0.37.0.

## Producer Requirements

Future `srd-builder` bundles should meet these requirements before Blackmoor
treats strict schema validation as an acceptance gate:

1. Validate every emitted item against the exact schema files included in the
   bundle as part of producer CI.
2. Fail the producer build when data and schemas disagree; schema validity
   and exemplar validity alone are insufficient.
3. Version the `meta.json` manifest shape or publish migration notes whenever
   keys such as `inventory` are removed or replaced.
4. Keep ID namespaces and patterns consistent across datasets, schemas, and
   cross-references.
5. Emit a machine-readable validation summary containing dataset, item ID,
   schema version, and error path.
6. Reconcile the reproducible-build claim with the timestamp and local Python
   version currently emitted in `build_report.json`, which are nondeterministic
   or environment-dependent values.
7. Generate and test migration manifests against both archived endpoint
   bundles, including field removals, ID renames, additions, removals, and count
   changes.
8. Ensure every artifact and link named by a migration guide is present or
   resolves to a canonical source.

## Consumer Policy

Blackmoor should preserve imported bundles as producer-owned artifacts, adapt
only its consumer code and tests, and record producer defects rather than
silently normalizing generated data. A future refresh should run, in order:

1. file-inventory and content comparison with the selected producer release;
2. the Blackmoor bundle contract test;
3. strict item validation against shipped schemas;
4. loader and SRD API tests;
5. the full repository verification suite.

Strict schema validation remains a reported upstream gap for v0.37.0. It should
be promoted to a required Blackmoor acceptance test once the producer bundle is
self-consistent and the validator is an approved project dependency.
