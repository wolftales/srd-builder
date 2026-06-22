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
  # AUTO-SYNC:check:expected START
  declare -A EXPECTED=(
    ["ability_scores.json"]=6
    ["classes.json"]=12
    ["conditions.json"]=15
    ["damage_types.json"]=13
    ["diseases.json"]=3
    ["equipment.json"]=259
    ["features.json"]=245
    ["lineages.json"]=13
    ["magic_items.json"]=240
    ["monsters.json"]=317
    ["poisons.json"]=14
    ["rules.json"]=167
    ["skills.json"]=18
    ["spells.json"]=319
    ["tables.json"]=35
    ["weapon_properties.json"]=11
  )

  # All datasets use the 'items' key since v0.30.0.
  declare -A KEYS=()
  # AUTO-SYNC:check:expected END

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

# Known-truths gate: pins hand-curated field values on specific records so
# silent parser drift (e.g., "Fireball is now level 4") fails the release.
# Skipped in CI by design (no PDF -> no build -> no dist); enforced here.
pytest tests/test_known_truths.py -q

echo "Release check passed for ${RULESET} in ${OUT_DIR}."
