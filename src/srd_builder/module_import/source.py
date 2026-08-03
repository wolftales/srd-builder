"""Locating and probing a source publication. The I/O boundary of the importer.

Source publications are third-party commercial products. They live outside the
repository and are named by configuration, never by a path baked into the code.
"""

from __future__ import annotations

import os
import re
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import fitz

from srd_builder.utils import pdf_probe

#: Environment variable naming the source publication to import.
SOURCE_ENV_VAR = "SRD_MODULE_SOURCE"


class SourceUnavailableError(RuntimeError):
    """The configured source publication could not be found."""


@dataclass(frozen=True)
class TocEntry:
    level: int
    title: str
    page: int  # 1-based, as the publication numbers its own bookmarks


@dataclass(frozen=True)
class PublicationIdentity:
    """What the publication says it is, established from the file itself."""

    path: Path
    fingerprint: str
    page_count: int
    producer: str
    toc: tuple[TocEntry, ...]

    @property
    def has_navigation(self) -> bool:
        return bool(self.toc)


def resolve_source_path(explicit: Path | str | None = None) -> Path:
    """The publication to import, from an explicit path or SRD_MODULE_SOURCE.

    Raises SourceUnavailableError rather than returning a default: silently
    importing the wrong publication is worse than refusing to import one.
    """
    candidate = explicit if explicit is not None else os.environ.get(SOURCE_ENV_VAR)
    if not candidate:
        raise SourceUnavailableError(
            f"No source publication configured. Pass one explicitly or set {SOURCE_ENV_VAR}."
        )
    path = Path(candidate).expanduser()
    if not path.is_file():
        raise SourceUnavailableError(f"Source publication not found: {path}")
    return path


@contextmanager
def open_source(path: Path) -> Iterator[fitz.Document]:
    """Open a source publication. Consumes utils.pdf_probe, never fitz directly."""
    with pdf_probe.open_pdf(path) as doc:
        yield doc


def probe_identity(doc: fitz.Document, path: Path) -> PublicationIdentity:
    """Establish what this publication is from its own contents."""
    return PublicationIdentity(
        path=path,
        fingerprint=f"sha256:{pdf_probe.pdf_sha256(path)}",
        page_count=doc.page_count,
        producer=str(doc.metadata.get("producer") or ""),
        toc=tuple(
            TocEntry(level=lvl, title=title, page=page) for lvl, title, page in doc.get_toc()
        ),
    )


#: Ruleset vocabulary that only appears in a 5e-family publication. Directory
#: names and storefront bundle labels are hints; identity comes from the text.
_FIFTH_EDITION_MARKERS = (
    r"\bDC\s*\d+\b",
    r"\bChallenge\s+\d+\s*\(\d",
    r"\bAdvantage\b",
    r"\bhit\s+dice\b",
    r"\bproficiency\s+bonus\b",
)


def ruleset_evidence(doc: fitz.Document, *, sample_pages: int = 8) -> dict[str, int]:
    """Count ruleset-identifying vocabulary in the publication's own text.

    Exists because a sibling bundle ships a Swords & Wizardry edition of this
    same adventure under a filename that implies 5e. Establish the ruleset from
    publication evidence and confirm it during review.
    """
    step = max(1, doc.page_count // sample_pages)
    text = " ".join(pdf_probe.page_text(doc, i) for i in range(0, doc.page_count, step))
    return {
        marker: len(re.findall(marker, text, flags=re.IGNORECASE))
        for marker in _FIFTH_EDITION_MARKERS
    }


def page_lines(doc: fitz.Document, index: int, profile: Any) -> list[dict[str, Any]]:
    """One page's text lines in reading order, with overprint removed.

    Returns dicts of {text, font, size, bbox, column}. Lines are ordered by
    column then vertical position, which is the reading order of a multi-column
    page and not the order the PDF stores them in.
    """
    page = pdf_probe.page_dict(doc, index)
    split = profile.column_split_x
    lines: list[dict[str, Any]] = []

    for block in page["blocks"]:
        seen: set[tuple[float, ...]] = set()
        for line in block.get("lines", []):
            spans = line.get("spans", [])
            if not spans:
                continue
            font = spans[0]["font"]
            geometry = tuple(round(value, 2) for value in line["bbox"])
            # The display face is drawn twice at an identical bbox. Same
            # geometry plus an overprinted face means a rendering artefact, not
            # a repeated sentence.
            if font in profile.overprinted_fonts:
                if geometry in seen:
                    continue
                seen.add(geometry)
            # Small caps split one word across spans of differing size; joining
            # the spans of a line restores it.
            text = "".join(span["text"] for span in spans)
            if not text.strip():
                continue
            x0, y0 = line["bbox"][0], line["bbox"][1]
            lines.append(
                {
                    "text": text,
                    "font": font,
                    "size": round(spans[0]["size"], 1),
                    "bbox": tuple(line["bbox"]),
                    "column": 0 if split is None or x0 < split else 1,
                    "_sort": (0 if split is None or x0 < split else 1, round(y0, 1), round(x0, 1)),
                }
            )

    lines.sort(key=lambda line: line["_sort"])
    for line in lines:
        del line["_sort"]
    return lines
