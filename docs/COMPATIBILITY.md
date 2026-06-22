# Compatibility policy

`srd-builder` ships a single semantic version (`builder_version`) that carries
**both** the extraction-behavior contract and the bundle envelope contract.
This document writes down what each bump level means for consumers.

It is the explicit policy that lets `builder_version` stand in for what would
otherwise need a separate `bundle_format_version`: there is one version
number, and renaming the dataset manifest is a MAJOR change to it.

## Pre-1.0 status

`srd-builder` is currently pre-1.0. Under semver, pre-1.0 explicitly allows
breaking changes to ship in any release including PATCH. We retain the
MAJOR/MINOR/PATCH framework below as the *intended* policy that will become
strict at v1.0.0, but pre-1.0 the rules carry the following carve-outs:

1. **Bundle artifact relocations** (e.g. moving `build_report.json` out of the
   bundle directory in v0.38.0) may ship in a MINOR release pre-1.0 with a
   release-note migration paragraph, instead of a MAJOR bump. This is the
   exception that applied to v0.38.0; it is recorded here explicitly so it
   is not a retroactive inference.
2. **Schema-tightening hardenings that close envelope shape** (e.g. setting
   `additionalProperties: false` on `meta.schema.json` top-level, removing
   `build.extracted_at` from the allowed properties, both shipped in v0.39.0)
   may ship in a MINOR release pre-1.0 with a release-note paragraph,
   because no producer or consumer is currently shipping those keys.
3. **Manifest renames** are still MAJOR, even pre-1.0. The cost to consumers
   of `files`\u2192`inventory`\u2192`datasets` is too high to silently absorb.
4. **Removing a required schema field** is still MAJOR even pre-1.0. A
   consumer reading the field will get a hard runtime error.

These carve-outs expire at v1.0.0. From v1.0.0 forward, the
MAJOR/MINOR/PATCH rules below are strict, and the only valid way to ship a
breaking change is a MAJOR bump.

Consumers integrating pre-1.0 SHOULD pin the exact `builder_version` they
tested against and re-test before adopting a new release, even within a
single MINOR cycle.

## Where `builder_version` is recorded

| Location | Field |
| --- | --- |
| `dist/srd_5_1/meta.json` | `builder_version` |
| `dist/srd_5_1/<dataset>.json` | `_meta.generated_by` (`"srd-builder v<X.Y.Z>"`) |
| `dist/build_report.json` | `builder_version` |

All three sites are written from `srd_builder.__version__`, which reads from
the installed package metadata (`pyproject.toml` is the single source of
truth). Consumers should treat `meta.json.builder_version` as the canonical
value.

## What changes at each level

### MAJOR (`X.0.0`) — breaking change

A consumer that has been working against version `X-1.Y.Z` is expected to
need code changes when moving to `X.0.0`.

Examples that REQUIRE a MAJOR bump:

- **Manifest renames** in `meta.json`. The dataset manifest has been called
  `files` (early), `inventory` (mid), and `datasets` (current). Renaming it
  again — or moving it under a parent key, or changing per-dataset entry
  shape from `{file, count, status}` — is MAJOR.
- **Removing a required field** from any shipped schema. If consumers can
  rely on a field being present, taking it away is breaking.
- **Narrowing an enum** in any shipped schema. If `category: 'consumable'`
  was previously valid for `equipment`, removing `'consumable'` from the
  enum is breaking.
- **Tightening a regex pattern** in a schema such that previously-valid
  records would now fail. Example: changing `simple_name` from
  `^[a-z][a-z0-9_]*$` to `^[a-z][a-z0-9]*$` (no underscores) would invalidate
  every record currently shipping with an underscore.
- **Changing field types.** `count: integer` becoming `count: string`. `page:
  oneOf integer|array` collapsing back to `page: integer`.
- **Moving artifacts within the bundle layout.** Example: moving
  `dist/srd_5_1/meta.json` to `dist/srd_5_1/_meta/meta.json` would break any
  consumer hard-coded to the current path. From v1.0.0 forward, the v0.38.0
  relocation of `build_report.json` from inside the bundle to alongside it
  would qualify as MAJOR. Pre-1.0, it shipped as MINOR under the carve-out
  documented in the *Pre-1.0 status* section above.
- **Removing a dataset** from the 16 currently shipped, or merging two
  datasets into one.

When a MAJOR change ships, the release notes ([README.md](../README.md),
[docs/ROADMAP.md](ROADMAP.md)) MUST include a migration note describing what
consumers need to change.

### MINOR (`0.Y.0`) — additive

A consumer that has been working against version `0.Y-1.Z` should NOT need
code changes when moving to `0.Y.0`. New surface may be available, but
nothing the consumer was already using is removed or changed.

Examples that fit MINOR:

- **Adding a new optional property** to a shipped schema. Example: v0.37.2
  adding `proficiency` and `capacity` as optional properties of
  `equipment.schema.json`.
- **Expanding an enum.** Example: v0.37.2 adding `vehicle`, `consumable`,
  `service` to `equipment.category`.
- **Relaxing a regex pattern** such that records valid under the old pattern
  remain valid under the new one (strict superset). Example: v0.37.2
  relaxing `rule.id` from `^rule:[a-z0-9_]+$` to
  `^rule:[a-z0-9_]+(/[a-z0-9_]+)*$`.
- **Adding a new dataset.** Existing 16 datasets unchanged; one new file
  appears in `meta.json.datasets` and the bundle directory. (Consumers
  iterating over `datasets` will see the new entry; consumers that ignore
  unknown datasets are unaffected.)
- **Renaming a schema field WHILE keeping the old one as a deprecated
  alias** for at least one MINOR cycle before removing in the next MAJOR.

### PATCH (`0.0.Z`) — data fix

A consumer that has been working against version `0.0.Z-1` should see
identical schema shape and identical envelope shape; only the content of
specific records may change to correct extraction or parsing bugs.

Examples that fit PATCH:

- **Fixing a parser bug** that was dropping data. Records re-appear or
  fields get populated correctly; schema is unchanged.
- **Correcting a cross-reference** that pointed at the wrong target.
- **Re-running extraction against a corrected source PDF** (`pdf_sha256`
  changes; everything else is regenerated).

## Why this is enough

The four artifacts below, together, prevent the failure mode that motivated
this policy (silent envelope renames):

| Artifact | What it guards |
| --- | --- |
| `schemas/meta.schema.json` | Top-level envelope shape, manifest key name, schemas map completeness, dataset entry shape |
| `schemas/build_report.schema.json` | Report shape with `additionalProperties: false` (catches new fields too) |
| `tests/test_meta_envelope_contract.py` | Runs both schemas against the actual built bundle; also guards specifically against the legacy `files`/`inventory` manifest names and against the `sha256:<hex>` prefix form being reintroduced |
| `docs/COMPATIBILITY.md` (this file) | Names the level a particular change must bump |

Any breaking change to the manifest, the envelope layout, or a shipped
schema MUST be accompanied by:

1. An update to `schemas/meta.schema.json` (or the relevant dataset schema)
   that reflects the new shape.
2. A MAJOR `builder_version` bump in `pyproject.toml`.
3. A migration note in the release section of [README.md](../README.md) and
   [docs/ROADMAP.md](ROADMAP.md) describing what consumers must change.

The envelope contract test will fail until step 1 is done. Step 2 is
caught by `tests/test_version_consistency.py`. Step 3 is caught at code
review.

## What this policy does NOT cover

- **Source PDF integrity.** Whether the PDF a particular build was made
  from matches a prior build is recorded in `meta.json.build.pdf_hash` and
  per-dataset `_meta.pdf_sha256`, but a change to the source document is
  not, in itself, a `builder_version` event — it's a data-content change
  with the next eligible bump level (typically PATCH).
- **Implementation details inside `src/srd_builder/`.** Refactoring an
  extractor or postprocess module does not require a version bump as long
  as the shipped output is byte-identical. Behavioral changes that alter
  output qualify under the rules above.
- **Test scaffolding, dev-only scripts, internal fixtures.** Not part of
  the consumer contract.
