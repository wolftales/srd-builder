"""font_fingerprint_walk pattern engine.

Header detection by font fingerprint, body accumulation per record.
Two header_scope modes: span (single-bucket concat output) and line
(font-split spans + optional cross-record merge post-pass).
"""

from __future__ import annotations

import re
from typing import Any

from ._shared import (
    _DEFAULT_STRUCTURAL_PATTERNS,
    _resolve_body_cleanup,
    _simplify_span,
    _span_matches_fingerprint,
)


def _line_bucket_for_spans(
    line_spans: list[dict[str, Any]], body_buckets: list[dict[str, Any]]
) -> str:
    """For font_split_spans: decide which bucket a line's spans belong in.

    A bucket may declare match_any_span={font_substring, require_italic, require_bold}.
    The first bucket whose predicate matches any span in the line wins.
    A bucket marked {"default": True} is the fallback.
    """
    default_name: str | None = None
    for bucket in body_buckets:
        if bucket.get("default", False):
            default_name = bucket["name"]
            continue
        predicate = bucket.get("match_any_span", {})
        font_sub = predicate.get("font_substring", "")
        need_italic = predicate.get("require_italic", False)
        need_bold = predicate.get("require_bold", False)
        for span in line_spans:
            font = span.get("font", "")
            if font_sub and font_sub not in font:
                continue
            if need_italic and not span.get("is_italic", False):
                continue
            if need_bold and not span.get("is_bold", False):
                continue
            return bucket["name"]
    if default_name is None:
        raise ValueError("font_split_spans body_buckets must include one {'default': True}")
    return default_name


def _post_pass_merge_short_records(
    records: list[dict[str, Any]], config: dict[str, Any]
) -> list[dict[str, Any]]:
    """Merge records whose check-bucket text is below threshold AND whose
    skip-bucket is empty, by prepending their spans into the next record.

    Mirrors the cross-page heuristic in extract_magic_items._merge_multipage_items.
    """
    if not records:
        return []
    threshold = config["merge_threshold"]
    check_bucket = config["merge_check_bucket"]
    skip_bucket = config.get("merge_skip_if_bucket_nonempty")

    merged: list[dict[str, Any]] = []
    current = records[0]
    for nxt in records[1:]:
        check_text_len = sum(len(s.get("text", "")) for s in current.get(check_bucket, []))
        skip = skip_bucket is not None and len(current.get(skip_bucket, [])) > 0
        if check_text_len < threshold and not skip:
            nxt[check_bucket] = current.get(check_bucket, []) + nxt.get(check_bucket, [])
        else:
            merged.append(current)
        current = nxt
    merged.append(current)
    return merged


def _extract_font_fingerprint_walk(
    pdf_path: str,
    pages: list[int],
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    """Walk pages and detect record headers by font fingerprint.

    Config schema (defaults in brackets):
        {
            "pattern_type": "font_fingerprint_walk",
            "header_fingerprints": [
                {
                    "font_substring": "GillSans",
                    "size_min": 13.5,
                    "size_max": 14.5,
                    "require_bold": True,
                    "require_italic": False,                  # optional
                    "min_text_len": 2,
                    "require_trailing_period": False,         # optional
                    "strip_trailing_period_from_name": False, # optional
                },
                # ...additional fingerprints OR'd together
            ],
            "header_scope": "span" | "line",                  # ["span"]
            "header_match_mode": "any_span" | "first_span",   # ["any_span"]; line-mode only
            "header_continuation_words": ["and", "or", ...],  # [None]; line-mode only
            "body_grouping": "single_bucket_concat" | "font_split_spans",
                                                              # ["single_bucket_concat"]
            "body_cleanup": "clean_text" | None,              # [None]; concat mode only
            "body_buckets": [                                 # font_split_spans only
                {"name": "metadata_blocks",
                 "match_any_span": {"font_substring": "Cambria",
                                    "require_italic": True}},
                {"name": "description_blocks", "default": True},
            ],
            "filter_structural": True,                        # [False]
            "structural_patterns": [...],                     # [_DEFAULT]
            "page_reset_record": True,                        # [True]
            "post_pass": "merge_short_records" | None,        # [None]
            "merge_threshold": 20,                            # post-pass param
            "merge_check_bucket": "description_blocks",
            "merge_skip_if_bucket_nonempty": "metadata_blocks",
        }

    Returns:
        list[dict] — one record per detected header. Shape depends on
        body_grouping:
            single_bucket_concat → {"name", "text", "page"}
            font_split_spans     → {"name", "page", <bucket_name>: [span_dicts]}
    """
    fingerprints = config["header_fingerprints"]
    if not fingerprints:
        raise ValueError("font_fingerprint_walk requires at least one header_fingerprints entry")

    header_scope = config.get("header_scope", "span")
    if header_scope == "span":
        return _font_fingerprint_walk_span_mode(pdf_path, pages, config)
    if header_scope == "line":
        return _font_fingerprint_walk_line_mode(pdf_path, pages, config)
    raise ValueError(f"Unknown header_scope '{header_scope}' (known: span, line)")


def _font_fingerprint_walk_span_mode(
    pdf_path: str,
    pages: list[int],
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    """Span-level header detection; single_bucket_concat body grouping only.

    Original prototype path used by extract_features. Kept narrow on purpose:
    new pattern complexity goes in _font_fingerprint_walk_line_mode().
    """
    from pathlib import Path

    from ...utils.pdf_probe import open_pdf

    fingerprints = config["header_fingerprints"]
    filter_structural = config.get("filter_structural", False)
    structural_re_list = [
        re.compile(p) for p in (config.get("structural_patterns") or _DEFAULT_STRUCTURAL_PATTERNS)
    ]
    body_cleanup = _resolve_body_cleanup(config.get("body_cleanup"))
    page_reset_record = config.get("page_reset_record", True)

    def _is_structural(text: str) -> bool:
        return any(rx.match(text) for rx in structural_re_list)

    records: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None

    with open_pdf(Path(pdf_path)) as pdf:
        for page_num in pages:
            if page_reset_record and current is not None:
                records.append(current)
                current = None

            page = pdf[page_num - 1]
            for block in page.get_text("dict")["blocks"]:
                if "lines" not in block:
                    continue
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        matched_fp: dict[str, Any] | None = None
                        for fp in fingerprints:
                            if _span_matches_fingerprint(span, fp):
                                matched_fp = fp
                                break

                        if matched_fp is not None:
                            if current is not None:
                                records.append(current)
                            name = text
                            if matched_fp.get("strip_trailing_period_from_name", False):
                                name = name.rstrip(".")
                            current = {"name": name, "text": "", "page": page_num}
                        elif current is not None and text:
                            if filter_structural and _is_structural(text):
                                continue
                            current["text"] += text + " "

    if current is not None:
        records.append(current)

    for r in records:
        r["text"] = body_cleanup(r["text"].strip())

    return records


def _font_fingerprint_walk_line_mode(
    pdf_path: str,
    pages: list[int],
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    """Line-level header detection with continuation, font-split body grouping,
    and optional cross-record post-pass merge.

    Used by extract_magic_items. Mirrors the original bespoke logic:
        - Header detected by checking the FIRST span of each line (mode
          'first_span') or ANY span ('any_span') against fingerprints.
        - If a header line ends in one of header_continuation_words, the next
          header line's text is appended and only the merged name is committed
          on the next non-header line.
        - body_grouping 'font_split_spans': line-level spans collected as
          simplified dicts and routed to a bucket based on per-line predicate.
        - Optional post_pass merges short records into the next.
    """
    from pathlib import Path

    from ...utils.pdf_probe import open_pdf

    fingerprints = config["header_fingerprints"]
    match_mode = config.get("header_match_mode", "any_span")
    continuation_words: set[str] = {
        w.lower() for w in (config.get("header_continuation_words") or [])
    }
    body_grouping = config.get("body_grouping", "single_bucket_concat")
    page_reset_record = config.get("page_reset_record", True)

    if body_grouping != "font_split_spans":
        raise ValueError(
            f"line header_scope currently requires body_grouping='font_split_spans' "
            f"(got '{body_grouping}')"
        )
    body_buckets = config["body_buckets"]
    bucket_names = [b["name"] for b in body_buckets]

    def _new_record(name: str, page_num: int) -> dict[str, Any]:
        rec: dict[str, Any] = {"name": name, "page": page_num}
        for b in bucket_names:
            rec[b] = []
        return rec

    def _line_matches_header(line_spans_raw: list[dict[str, Any]]) -> dict[str, Any] | None:
        if not line_spans_raw:
            return None
        candidates = [line_spans_raw[0]] if match_mode == "first_span" else line_spans_raw
        for span in candidates:
            for fp in fingerprints:
                if _span_matches_fingerprint(span, fp):
                    return fp
        return None

    records: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    pending_name: str | None = None
    pending_fp: dict[str, Any] | None = None

    with open_pdf(Path(pdf_path)) as pdf:
        for page_num in pages:
            page = pdf[page_num - 1]
            for block in page.get_text("dict")["blocks"]:
                if block.get("type") != 0:
                    continue
                for line in block.get("lines", []):
                    raw_spans = line.get("spans", [])
                    if not raw_spans:
                        continue
                    simple_spans = [_simplify_span(s) for s in raw_spans]
                    line_text = "".join(s["text"] for s in simple_spans).strip()
                    if not line_text:
                        continue

                    header_fp = _line_matches_header(raw_spans)

                    if header_fp is not None:
                        # Header line. Build / extend the pending name.
                        if pending_name is not None:
                            pending_name = pending_name.strip() + " " + line_text
                        else:
                            pending_name = line_text
                            pending_fp = header_fp
                        # Defer commit if trailing word signals continuation.
                        last_word = pending_name.split()[-1].lower() if pending_name.split() else ""
                        if last_word in continuation_words:
                            continue
                        # Otherwise fall through: header is complete on this line,
                        # but the original code only finalizes on the *next*
                        # non-header line. Preserve that timing.
                        continue

                    # Non-header line. If we have a pending header, finalize it
                    # into a new record now.
                    if pending_name is not None:
                        if current is not None:
                            records.append(current)
                        name = pending_name
                        if pending_fp is not None and pending_fp.get(
                            "strip_trailing_period_from_name", False
                        ):
                            name = name.rstrip(".")
                        current = _new_record(name, page_num)
                        pending_name = None
                        pending_fp = None

                    if current is None:
                        continue
                    bucket = _line_bucket_for_spans(simple_spans, body_buckets)
                    current[bucket].extend(simple_spans)

            # End of page. Flush any pending name as its own record (mirrors
            # the original per-page finalize behavior).
            if pending_name is not None:
                if current is not None:
                    records.append(current)
                name = pending_name
                if pending_fp is not None and pending_fp.get(
                    "strip_trailing_period_from_name", False
                ):
                    name = name.rstrip(".")
                current = _new_record(name, page_num)
                pending_name = None
                pending_fp = None

            if page_reset_record and current is not None:
                records.append(current)
                current = None

    if current is not None:
        records.append(current)

    post_pass = config.get("post_pass")
    if post_pass == "merge_short_records":
        records = _post_pass_merge_short_records(records, config)
    elif post_pass is not None:
        raise ValueError(f"Unknown post_pass '{post_pass}'")

    return records
