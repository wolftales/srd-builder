# Build Verification Checklist

This document defines the complete verification process for validating srd-builder builds and refactors.

## Quick Verification (Development)

For development work and small changes:

```bash
# 1. Run golden dataset tests
pytest tests/test_conditions_golden.py tests/test_golden_monsters.py tests/test_golden_spells.py -v

# 2. Run code quality checks
ruff check .

# 3. Spot-check one dataset
head -100 dist/srd_5_1/monsters.json
```

**Expected:** All tests pass, ruff clean, JSON structure looks correct.

---

## Complete Verification (Before Commit)

For refactors, major changes, or pre-release validation:

### 1. Build Complete Bundle

```bash
# Build with --bundle flag to include schemas and docs
python -m srd_builder.build --ruleset srd_5_1 --format json --bundle

# Or use Makefile shortcut
make output
```

### 2. Verify Bundle Contents

```bash
# Check all expected files present
ls -la dist/srd_5_1/

# Expected structure:
# dist/srd_5_1/
# ├── README.md              (bundle guide)
# ├── *.json                 (13 data files)
# ├── schemas/*.schema.json  (10 schema files)
# └── docs/*.md              (2 documentation files)
```

**Expected files (27 total):**

**Data files (14):**
- build_report.json
- classes.json
- conditions.json
- diseases.json
- equipment.json
- features.json
- index.json
- lineages.json
- madness.json
- meta.json
- monsters.json
- poisons.json
- spells.json
- tables.json

**Schemas (10):**
- schemas/class.schema.json
- schemas/condition.schema.json
- schemas/disease.schema.json
- schemas/equipment.schema.json
- schemas/features.schema.json
- schemas/lineage.schema.json
- schemas/madness.schema.json
- schemas/monster.schema.json
- schemas/poison.schema.json
- schemas/spell.schema.json
- schemas/table.schema.json

**Documentation (3):**
- README.md (at root)
- docs/SCHEMAS.md
- docs/DATA_DICTIONARY.md

### 3. Validate File Sizes

```bash
wc -c dist/srd_5_1/*.json
```

**Expected sizes (approximate):**
- monsters.json: ~1,041,000 bytes (317 monsters)
- spells.json: ~550,000 bytes (319 spells)
- equipment.json: ~141,000 bytes (106+ items)
- features.json: ~165,000 bytes (246 features)
- index.json: ~324,000 bytes (search index)
- conditions.json: ~10,000 bytes (15 conditions)
- classes.json: ~47,000 bytes (12 classes)
- lineages.json: ~29,000 bytes (13 lineages)
- tables.json: ~145,000 bytes (23 tables)
- diseases.json: ~5,400 bytes
- madness.json: ~13,000 bytes
- poisons.json: ~10,400 bytes
- meta.json: ~11,400 bytes
- build_report.json: ~200 bytes

**If file sizes are drastically different** (e.g., <1000 bytes), parsing likely failed.

### 4. Run Full Test Suite

```bash
pytest -v
```

**Expected:**
- 105+ tests passing
- 2 known failures (both in tmp_path environment):
  - `test_build_pipeline` (looks for schemas in tmp_path not workspace)
  - `test_meta_json_schema_version` (expects deprecated $schema_version field)

**If other tests fail,** the refactor broke something.

### 5. Validate Against Schemas

```bash
# Requires jsonschema CLI: pip install check-jsonschema
check-jsonschema --schemafile dist/srd_5_1/schemas/monster.schema.json dist/srd_5_1/monsters.json
check-jsonschema --schemafile dist/srd_5_1/schemas/spell.schema.json dist/srd_5_1/spells.json
check-jsonschema --schemafile dist/srd_5_1/schemas/equipment.schema.json dist/srd_5_1/equipment.json
```

**Expected:** No validation errors.

### 6. Content Spot Checks

```bash
# Check monsters contain expected fields
jq '.items[0] | keys' dist/srd_5_1/monsters.json

# Check spell count
jq '.items | length' dist/srd_5_1/spells.json  # Should be 319

# Check index stats
jq '.stats' dist/srd_5_1/index.json
```

**Expected counts:**
- Monsters: 317 total (201 monsters + 95 creatures + 21 NPCs)
- Spells: 319
- Equipment: 106+
- Features: 246 (154 class + 92 lineage)
- Tables: 23
- Conditions: 15
- Classes: 12
- Lineages: 13

### 7. Code Quality Checks

```bash
# Linting and formatting
ruff check .

# Type checking (optional - has pre-existing errors)
mypy src/srd_builder/
```

**Expected:** Ruff clean, mypy may have 1 pre-existing error about duplicate module names.

---

## Regression Testing (Baseline Comparison)

For major refactors, compare output against known-good baseline:

### 1. Save Baseline Before Refactor

```bash
# Before starting refactor work
python -m srd_builder.build --ruleset srd_5_1 --format json --bundle
cp -r dist/srd_5_1 /tmp/baseline_srd_5_1
```

### 2. Build After Refactor

```bash
# After completing refactor
python -m srd_builder.build --ruleset srd_5_1 --format json --bundle
```

### 3. Compare Outputs

```bash
# Byte-for-byte comparison (should be identical)
diff -r /tmp/baseline_srd_5_1 dist/srd_5_1

# Or use hash comparison
find /tmp/baseline_srd_5_1 -type f -exec sha256sum {} \; | sort > /tmp/baseline_hashes.txt
find dist/srd_5_1 -type f -exec sha256sum {} \; | sort > /tmp/current_hashes.txt
diff /tmp/baseline_hashes.txt /tmp/current_hashes.txt
```

**Expected:** No differences (files should be byte-identical).

**If there are differences:**
- Check if timestamps in metadata (these should be deterministic now)
- Check if data ordering changed (investigate why)
- Check if fields were added/removed (breaking change)

---

## Known Issues / Acceptable Failures

### Test Failures (2)

**test_build_pipeline** - Looking for schemas in tmp_path:
- **Why it fails:** Test creates build in tmp_path but validator looks in workspace root for schemas/
- **Impact:** None - real builds work fine
- **Fix needed:** Update test to either bundle schemas or mock validator

**test_meta_json_schema_version** - Deprecated field:
- **Why it fails:** Looking for `$schema_version` field that was removed from meta.json
- **Impact:** None - schema_version now in each dataset's _meta
- **Fix needed:** Update test to check dataset._meta.schema_version instead

### MyPy Error (1)

**Duplicate module names:**
- **Issue:** "Source file found twice under different module names"
- **Why:** Possibly related to src/ layout or package discovery
- **Impact:** None - not blocking development
- **Fix needed:** Investigation required

---

## Automated Verification (CI)

For CI/GitHub Actions:

```yaml
- name: Build complete bundle
  run: python -m srd_builder.build --ruleset srd_5_1 --format json --bundle

- name: Verify bundle structure
  run: |
    test -f dist/srd_5_1/README.md
    test -d dist/srd_5_1/schemas
    test -d dist/srd_5_1/docs
    test -f dist/srd_5_1/monsters.json
    test -f dist/srd_5_1/spells.json

- name: Validate file counts
  run: |
    # Should have 14 JSON files + README at root
    [ $(ls dist/srd_5_1/*.json | wc -l) -eq 14 ]
    # Should have 10+ schema files
    [ $(ls dist/srd_5_1/schemas/*.schema.json | wc -l) -ge 10 ]
    # Should have 2 doc files
    [ $(ls dist/srd_5_1/docs/*.md | wc -l) -eq 2 ]

- name: Run tests
  run: pytest -v --tb=short
```

---

## Post-Refactor Checklist

After completing a refactor:

- [ ] Full build with `--bundle` completes without errors
- [ ] All 27 expected files present in dist/srd_5_1/
- [ ] File sizes match expected ranges
- [ ] Golden tests pass (7/7)
- [ ] Full test suite: 105+ pass, ≤2 known failures
- [ ] Ruff checks clean
- [ ] Content spot checks pass (monster count, spell count, etc.)
- [ ] Git history preserved (`git log --follow` works on moved files)
- [ ] Documentation updated (ARCHITECTURE.md, CHANGELOG.md, etc.)

---

## References

- [BUNDLE_README.md](BUNDLE_README.md) - Expected bundle structure
- [ARCHITECTURE.md](ARCHITECTURE.md) - System design and module organization
- [SCHEMAS.md](SCHEMAS.md) - Schema versioning and field definitions
