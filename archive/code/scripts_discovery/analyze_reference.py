#!/usr/bin/env python3
"""Summarize the TabylTop JSON reference dataset."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze reference JSON monster data")
    parser.add_argument("json_path", type=Path, help="Path to srd_cc_v5.1_rules_tabyltop.json")
    parser.add_argument("--output", type=Path, help="Save summary to file")
    args = parser.parse_args()

    if not args.json_path.exists():
        raise FileNotFoundError(f"Reference JSON not found: {args.json_path}")

    with open(args.json_path, encoding="utf-8") as handle:
        data = json.load(handle)

    # This reference JSON is a raw PDF extraction (tables/paragraphs/headings)
    # Monster names appear as h1/h2/h3 headings in pages 300+
    monster_headers = []
    for entry in data:
        entry_type = entry.get("type", "")
        page = entry.get("page", 0)

        # Monsters section starts around page 300
        if page >= 300 and entry_type in ("h1", "h2", "h3", "h4"):
            # Extract text from subelements
            text = ""
            for sub in entry.get("subelements", []):
                text += sub.get("text", "")
            text = text.strip()

            if text:
                monster_headers.append({"name": text, "page": page, "level": entry_type})

    names = [m["name"] for m in monster_headers]
    duplicates = {name: count for name, count in Counter(names).items() if count > 1}

    summary = {
        "total_entries": len(data),
        "monster_count": len(monster_headers),
        "unique_monster_names": len(set(names)),
        "duplicates": duplicates,
        "monster_names": sorted(set(names)),
        "sample_monsters": monster_headers[:5],
    }

    output_json = json.dumps(summary, indent=2)

    if args.output:
        args.output.write_text(output_json)
        print(f"Summary saved to {args.output}")
    else:
        print(output_json)


if __name__ == "__main__":
    main()
