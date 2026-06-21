# SRD Builder Forensic Audit

Audit date: 2026-06-20. Scope: current checked-out branch `work` at `82345c2`. Main branch, remote CI, open PRs, and issues could not be verified locally because this checkout has no configured remote and `gh` is not installed.

## Executive Assessment

- **Current maturity:** useful but not release-stable. The repository contains a credible SRD 5.1 PDF-to-JSON pipeline, schemas, docs, provenance controls, and many regression tests. However, the current environment can produce a misleading partial bundle when the source PDF is absent, and the default test suite currently fails.
- **Progressing or circling:** recent history is mixed. v0.27.x–v0.30.0 work retired manual data and fixed structural output issues: meaningful progress. v0.31.0–v0.37.0 was largely lifecycle cleanup with acknowledged minimal capability gain. The current branch resumes useful consolidation by binding several extractors to shared pattern engines, but the dominant risk is now data correctness/reproducibility rather than further abstraction.
- **Three most important conclusions:**
  1. The build command can exit successfully with only 48 static items and empty core datasets when no PDF is present, while validation and cross-reference checks still pass.
  2. Documentation overstates current reproducibility and output guarantees: README, ROADMAP, ARCHITECTURE, Makefile, and release-check disagree on commands, paths, counts, and schema state.
  3. The shortest path forward is not another broad refactor; it is to make incomplete builds impossible to mistake for distributable artifacts, then pin representative record-level correctness against real generated output.
- **Recommended immediate decision:** decide whether `make bundle` without `rulesets/srd_5_1/SRD_CC_v5.1.pdf` is a supported partial developer build or a hard error. For release/default bundle, it should be a hard error.

## System and Data-Flow Map

### Current architecture

- `src/srd_builder/build.py` is the I/O orchestrator: it writes `build_report.json`, invokes extraction, parses raw data, postprocesses records, builds indexes, validates references, writes `meta.json`, and optionally copies bundle collateral.
- `extract/` has two layers: a table extraction engine and per-dataset PDF extractors. The current branch has a split `extract/patterns/` package with dispatch plus pattern modules.
- `parse/` maps raw extraction payloads to structured records; there is no parse engine.
- `postprocess/engine.py` normalizes 12 simple datasets from declarative `DATASET_CONFIGS`; monsters, equipment, spells, and rules remain custom because they carry domain-specific logic or extra kwargs.
- `assemble/` builds equipment from tables/prose and creates indexes/cross-reference indexes.
- `utils/metadata.py` owns `_meta` blocks, schema lookup, inventory, page indexing, and ruleset source stamping.
- `schemas/` defines per-record JSON Schemas; collection envelopes are only partly validated by tests/build helpers.

### End-to-end data lineage

1. Source PDF expected at `rulesets/srd_5_1/SRD_CC_v5.1.pdf`.
2. Build creates `dist/<ruleset>/` and `rulesets/<ruleset>/raw/`.
3. Extractors write `*_raw.json` intermediates for monsters, equipment, spells, magic items, rules, and tables when a PDF is available.
4. Parsed records are produced by dataset-specific parsers.
5. Postprocess applies record normalization via custom cleaners or `clean_records()`.
6. `_write_datasets()` wraps records with `_meta`, writes dataset JSON, builds `index.json`, and runs cross-reference validation.
7. `generate_meta_json()` writes bundle metadata after datasets are already written.
8. `--bundle` copies schemas, exemplars, docs, and writes a generated bundle README.

### Major ownership boundaries

- Source identity and ruleset registry: `constants.py`.
- Build orchestration and distribution shape: `build.py`.
- Record provenance and metadata: `utils/metadata.py`.
- Schema validation: `utils/validate.py`, plus tests.
- Manual/derived data governance: `docs/PROVENANCE.md` and `tests/test_pdf_provenance.py`.

## Findings

### Critical

#### F-CRIT-001 — Successful builds can silently ship empty core datasets

- **Evidence:** `_extract_raw_monsters()` prints `No PDF found; extraction will skip.` and returns `None` when no PDF exists; analogous extractors return `None` or swallow exceptions for equipment, spells, magic items, rules, and tables. `build()` continues and writes datasets regardless. `_write_datasets()` always writes empty `monsters.json`, `spells.json`, and `magic_items.json` when inputs are absent. Cross-reference validation is informational only when it fails, and passes on empty datasets.
- **Observed behavior:** `PYTHONPATH=src python -m srd_builder.build --ruleset srd_5_1 --out dist --bundle` completed with no source PDF and produced only 7 dataset JSON files: 6 ability scores, 13 damage types, 18 skills, 11 weapon properties, and empty monsters/spells/magic_items.
- **Why it matters:** a consumer or release process can receive a structurally valid but substantively empty bundle.
- **User/data impact:** missing monsters, spells, equipment, classes, lineages, tables, features, rules, poisons, conditions, and diseases may appear as an intentional valid build.
- **Root cause:** extraction absence is modeled as optional input rather than an invalid release condition; validators focus on schemas and references, not minimum completeness.
- **Recommended disposition:** fix.
- **Smallest useful corrective action:** make `--bundle` fail if the source PDF is absent or if `meta.json` inventory does not meet explicit minimum counts for release datasets.
- **Confidence:** high.

#### F-CRIT-002 — Default test suite fails in the audited checkout

- **Evidence:** `pytest -q` failed with missing PDF errors from extractor tests that assert `rulesets/srd_5_1/SRD_CC_v5.1.pdf` exists, and with version tests reading `__version__ == "0.0.0+unknown"` from an uninstalled source checkout.
- **Observed behavior:** lint, format, and mypy passed; pytest failed with many PDF-dependent errors and 5 explicit failures.
- **Why it matters:** the documented local and CI gate is not currently green in this checkout without installation/source PDF handling alignment.
- **User/data impact:** developers cannot tell whether failures reflect regressions or environment setup; CI reliability depends on details not reproduced by `pytest -q` locally.
- **Root cause:** some PDF tests assert on missing PDF while other PDF tests skip; version tests assume editable installation metadata is present.
- **Recommended disposition:** fix.
- **Smallest useful corrective action:** standardize PDF-dependent tests to skip or mark as package/source-required, and ensure documented local commands include editable install or a source fallback version policy.
- **Confidence:** high.

#### F-CRIT-003 — Validation can pass empty or partial outputs

- **Evidence:** `validate_dataset()` returns 0 and skips missing dataset files; it validates only records present under `items`, not required dataset presence or minimum counts. `check_data_quality()` currently checks only spell description emptiness and duplicate equipment rarity index entries. `_check_pdf_hash()` prints `PDF/hash not present — OK for v0.2.0.` when no source exists.
- **Observed behavior:** after a no-PDF partial build, cross-reference validation printed success and schema validation would validate zero core records.
- **Why it matters:** passing validation is being conflated with correctness.
- **User/data impact:** incomplete outputs can satisfy the toolchain and downstream trust signals.
- **Root cause:** validators are schema-shape gates rather than release-quality gates.
- **Recommended disposition:** fix.
- **Smallest useful corrective action:** add a release validation mode that enforces all expected dataset files, minimum counts, non-empty core datasets, PDF hash presence, and known-truth records.
- **Confidence:** high.

### High

#### F-HIGH-001 — Documentation and build commands conflict

- **Evidence:** README tells users to run `make build`, but Makefile has `output` and `bundle` targets, not `build`. README says output lands in `dist/srd_5_1/` and lists `quality_report.json`, but the build path observed did not create that file. ROADMAP still describes old paths such as `dist/<ruleset>/data/monsters.json` and `rulesets/<ruleset>/raw/*.pdf`, while current code expects the PDF directly under `rulesets/<ruleset>/` and creates `raw/` for generated intermediates.
- **Observed behavior:** command/path drift makes onboarding and release instructions unreliable.
- **Why it matters:** reproducibility is a primary project claim.
- **User/data impact:** users may run wrong commands or misinterpret partial outputs.
- **Root cause:** documentation is release-narrative-heavy and not continuously tested against commands.
- **Recommended disposition:** consolidate/document.
- **Smallest useful corrective action:** make README command block, Makefile targets, and current build path agree; move stale historical roadmap sections under archive or mark them historical.
- **Confidence:** high.

#### F-HIGH-002 — Recent work contains meaningful refactoring but limited capability advancement

- **Evidence:** git history immediately before the audit includes many refactor/docs commits: PDF primitive lifting, pattern splitting, engine binding, and architecture notes. ROADMAP itself says v0.33.0–v0.37.0 were lifecycle-only swaps and did not advance engine binding.
- **Observed behavior:** current branch has real consolidation after v0.37.0, but little evidence of new data coverage or downstream Blackmoor-facing capability.
- **Why it matters:** the user's concern about cleanup churn is substantially valid.
- **User/data impact:** engineering time may reduce code size without improving correctness or usable artifacts.
- **Root cause:** acceptance criteria are framed around byte-identical refactors rather than release-quality data outcomes.
- **Recommended disposition:** document and redirect.
- **Smallest useful corrective action:** freeze architecture cleanup unless it removes an active correctness/reproducibility blocker; define next milestone by output completeness/quality gates.
- **Confidence:** high.

#### F-HIGH-003 — CI configuration masks type-check failure and cannot include the source PDF

- **Evidence:** CI runs Python 3.14, installs editable package, runs ruff, format, mypy with `continue-on-error: true`, and pytest. CI also forbids committed SRD PDFs/TXT under `rulesets/`.
- **Observed behavior:** CI cannot exercise full PDF extraction unless it obtains a PDF another way; type failures would not block.
- **Why it matters:** full extraction correctness is the core product, but CI is structurally biased toward fixture/unit coverage.
- **User/data impact:** regressions in PDF-only paths may escape unless local release checks are run manually.
- **Root cause:** licensing/source-document constraints plus CI gate design.
- **Recommended disposition:** document/fix.
- **Smallest useful corrective action:** split CI into mandatory no-PDF unit checks and documented release-only PDF checks; remove `continue-on-error` once mypy is intended as a gate, or label it advisory.
- **Confidence:** medium-high.

#### F-HIGH-004 — Provenance is much improved but consumer artifact lineage remains incomplete for partial builds

- **Evidence:** PROVENANCE has a detailed registry for retired manual sources and live augmentations. `_meta` can include `pdf_sha256`, item counts, source pages, and extraction warnings, but those fields are only populated when inputs/records exist. Build report always includes a timestamp and builder version, but in this source checkout the version fallback is `0.0.0+unknown`.
- **Observed behavior:** no-PDF bundle has no PDF hash and no useful extraction lineage while still being generated.
- **Why it matters:** consumers need to know which source and pipeline produced artifacts.
- **User/data impact:** a partial artifact can look official but lacks source hash and completeness guarantees.
- **Root cause:** provenance fields are optional in the same mode used for bundle generation.
- **Recommended disposition:** fix.
- **Smallest useful corrective action:** require `pdf_sha256`, expected inventory, and non-unknown builder version for release/bundle mode.
- **Confidence:** high.

### Medium

#### F-MED-001 — Two active source-location conventions create ambiguity

- **Evidence:** constants say the expected raw PDF is `rulesets/<id>/<pdf_filename>`. README says to place the PDF at `rulesets/srd_5_1/SRD_CC_v5.1.pdf` and says `raw/` is for intermediates. ROADMAP says source PDFs belong under `rulesets/<ruleset>/raw/*.pdf`.
- **Observed behavior:** old docs and validation helpers still look under `raw/` for PDF hash validation, while build extraction looks under the ruleset root.
- **Why it matters:** a user can place the PDF where older docs say and get empty builds.
- **User/data impact:** avoidable partial-output failures.
- **Root cause:** migration from raw-PDF directory to generated-raw directory was not fully reflected.
- **Recommended disposition:** consolidate.
- **Smallest useful corrective action:** one canonical source-PDF path; validation should check the same path as build.
- **Confidence:** high.

#### F-MED-002 — Release-check script is stale relative to current output shape/counts

- **Evidence:** `scripts/release_check.sh` expects equipment 258, tables 38, features under `features`, conditions under `conditions`, and only a subset of datasets. Current README says equipment 259, tables 35, and output keys normalized to `items`.
- **Observed behavior:** documented deterministic gate likely fails or skips meaningful current invariants depending on generated files and `jq` availability.
- **Why it matters:** release validation is the place where partial/incorrect output should be caught.
- **User/data impact:** stale checks provide false confidence or false failures.
- **Root cause:** release gate was not updated with v0.30.0 output normalization and count changes.
- **Recommended disposition:** fix.
- **Smallest useful corrective action:** derive expected counts from a reviewed manifest or update hardcoded counts/keys for all 16 datasets.
- **Confidence:** high.

#### F-MED-003 — Generic postprocess engine mutates inputs in place

- **Evidence:** `clean_record()` documents that it mutates in place and returns the same record.
- **Observed behavior:** current build passes freshly parsed records, so this is probably safe now, but it is a hidden side effect at a module boundary claiming pure normalization.
- **Why it matters:** future reuse in tests or multi-output builds can create order-dependent results.
- **User/data impact:** difficult-to-diagnose data drift if raw parsed records are reused after cleaning.
- **Root cause:** convenience-oriented engine implementation.
- **Recommended disposition:** accept short term, document; fix only if reuse bugs appear.
- **Smallest useful corrective action:** document ownership contract: callers must treat records as consumed by postprocess.
- **Confidence:** medium.

#### F-MED-004 — Partial exception swallowing can hide dataset regressions

- **Evidence:** equipment, spell, magic item, rules, table, lineage, class, spell-class, feature, prose, metadata, and poison extraction/parsing paths catch `Exception`, print a warning, and continue.
- **Observed behavior:** a broken extractor can downgrade output to missing/empty data without failing the build.
- **Why it matters:** correctness failures become warnings in production bundle mode.
- **User/data impact:** incomplete artifacts can be distributed.
- **Root cause:** local iteration resiliency and production release semantics share one build mode.
- **Recommended disposition:** fix for release, accept for dev.
- **Smallest useful corrective action:** add `--allow-partial` for developer builds; default `--bundle` should raise on extraction/parsing failure.
- **Confidence:** high.

#### F-MED-005 — Data checks inspect generated artifacts insufficiently

- **Evidence:** `check_data_quality()` only checks spell descriptions and duplicate equipment rarity index entries. Many critical dimensions requested by docs—counts, referential integrity, page provenance, malformed values—are spread across scripts/tests and not guaranteed by `utils.validate`.
- **Observed behavior:** generated no-PDF artifacts pass the available reference validation.
- **Why it matters:** malformed but schema-valid content can pass.
- **User/data impact:** consumers receive bad values with valid schemas.
- **Root cause:** schema validation is not complemented by comprehensive semantic validation.
- **Recommended disposition:** fix incrementally.
- **Smallest useful corrective action:** promote a small known-truth gate for one representative record per critical dataset into release validation.
- **Confidence:** high.

### Low

#### F-LOW-001 — Architecture docs still describe legacy monolithic datasets

- **Evidence:** ARCHITECTURE says magic_items and tables are monolithic and that magic_items reimplements `normalize_id()`, but current build uses `clean_records(magic_items, "magic_item")` and `clean_records(tables, "table")`.
- **Observed behavior:** docs understate completed postprocess consolidation.
- **Why it matters:** contributors may solve already-solved problems.
- **User/data impact:** wasted cleanup work.
- **Root cause:** docs evolved additively rather than replacing obsolete sections.
- **Recommended disposition:** document.
- **Smallest useful corrective action:** mark historical notes as historical or remove contradicted migration guidance.
- **Confidence:** high.

#### F-LOW-002 — Main/remote PR and issue state not auditable in this checkout

- **Evidence:** `git remote -v` produced no remotes; `gh pr list` and `gh issue list` failed because `gh` is not installed.
- **Observed behavior:** open PRs/issues and hosted CI could not be inspected.
- **Why it matters:** audit cannot confirm repository-level delivery hygiene outside local history.
- **User/data impact:** unknown issue/PR backlog risk.
- **Root cause:** local environment limitation.
- **Recommended disposition:** document.
- **Smallest useful corrective action:** repeat this portion in an environment with GitHub remote metadata and CLI/API access.
- **Confidence:** high.

## Duplication Inventory

| Cluster | Implementations involved | Behavior differs? | Recommended canonical owner | Consolidation risk |
| --- | --- | --- | --- | --- |
| Extraction absence/exception handling | `_extract_raw_*` helpers and inline PDF-only sections in `build.py` | Yes: some print, some silently return, some catch broad exceptions | `build.py` build-mode policy helper | Low-medium; semantics change if made strict |
| PDF source path policy | `constants.RULESETS[*].pdf_filename`, README, ROADMAP, `utils.validate._check_pdf_hash()` | Yes: ruleset root vs `raw/` | `constants.RULESETS` plus one path resolver | Low |
| Dataset write/wrap path | Mostly `_write_datasets()` now; historical docs still describe prose/simple divergence | Code largely unified, docs differ | `_write_datasets()` | Low |
| Record normalization | `postprocess/engine.py` for 12 datasets; custom modules for monsters/equipment/spells/rules | Legitimately differs for domain logic/kwargs | Keep current split | Medium if forced into abstraction |
| Release expected counts | README table, ARCHITECTURE table, release_check hardcoded counts, generated `meta.json` | Yes | generated `meta.json` plus reviewed release manifest | Low |
| Schema validation entrypoints | `utils/validate.py`, tests, scripts/release_check.sh, CI pytest | Yes: different coverage and requiredness | release validation command | Medium |
| Historical/manual provenance narratives | PROVENANCE, ROADMAP release log, test snapshots | Mostly consistent but verbose/duplicated | PROVENANCE for current state; archive release narrative | Low |

## Data Quality and Governance Assessment

| Control | Current state | Evidence | Risk | Recommended minimum standard |
| --- | --- | --- | --- | --- |
| Source acquisition | PDF not committed; expected path is ruleset root; no automated fetch | README and constants agree on root path; CI forbids committed PDFs | Missing PDF creates partial success | Bundle/release requires source PDF and hash |
| Source version | `RULESETS` records `source_id`, version, filename | `constants.py` registry | Single ruleset only; future support speculative | One registry entry per source with source URL/license/checksum |
| Checksums | `pdf_sha256` can be stamped; no-PDF output lacks it | `_meta` optional `pdf_sha256`; build reads `pdf_meta.json` | Consumers cannot verify source | Release artifacts must include PDF hash in `meta.json` and each dataset `_meta` |
| Retrieval date | Not clearly recorded deterministically | build report has timestamp only | Timestamps are nondeterministic and not source retrieval | Record source publication/version, not build-time retrieval unless in non-hashed report |
| Transformation lineage | Strong module-level separation; raw intermediates generated under `rulesets/<id>/raw` | build workflow | Partial outputs lack lineage | Keep raw extraction outputs for release or publish extract manifest |
| Manual corrections | Strong registry and reproducer discipline | PROVENANCE table and tests | Active augmentation still invented data | All invented records carry typed provenance and schema support |
| Schema ownership | Schemas exist per dataset | schemas + DATASET_TO_SCHEMA | Envelope validation incomplete | Validate full document envelope plus item records |
| Schema versioning | Present but docs drift | README/ARCHITECTURE/ROADMAP disagree | Consumers get stale version claims | Generate docs from schemas/meta where possible |
| Compatibility policy | Discussed in docs, not enforced | release notes/schema bumps | Breaking output can bypass migration docs | Release checklist must require migration note on major schema bumps |
| Determinism | Intended; release_check hashes excluding build_report | script excludes timestamp report | stale counts/keys undermine check | Determinism gate over all deterministic artifacts and all 16 datasets |
| Completeness | Claimed complete, but no-PDF build partial | observed generated dist | Critical | Minimum count manifest required in release mode |
| Referential integrity | Cross-reference validation exists | `validate_references()` called by build | Empty datasets trivially pass | Reference validation plus expected non-empty source sets |
| Consumer artifact identity | `_meta.generated_by` and build report | version fallback is unknown if not installed | Unknown builder version in local artifacts | release mode rejects `0.0.0+unknown` |

## Test and Tool Results

| Command | Result | Important output/warnings |
| --- | --- | --- |
| `python --version && ruff check .` | PASS | Python 3.14.4; all checks passed. |
| `ruff format --check .` | PASS | 183 files already formatted. |
| `mypy src` | PASS locally | Success: no issues found in 84 source files. CI treats mypy as advisory. |
| `pytest -q` | FAIL | Missing `rulesets/srd_5_1/SRD_CC_v5.1.pdf` caused extractor errors; version tests saw `0.0.0+unknown`; 5 failed plus many errors. |
| `python -m srd_builder.build --ruleset srd_5_1 --out dist --bundle` | FAIL | Module not found without editable install or `PYTHONPATH=src`. |
| `PYTHONPATH=src python -m srd_builder.build --ruleset srd_5_1 --out dist --bundle` | PASS with severe warning | Printed `No PDF found; extraction will skip`; generated a partial bundle and reported cross-references valid. |
| `gh pr list --state open --limit 20` | NOT RUN/UNAVAILABLE | `gh: command not found`. |
| `gh issue list --state open --limit 20` | NOT RUN/UNAVAILABLE | `gh: command not found`. |

### Coverage gaps

- Default pytest does not consistently skip source-PDF-required tests.
- Current generated artifacts are not fully validated for minimum counts or full envelope shape.
- Release checks are stale and cover only selected datasets.
- CI cannot verify PDF extraction unless a licensed source is supplied outside the repo.
- No remote PR/issue/CI state was accessible from this checkout.

## Progress Versus Churn

### Recent meaningful accomplishments

- Retired large hand-curated data surfaces with live extractors and reproducer-backed provenance.
- Normalized output keys and resolved duplicate IDs in v0.30.0.
- Consolidated 12 simple postprocess datasets behind `DATASET_CONFIGS` while preserving custom modules where warranted.
- Split a large extraction patterns module into a package and bound several font-walk extractors to shared engines on the current branch.

### Repeated or low-value work

- v0.31.0–v0.37.0 lifecycle-only PyMuPDF wrapper swaps did not materially advance capabilities.
- Multiple docs repeat release narratives and stale counts, creating more cleanup work.
- Further abstraction of one-caller monster logic would likely be churn unless it removes a correctness blocker.

### Decisions that need to be made once and recorded

1. Is a no-PDF build a supported partial dev mode or an invalid bundle/release?
2. What is the canonical source-PDF path?
3. What exact inventory/count manifest defines a complete SRD 5.1 release?
4. Which command is the authoritative release gate?
5. Is mypy advisory or blocking?

### Work that should stop

- Stop broad architecture cleanup that preserves byte-identical output but does not improve release correctness, provenance, or consumer usability.
- Stop adding release narrative to ROADMAP as a substitute for executable acceptance criteria.
- Stop treating schema validation of present records as evidence of dataset completeness.

## Recovery Plan

### Phase 0: decisions or containment

| Action | Outcome | Acceptance criteria | Dependencies | Scope |
| --- | --- | --- | --- | --- |
| Define release vs dev build semantics | No accidental partial bundles | `--bundle` without PDF fails unless `--allow-partial` is explicit | Decision on source PDF handling | Small |
| Canonicalize source PDF location | One path used everywhere | README, constants, validation, tests all reference same path | None | Small |
| Freeze nonessential refactors | Attention moves to correctness | New work must cite data/release acceptance criterion | Team agreement | Small |

### Phase 1: correctness and data integrity

| Action | Outcome | Acceptance criteria | Dependencies | Scope |
| --- | --- | --- | --- | --- |
| Add release completeness gate | Empty/partial artifacts fail | All 16 dataset files required; counts meet manifest; PDF hash present; builder version known | Phase 0 build semantics | Medium |
| Fix test environment split | Local/CI failures are interpretable | PDF-required tests skip/mark when PDF absent; installed/version tests documented | Source path decision | Medium |
| Update release_check | Determinism gate matches current output | Current counts/keys for all 16 datasets; known-truths run; no stale `features`/`conditions` keys | Completeness manifest | Small |
| Validate full envelopes | Schema-shape confidence improves | `_meta` and collection keys validated, not only item records | Schema decision | Medium |

### Phase 2: architectural consolidation

| Action | Outcome | Acceptance criteria | Dependencies | Scope |
| --- | --- | --- | --- | --- |
| Centralize extraction failure policy | No broad exception swallowing in release mode | One helper controls warn-vs-raise by mode | Phase 0 semantics | Medium |
| Remove stale architecture/doc contradictions | One current source of truth | ARCHITECTURE describes current postprocess/extract state only; historical notes archived | Phase 1 gates | Small |
| Keep monster bespoke unless second caller appears | Avoid abstraction churn | BACKLOG records decision and trigger | None | Small |

### Phase 3: capability advancement

| Action | Outcome | Acceptance criteria | Dependencies | Scope |
| --- | --- | --- | --- | --- |
| Blackmoor consumption contract | Output is usable downstream | Consumer can identify source, pipeline version, schema versions, counts, and IDs for every artifact | Phase 1 provenance gates | Medium |
| Next SRD ruleset feasibility spike | Multi-ruleset claim tested | One minimal alternate ruleset fixture exercises ID prefix/source registry without broad rewrite | Phase 2 cleanup | Large |
| Record-level semantic audits | Data correctness improves | Representative monster/spell/equipment/class/lineage records traced from PDF to final JSON | Phase 1 full build | Medium |

## Recommended Next Three Actions

1. **Make `--bundle` fail without the canonical source PDF and expected minimum inventory.** This produces immediate measurable progress by preventing false release artifacts.
2. **Repair the documented quality gate so `pytest -q`, release-check, and CI semantics are explicit and reproducible.** This turns current red tests into actionable signals instead of environmental noise.
3. **Run one full PDF-backed build and audit five representative records end-to-end into final JSON.** This directly addresses correctness and gives downstream consumers evidence beyond passing schemas.
