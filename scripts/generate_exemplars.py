#!/usr/bin/env python3
"""Generate one valid exemplar instance per schema in schemas/.

Each exemplar is a minimal JSON record that satisfies the schema's required
properties. The output serves three independent purposes:

1. Homebrew authoring templates (replaces docs/templates/).
2. Known-truths fixture baseline for data-integrity audits.
3. Schema round-trip smoke test — every schema must validate its own exemplar.

Usage:
    python scripts/generate_exemplars.py                # writes exemplars/*.json
    python scripts/generate_exemplars.py --check        # validate-only, no write
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMAS_DIR = REPO_ROOT / "schemas"
EXEMPLARS_DIR = REPO_ROOT / "exemplars"

# Patterns we explicitly recognise; everything else falls through to a
# small set of generic heuristics below.
_PATTERN_EXAMPLES: dict[str, str] = {
    r"^[a-z][a-z0-9_]*$": "example",
    r"^[a-z0-9_]+$": "example",
    r"^[a-z_]+$": "example",
    r"^[A-Z]{3}$": "STR",
    r"^d(6|8|10|12)$": "d8",
    r"^[a-z][a-z0-9\s-]*$": "example",
    r"^[a-z0-9_:]+$": "example",
    r"^(class|lineage):[a-z0-9_]+$": "class:example",
    r"^(monster|creature|npc):[a-z0-9_]+$": "monster:example",
}

# Matches "^prefix:" — covers both bare "^foo:" and "^foo:[a-z..." forms.
_ID_PREFIX_RE = re.compile(r"^\^([a-z_]+):")


def _example_for_pattern(pattern: str) -> str:
    """Return a string that satisfies a known SRD-builder regex pattern."""
    if pattern in _PATTERN_EXAMPLES:
        return _PATTERN_EXAMPLES[pattern]
    m = _ID_PREFIX_RE.match(pattern)
    if m:
        prefix = m.group(1)
        if pattern.count(":[") == 2:  # owner-qualified e.g. feature:owner:name
            return f"{prefix}:example_owner:example"
        return f"{prefix}:example"
    return ""


def _example_for_property(prop: dict[str, Any], name: str = "") -> Any:
    """Build a value satisfying a single property schema."""
    if "enum" in prop:
        return prop["enum"][0]
    if "const" in prop:
        return prop["const"]
    if "oneOf" in prop:
        return _example_for_property(prop["oneOf"][0], name)
    if "anyOf" in prop:
        return _example_for_property(prop["anyOf"][0], name)

    prop_type = prop.get("type")
    if isinstance(prop_type, list):
        prop_type = prop_type[0]

    if prop_type == "string":
        if "pattern" in prop:
            return _example_for_pattern(prop["pattern"])
        if "format" in prop and prop["format"] == "date":
            return "2026-01-01"
        return f"example {name}".strip() or "example"
    if prop_type == "integer":
        return prop.get("minimum", 1)
    if prop_type == "number":
        return prop.get("minimum", 0.0)
    if prop_type == "boolean":
        return False
    if prop_type == "array":
        item_schema = prop.get("items", {})
        min_items = prop.get("minItems", 1)
        return [_example_for_property(item_schema, name) for _ in range(max(1, min_items))]
    if prop_type == "object":
        return _build_object(prop)
    return {}


def _build_object(schema: dict[str, Any]) -> dict[str, Any]:
    """Build a minimal object satisfying ``required`` of ``schema``."""
    result: dict[str, Any] = {}
    properties = schema.get("properties", {})
    for req_name in schema.get("required", []):
        prop = properties.get(req_name, {})
        result[req_name] = _example_for_property(prop, req_name)
    min_props = schema.get("minProperties", 0)
    if min_props and len(result) < min_props:
        # Borrow optional `properties` to fill the gap.
        for opt_name, opt_schema in properties.items():
            if len(result) >= min_props:
                break
            if opt_name in result:
                continue
            result[opt_name] = _example_for_property(opt_schema, opt_name)
        # Or fall back to patternProperties.
        if len(result) < min_props and "patternProperties" in schema:
            for i, (pat, sub) in enumerate(schema["patternProperties"].items()):
                if len(result) >= min_props:
                    break
                key = _example_for_pattern(pat) or f"k{i}"
                result[key] = _example_for_property(sub, key)
    return result


def build_exemplar(schema: dict[str, Any]) -> dict[str, Any]:
    """Return a minimal valid instance for ``schema``."""
    return _build_object(schema)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate exemplars without writing; exit non-zero on failure.",
    )
    args = parser.parse_args(argv)

    schemas = sorted(SCHEMAS_DIR.glob("*.schema.json"))
    if not schemas:
        print(f"No schemas found under {SCHEMAS_DIR}", file=sys.stderr)
        return 1

    if not args.check:
        EXEMPLARS_DIR.mkdir(exist_ok=True)

    failures: list[str] = []
    written = 0
    for schema_path in schemas:
        name = schema_path.name.replace(".schema.json", "")
        schema = json.loads(schema_path.read_text())
        exemplar = build_exemplar(schema)
        validator = Draft202012Validator(schema)
        errors = sorted(validator.iter_errors(exemplar), key=lambda e: e.path)
        if errors:
            failures.append(name)
            print(f"FAIL {name}:", file=sys.stderr)
            for err in errors[:5]:
                path = "/".join(str(p) for p in err.path) or "<root>"
                print(f"  - {path}: {err.message}", file=sys.stderr)
            continue
        if not args.check:
            out = EXEMPLARS_DIR / f"{name}.exemplar.json"
            out.write_text(json.dumps(exemplar, indent=2) + "\n")
            written += 1

    if failures:
        print(
            f"\n{len(failures)}/{len(schemas)} exemplars failed schema validation",
            file=sys.stderr,
        )
        return 1

    if args.check:
        print(f"OK: all {len(schemas)} exemplars validate against their schemas.")
    else:
        print(f"OK: wrote {written} exemplars to {EXEMPLARS_DIR.relative_to(REPO_ROOT)}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
