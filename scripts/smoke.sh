#!/usr/bin/env bash
set -euo pipefail

RULESET=${1:-srd_5_1}
OUT_DIR=${2:-dist}

export PYTHONPATH="src${PYTHONPATH:+:${PYTHONPATH}}"

python -m srd_builder.build --ruleset "${RULESET}" --out "${OUT_DIR}" >/dev/null

DATA_DIR="${OUT_DIR}/${RULESET}/data"
if [[ ! -d "${DATA_DIR}" ]]; then
  echo "No data directory found at ${DATA_DIR}" >&2
  exit 1
fi

echo "Artifacts in ${DATA_DIR}:"
DATA_DIR="${DATA_DIR}" python - <<'PY'
import json
import os
import pathlib

data_dir = pathlib.Path(os.environ["DATA_DIR"])
for path in sorted(data_dir.glob("*.json")):
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and "items" in payload:
        count = len(payload["items"])
        label = f"{count} items"
    elif isinstance(payload, dict) and "stats" in payload:
        stats = payload["stats"]
        total = stats.get("total_entities", 0)
        label = f"{total} entities"
    else:
        label = "n/a"
    print(f"- {path.name}: {label}")
PY
