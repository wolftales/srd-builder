#!/usr/bin/env bash
set -euo pipefail

RULESET=${1:-srd_5_1}
OUT_DIR=${2:-dist}

export PYTHONPATH="src${PYTHONPATH:+:${PYTHONPATH}}"

python -m srd_builder.build --ruleset "${RULESET}" --out "${OUT_DIR}" >/dev/null
python -m srd_builder.validate --ruleset "${RULESET}" >/dev/null

DATA_DIR="${OUT_DIR}/${RULESET}/data"
if [[ ! -d "${DATA_DIR}" ]]; then
  echo "Expected dataset directory at ${DATA_DIR}" >&2
  exit 1
fi

declare -A HASHES
mapfile -t FILES < <(find "${DATA_DIR}" -maxdepth 1 -name '*.json' | sort)
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

if rg --fixed-strings --glob '*.json' --no-heading --line-number 'timestamp' "${DATA_DIR}" >/dev/null; then
  echo "Timestamps found in data files." >&2
  exit 1
fi

echo "Release check passed for ${RULESET} in ${OUT_DIR}."
