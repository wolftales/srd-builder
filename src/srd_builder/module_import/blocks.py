"""Turning ordered page lines into classified content blocks.

Block role and audience are read off typography, because that is how the
publication marks them - there is no label in the text saying "this paragraph is
player-safe". That makes `audience` an importer inference, and every block
records it as one so a consumer can fail closed rather than read GM text aloud.
"""

from __future__ import annotations

import re
from typing import Any

from srd_builder.module_import.profile import AUDIENCE_BY_BLOCK_TYPE, SourceProfile
from srd_builder.module_import.spine import KeyedEntry, slugify

# Hyphenation at a line break, e.g. "aban-\ndoned" -> "abandoned".
_LINE_BREAK_HYPHEN = re.compile(r"(\w)-\s+(\w)")
_WHITESPACE = re.compile(r"\s+")


def join_lines(texts: list[str]) -> str:
    """Reflow wrapped lines into a paragraph."""
    joined = " ".join(text.strip() for text in texts if text.strip())
    joined = _LINE_BREAK_HYPHEN.sub(r"\1\2", joined)
    return _WHITESPACE.sub(" ", joined).strip()


def _starts_key(text: str, key: str) -> bool:
    return text.strip().startswith(f"{key}.")


def slice_for_key(
    reading_order: list[dict[str, Any]], key: str, next_key: str | None
) -> list[dict[str, Any]]:
    """The lines belonging to one keyed location.

    Runs from that key's heading to the next key's heading. A keyed entry owns
    everything printed under it, including material that continues onto later
    pages, which is why this works on a reading-order stream rather than a page.
    """
    start = next(
        (i for i, line in enumerate(reading_order) if _starts_key(line["text"], key)), None
    )
    if start is None:
        return []
    end = len(reading_order)
    if next_key is not None:
        for offset, line in enumerate(reading_order[start + 1 :], start=start + 1):
            if _starts_key(line["text"], next_key):
                end = offset
                break
    return reading_order[start + 1 : end]


def blocks_for_key(
    lines: list[dict[str, Any]], entry: KeyedEntry, profile: SourceProfile, page_label: str
) -> list[dict[str, Any]]:
    """Group a keyed location's lines into typed blocks.

    Consecutive lines sharing a body font become one block; a heading font or a
    change of role closes the current block. Non-body faces (captions, page
    furniture) are dropped rather than guessed at.
    """
    grouped: list[tuple[str, list[str]]] = []
    for line in lines:
        block_type = profile.block_type(line["font"])
        if block_type is None:
            if profile.is_heading(line["font"]):
                grouped.append(("", []))  # a heading breaks the run
            continue
        if grouped and grouped[-1][0] == block_type:
            grouped[-1][1].append(line["text"])
        else:
            grouped.append((block_type, [line["text"]]))

    blocks: list[dict[str, Any]] = []
    for block_type, texts in grouped:
        if not block_type:
            continue
        text = join_lines(texts)
        if not text:
            continue
        ordinal = sum(1 for block in blocks if block["type"] == block_type) + 1
        blocks.append(
            {
                "id": f"block:{slugify(entry.key)}_{block_type}_{ordinal}",
                "type": block_type,
                "audience": AUDIENCE_BY_BLOCK_TYPE[block_type],
                "text": text,
                "source_ref": {"source_key": entry.key, "printed_page": page_label},
                "stance": "source_explicit",
                # The publication states the prose; the typography implies who
                # may hear it. That inference is the one that leaks secrets when
                # it is wrong, so it is always declared.
                "inferred_fields": ["audience"],
            }
        )
    return blocks
