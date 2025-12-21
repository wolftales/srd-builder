#!/usr/bin/env bash
# Quick smoke test with optional bundle structure validation
set -euo pipefail

RULESET=${1:-srd_5_1}
OUT_DIR=${2:-dist}
MODE=${3:-dev}  # dev or bundle

export PYTHONPATH="src${PYTHONPATH:+:${PYTHONPATH}}"

python -m srd_builder.build --ruleset "${RULESET}" --out "${OUT_DIR}" >/dev/null

# Check for flat structure (current) or data/ subdirectory (legacy)
if [[ -d "${OUT_DIR}/${RULESET}" ]]; then
  DIST_DIR="${OUT_DIR}/${RULESET}"
elif [[ -d "${OUT_DIR}/${RULESET}/data" ]]; then
  DIST_DIR="${OUT_DIR}/${RULESET}/data"
else
  echo "No data directory found at ${OUT_DIR}/${RULESET}" >&2
  exit 1
fi

echo "Artifacts in ${DIST_DIR}:"
DIST_DIR="${DIST_DIR}" python - <<'PY'
import json
import os
import pathlib

dist_dir = pathlib.Path(os.environ["DIST_DIR"])
for path in sorted(dist_dir.glob("*.json")):
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and "items" in payload:
        count = len(payload["items"])
        label = f"{count} items"
    elif isinstance(payload, dict) and "features" in payload:
        count = len(payload["features"])
        label = f"{count} features"
    elif isinstance(payload, dict) and "conditions" in payload:
        count = len(payload["conditions"])
        label = f"{count} conditions"
    elif isinstance(payload, dict) and "stats" in payload:
        stats = payload["stats"]
        total = stats.get("total_entities", 0)
        label = f"{total} entities"
    else:
        label = "n/a"
    print(f"- {path.name}: {label}")
PY

# Bundle structure validation
if [[ "${MODE}" == "bundle" ]]; then
  echo ""
  echo "Bundle structure checks:"

  ISSUES=0

  # Check README
  if [[ -f "${DIST_DIR}/README.md" ]]; then
    echo "✓ README.md present"
  else
    echo "✗ Missing README.md"
    ((ISSUES++))
  fi

  # Check schemas/
  if [[ -d "${DIST_DIR}/schemas" ]]; then
    SCHEMA_COUNT=$(find "${DIST_DIR}/schemas" -name '*.schema.json' -type f | wc -l)
    if [[ ${SCHEMA_COUNT} -ge 8 ]]; then
      echo "✓ schemas/ directory (${SCHEMA_COUNT} files)"
    else
      echo "✗ schemas/ has only ${SCHEMA_COUNT} files (expected ≥8)"
      ((ISSUES++))
    fi
  else
    echo "✗ Missing schemas/ directory"
    ((ISSUES++))
  fi

  # Check docs/
  if [[ -d "${DIST_DIR}/docs" ]]; then
    DOCS_COUNT=$(find "${DIST_DIR}/docs" -name '*.md' -type f | wc -l)
    if [[ ${DOCS_COUNT} -eq 2 ]]; then
      echo "✓ docs/ directory (${DOCS_COUNT} files)"
    else
      echo "✗ docs/ has ${DOCS_COUNT} files (expected 2)"
      ((ISSUES++))
    fi
  else
    echo "✗ Missing docs/ directory"
    ((ISSUES++))
  fi

  if [[ ${ISSUES} -gt 0 ]]; then
    echo ""
    echo "Bundle validation failed: ${ISSUES} issues found"
    exit 1
  fi
fi
