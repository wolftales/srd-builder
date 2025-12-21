#!/usr/bin/env bash
# Deterministic build verification with item count validation
set -euo pipefail

RULESET=${1:-srd_5_1}
OUT_DIR=${2:-dist}

export PYTHONPATH="src${PYTHONPATH:+:${PYTHONPATH}}"

python -m srd_builder.build --ruleset "${RULESET}" --out "${OUT_DIR}" >/dev/null
python -m srd_builder.utils.validate --ruleset "${RULESET}" >/dev/null

# Support both flat structure and data/ subdirectory
if [[ -d "${OUT_DIR}/${RULESET}" ]]; then
  DATA_DIR="${OUT_DIR}/${RULESET}"
elif [[ -d "${OUT_DIR}/${RULESET}/data" ]]; then
  DATA_DIR="${OUT_DIR}/${RULESET}/data"
else
  echo "Expected dataset directory at ${OUT_DIR}/${RULESET}" >&2
  exit 1
fi

# Hash comparison (determinism check) - exclude build_report.json which has timestamps
declare -A HASHES
mapfile -t FILES < <(find "${DATA_DIR}" -maxdepth 1 -name '*.json' ! -name 'build_report.json' | sort)
for file in "${FILES[@]}"; do
  HASHES["${file}"]=$(sha256sum "${file}" | awk '{print $1}')
done

python -m srd_builder.build --ruleset "${RULESET}" --out "${OUT_DIR}" >/dev/null

for file in "${FILES[@]}"; do
  new_hash=$(sha256sum "${file}" | awk '{print $1}')
  if [[ "${HASHES[${file}]}" != "${new_hash}" ]]; then
    echo "Hash mismatch for ${file}" >&2
    exit 1
  fi
done

# Timestamp check
if command -v rg &> /dev/null; then
  if rg --fixed-strings --glob '*.json' --no-heading --line-number 'timestamp' "${DATA_DIR}" >/dev/null 2>&1; then
    echo "Timestamps found in data files." >&2
    exit 1
  fi
fi

# Item count validation (if jq available)
if command -v jq &> /dev/null; then
  declare -A EXPECTED=(
    ["monsters.json"]=317
    ["spells.json"]=319
    ["equipment.json"]=258
    ["classes.json"]=12
    ["lineages.json"]=13
    ["tables.json"]=38
  )

  # Special keys for non-standard structures
  declare -A KEYS=(
    ["features.json"]="features"
    ["conditions.json"]="conditions"
  )
  EXPECTED["features.json"]=246
  EXPECTED["conditions.json"]=15

  for file in "${!EXPECTED[@]}"; do
    if [[ -f "${DATA_DIR}/${file}" ]]; then
      key="${KEYS[$file]:-items}"
      actual=$(jq ".${key} | length" "${DATA_DIR}/${file}" 2>/dev/null || echo "0")
      expected=${EXPECTED[$file]}
      if [[ ${actual} -ne ${expected} ]]; then
        echo "Item count mismatch in ${file}: expected ${expected}, found ${actual}" >&2
        exit 1
      fi
    fi
  done
fi

echo "Release check passed for ${RULESET} in ${OUT_DIR}."
