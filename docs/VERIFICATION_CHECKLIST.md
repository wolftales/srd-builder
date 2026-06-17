# Build Verification Checklist (Producers / Maintainers)

This is the **maintainer-facing** checklist for validating a srd-builder bundle before tagging a release. It assumes you have a working dev environment (`make init`) and the SRD PDF in place.

> Looking for *consumer-side* integration guidance? See [docs/INTEGRATION.md](docs/INTEGRATION.md).

---

## Quick Verification (Development)

For development work and small changes:

```bash
# 1. Run golden dataset tests (16 datasets)
pytest tests/test_golden_*.py -v

# 2. Code quality
ruff check . && ruff format --check .

# 3. Spot-check one dataset
jq '._meta' dist/srd_5_1/monsters.json
```

**Expected:** all golden tests pass, ruff clean, `_meta` block looks right.

---

## Complete Verification (Pre-Release)

For refactors, major changes, and any tagged release.

### 1. Build the bundle

```bash
make bundle
```

This runs the full pipeline and writes `dist/srd_5_1/` (16 datasets + manifest + schemas + docs).

### 2. Smoke-check the bundle

```bash
./scripts/smoke.sh srd_5_1 dist bundle
```

This script checks file presence and basic structural assertions. Exit code 0 = pass.

### 3. Verify bundle contents match `meta.json`

The bundle should be self-describing. **Always trust `meta.json` over hard-coded expectations** — if the inventory grew, fix the checklist, not the bundle.

```bash
# Show what shipped
jq '.inventory' dist/srd_5_1/meta.json
jq '.schemas | keys' dist/srd_5_1/meta.json
jq '.files | keys' dist/srd_5_1/meta.json
```

**Expected bundle structure (v0.23.0 baseline):**

```
dist/srd_5_1/
├── README.md              (generated from meta.json)
├── meta.json              (inventory + schemas + files manifest)
├── index.json             (cross-dataset lookups)
├── build_report.json      (per-stage stats)
├── *.json                 (16 dataset files)
├── schemas/*.schema.json  (16 schema files)
└── docs/*.md              (2 docs: DATA_DICTIONARY.md, SCHEMAS.md)
```

**Datasets shipped (16):** ability_scores, classes, conditions, damage_types, diseases, equipment, features, lineages, magic_items, monsters, poisons, rules, skills, spells, tables, weapon_properties.

**Schemas shipped (16):** one `.schema.json` per dataset. (`madness.schema.json` was removed in v0.23.0 — madness data lives in `tables.json`.)

### 4. Inventory cross-check (new in v0.23.0)

The `meta.json.datasets` block has a per-dataset entry of the form
`{file, count, status}`. Compare the declared `count` against what's actually in each JSON file:

```bash
# Compare meta.json datasets[*].count against actual item counts
python3 - <<'PY'
import json, sys
from pathlib import Path

meta = json.load(open("dist/srd_5_1/meta.json"))
datasets = meta["datasets"]
fail = False
for dataset, entry in sorted(datasets.items()):
    expected = entry["count"]
    path = Path("dist/srd_5_1") / entry["file"]
    doc = json.load(open(path))
    actual = len(doc.get("items") or doc.get(dataset, []))
    status = "OK" if actual == expected else "MISMATCH"
    if status == "MISMATCH":
        fail = True
    print(f"  {dataset:22s} expected={expected:4d} actual={actual:4d}  {status}")
sys.exit(1 if fail else 0)
PY
```

**Expected:** every dataset reports `OK`. A mismatch means either `build_inventory()` miscounted or the dataset has the wrong shape.

### 5. Schema validation

Validate every dataset against its shipped schema. Driven by `meta.json` so this stays correct as datasets are added:

```bash
python3 - <<'PY'
import json, subprocess, sys
from pathlib import Path

meta = json.load(open("dist/srd_5_1/meta.json"))
root = Path("dist/srd_5_1")
fail = False
for dataset, entry in sorted(meta["schemas"].items()):
    schema = root / entry["file"]
    data   = root / meta["datasets"][dataset]["file"]
    rc = subprocess.call(["check-jsonschema", "--schemafile", str(schema), str(data)])
    if rc != 0:
        fail = True
sys.exit(1 if fail else 0)
PY
```

Requires `pip install check-jsonschema`. Exit code 0 = every dataset valid.

### 6. Full test suite

```bash
pytest -q
```

**Baseline (v0.23.0):** 292 passing, 19 skipped (skips are environment-gated, e.g. tests that need the actual SRD PDF). Any new failure on green main is a regression.

### 7. Golden tests

```bash
pytest tests/test_golden_*.py -v
```

**Baseline:** 16 golden tests (one per dataset), all passing. These compare a parse-and-postprocess run against committed normalized fixtures. A failure here means either the parser changed (intentional → update fixture via `python scripts/bump_version.py`) or there's a regression.

### 8. Code quality

```bash
# In dev (pre-commit installed)
pre-commit run -a

# In CI / containers
ruff check .
ruff format --check .
pytest -q
```

All must pass. Pre-commit also runs `pretty-format-json` (excludes `tests/fixtures/.*/normalized/` and `archive/dist_versions/.*` to preserve curly quotes in snapshots).

---

## Regression Testing (Baseline Comparison)

For major refactors, compare output against a known-good baseline:

```bash
# Before refactor
make bundle
cp -R dist/srd_5_1 /tmp/baseline_srd_5_1

# ... do the refactor ...

# After refactor
make bundle
diff -r /tmp/baseline_srd_5_1 dist/srd_5_1
```

**Expected:** no diff (output is deterministic). If there *is* a diff, decide whether it's intentional (data fix → update goldens) or an accident.

`archive/dist_versions/srd_5_1_YYYYMMDD_v0.X.Y/` snapshots in the repo serve the same purpose for comparing against previously-shipped releases.

---

## Pre-Release Checklist

Before tagging a new version:

- [ ] `make bundle` completes cleanly
- [ ] `./scripts/smoke.sh srd_5_1 dist bundle` exits 0
- [ ] `meta.json.inventory` matches actual item counts (step 4 above)
- [ ] All 16 datasets validate against their schemas (step 5)
- [ ] `pytest -q`: 292+ passing, 19 skipped, 0 failed
- [ ] All 16 golden tests pass
- [ ] `pre-commit run -a` clean
- [ ] `pyproject.toml` version bumped (use `python scripts/bump_version.py X.Y.Z` — it also regenerates committed fixtures)
- [ ] `docs/ROADMAP.md` updated for the new version
- [ ] Snapshot saved to `archive/dist_versions/srd_5_1_YYYYMMDD_vX.Y.Z/`
- [ ] Git tree is clean, commits land on main, then `git tag vX.Y.Z && git push --tags`

---

## Automated Verification (CI)

A minimal CI block:

```yaml
- name: Build bundle
  run: make bundle

- name: Smoke check
  run: ./scripts/smoke.sh srd_5_1 dist bundle

- name: Inventory cross-check
  run: |
    python3 - <<'PY'
    import json
    from pathlib import Path
    meta = json.load(open("dist/srd_5_1/meta.json"))
    fail = False
    for dataset, entry in meta["datasets"].items():
        expected = entry["count"]
        doc = json.load(open(Path("dist/srd_5_1") / entry["file"]))
        actual = len(doc.get("items") or doc.get(dataset, []))
        assert actual == expected, f"{dataset}: {actual} != {expected}"
    PY

- name: Tests
  run: pytest -q
```

---

## References

- The consumer-facing bundle README is generated dynamically into `dist/srd_5_1/README.md` on every `make bundle` (see `_generate_bundle_readme` in [src/srd_builder/build.py](src/srd_builder/build.py)).
- [ARCHITECTURE.md](ARCHITECTURE.md) — system design and module organization
- [SCHEMAS.md](SCHEMAS.md) — schema versioning and field definitions
- [INTEGRATION.md](INTEGRATION.md) — consumer-side integration guide
