"""Bundle JSON files round-trip byte-identically through our own `json.dumps`.

This is a self-consistency check on the producer's output, NOT a Prettier
or Biome compatibility test. It confirms that re-loading and re-dumping
any shipped JSON with the same parameters `srd_builder.build` uses
(`indent=2, ensure_ascii=False`, trailing newline) returns identical bytes.

What this catches:
  - The bundle was hand-edited or rewritten by a different tool, breaking
    determinism vs the upstream release tag.
  - `srd_builder.build` started emitting JSON with different formatting
    parameters, in which case `docs/COMPATIBILITY.md` (section "Consumer
    handling of bundle artifacts") must be updated to match.

What this does NOT catch:
  - Prettier (or any other external formatter) producing a different
    byte-stream than ours. Cross-formatter compatibility is not a
    producer guarantee; see the COMPATIBILITY.md section above.

Skipped when `dist/srd_5_1/` is absent (CI without a bundle).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

DIST_DIR = Path(__file__).resolve().parents[1] / "dist" / "srd_5_1"


def _bundle_json_files() -> list[Path]:
    if not DIST_DIR.exists():
        return []
    return sorted(DIST_DIR.glob("*.json"))


@pytest.mark.parametrize(
    "json_path",
    _bundle_json_files()
    or [pytest.param(None, marks=pytest.mark.skip(reason="dist/srd_5_1/ not built"))],
    ids=lambda p: p.name if p else "no-bundle",
)
def test_bundle_json_is_redump_identical(json_path: Path) -> None:
    raw = json_path.read_bytes()
    obj = json.loads(raw)
    redumped = (json.dumps(obj, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    assert raw == redumped, (
        f"{json_path.name} is not byte-identical to its json.dumps re-dump "
        f"(indent=2, ensure_ascii=False, trailing newline). "
        f"Shipped: {len(raw)} bytes, redumped: {len(redumped)} bytes. "
        f"This breaks the producer self-consistency invariant documented "
        f"in docs/COMPATIBILITY.md (section: Consumer handling of bundle artifacts)."
    )
