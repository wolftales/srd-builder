"""font_stateful_walk pattern engine.

Header detection + ordered span rules + intra-record state machine.
Supports flat subfields, span-list buckets, per-rule guards,
text-driven state transitions, cross-page record carry, and a
merge_nameless_into_previous post-pass.
"""

from __future__ import annotations

from typing import Any

from ._shared import (
    _bucket_text,
    _make_span_block,
    _span_matches_predicate,
)


def _guard_passes(
    guard: dict[str, Any] | None,
    record: dict[str, Any] | None,
    state: str,
) -> bool:
    """Evaluate a rule's optional guard. Returns False if the rule must skip."""
    if not guard:
        return True
    if guard.get("require_current_record", False) and record is None:
        return False
    if "state_in" in guard and (record is None or state not in guard["state_in"]):
        return False
    subfield_empty = guard.get("subfield_empty")
    if subfield_empty is not None:
        if record is None:
            return False
        if record.get(subfield_empty, "") != "":
            return False
    return True


def _apply_state_transitions(
    record: dict[str, Any], state: str, transitions: list[dict[str, Any]]
) -> str:
    """Check each transition; return the (possibly new) state."""
    for t in transitions:
        if t.get("when_state") != state:
            continue
        trig = t.get("trigger", {})
        btc = trig.get("bucket_text_contains")
        if btc and btc["text"] in _bucket_text(record, btc["bucket"]):
            return t["to_state"]
    return state


def _new_stateful_record(
    name: str,
    page_num: int,
    subfields: list[str],
    buckets: list[str],
    track_pages_list: bool,
) -> dict[str, Any]:
    rec: dict[str, Any] = {"name": name, "page": page_num}
    if track_pages_list:
        rec["pages"] = [page_num]
    for sf in subfields:
        rec[sf] = ""
    for b in buckets:
        rec[b] = []
    return rec


def _carry_predicate_holds(pred: dict[str, Any] | None, record: dict[str, Any] | None) -> bool:
    """Evaluate carry_if. Returns True iff the record should be carried."""
    if pred is None or record is None:
        return False
    if pred.get("name_nonempty", False) and not record.get("name", "").strip():
        return False
    bucket_empty = pred.get("bucket_empty")
    if bucket_empty is not None and record.get(bucket_empty):
        return False
    return True


def _keep_predicate_holds(pred: dict[str, Any] | None, record: dict[str, Any]) -> bool:
    if pred is None:
        return True
    if pred.get("name_nonempty", False) and not record.get("name", "").strip():
        return False
    return True


def _post_pass_merge_nameless_into_previous(
    records: list[dict[str, Any]],
    subfields: list[str],
    buckets: list[str],
    track_pages_list: bool,
) -> list[dict[str, Any]]:
    """Merge nameless records (continuations) into the previous record.

    Concatenates each bucket, extends each subfield only if the previous
    subfield is empty, and appends the nameless record's page to pages.
    Nameless records with no previous record are dropped (matches original
    extract_spells behavior).
    """
    merged: list[dict[str, Any]] = []
    for rec in records:
        if rec.get("name", "").strip():
            merged.append(rec)
            continue
        if not merged:
            continue  # orphan continuation; drop
        prev = merged[-1]
        for b in buckets:
            prev[b].extend(rec.get(b, []))
        for sf in subfields:
            if prev.get(sf, "") == "" and rec.get(sf, ""):
                prev[sf] = rec[sf]
        if track_pages_list:
            p = rec.get("page")
            if p is not None and p not in prev.get("pages", []):
                prev.setdefault("pages", []).append(p)
    return merged


def _extract_font_stateful_walk(
    pdf_path: str,
    pages: list[int],
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    """Header + ordered span-rule walk with intra-record state machine.

    Config schema (see also patterns.py header for the full vocabulary):
        {
            "pattern_type": "font_stateful_walk",
            "header_fingerprint": {<span predicate>},
            "subfields": ["level_and_school", ...],
            "buckets":   ["header_blocks", "description_blocks", ...],
            "initial_state": "header",
            "span_rules": [
                {
                    "match": {<span predicate>; {} = always},
                    "guard": {                              # optional
                        "require_current_record": True,
                        "state_in": ["header"],
                        "subfield_empty": "level_and_school",
                    },
                    "if_no_record": "skip" | "create_nameless",  # default "skip"
                    "action": {
                        "type": "set_subfield",
                        "name": "<subfield>",
                        "also_append_to": "<bucket>",       # optional
                        "attach": {<key>: <value or sentinel>, ...},
                    },
                    # OR
                    "action": {
                        "type": "append_to_bucket",
                        "bucket": "<bucket>",
                        "attach": {...},
                    },
                    # OR
                    "action": {
                        "type": "append_to_state_bucket",
                        "state_buckets": {"<state>": "<bucket>", ...},
                        "attach": {...},
                    },
                },
                ...
            ],
            "state_transitions": [
                {
                    "when_state": "header",
                    "trigger": {"bucket_text_contains":
                                {"bucket": "header_blocks", "text": "Duration:"}},
                    "to_state": "description",
                },
            ],
            "carry_if": {                                   # optional
                "name_nonempty": True,
                "bucket_empty": "description_blocks",
            },
            "post_pass": "merge_nameless_into_previous",    # optional
            "keep_if": {"name_nonempty": True},             # optional final filter
            "track_pages_list": True,                       # default False
        }

    Sentinel values usable inside any `attach` dict:
        "$bold_from_font"   → bool from font name
        "$italic_from_font" → bool from font name
    """
    from pathlib import Path

    from ...utils.pdf_probe import open_pdf

    header_fp = config["header_fingerprint"]
    subfields: list[str] = config.get("subfields", [])
    buckets: list[str] = config["buckets"]
    initial_state: str = config.get("initial_state", "default")
    span_rules: list[dict[str, Any]] = config.get("span_rules", [])
    state_transitions: list[dict[str, Any]] = config.get("state_transitions", [])
    carry_if = config.get("carry_if")
    post_pass = config.get("post_pass")
    keep_if = config.get("keep_if")
    track_pages_list: bool = config.get("track_pages_list", False)

    records: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    state: str = initial_state

    def commit_current() -> None:
        nonlocal current, state
        if current is not None:
            records.append(current)
        current = None
        state = initial_state

    with open_pdf(Path(pdf_path)) as pdf:
        for page_num in pages:
            page = pdf[page_num - 1]
            for block in page.get_text("dict").get("blocks", []):
                if block.get("type") != 0:
                    continue
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text = span.get("text", "").strip()
                        if not text:
                            continue

                        # Header detection always takes precedence.
                        if _span_matches_predicate(span, header_fp):
                            commit_current()
                            current = _new_stateful_record(
                                text, page_num, subfields, buckets, track_pages_list
                            )
                            state = initial_state
                            continue

                        # Evaluate span_rules in order; first match wins.
                        for rule in span_rules:
                            if not _span_matches_predicate(span, rule.get("match", {})):
                                continue
                            if not _guard_passes(rule.get("guard"), current, state):
                                continue
                            if current is None:
                                if rule.get("if_no_record", "skip") != "create_nameless":
                                    break  # rule matched but cannot fire; stop
                                current = _new_stateful_record(
                                    "", page_num, subfields, buckets, track_pages_list
                                )
                                state = initial_state
                            action = rule["action"]
                            atype = action["type"]
                            attach = action.get("attach", {})
                            block_dict = _make_span_block(span, attach)
                            if atype == "set_subfield":
                                current[action["name"]] = text
                                also = action.get("also_append_to")
                                if also:
                                    current[also].append(block_dict)
                            elif atype == "append_to_bucket":
                                current[action["bucket"]].append(block_dict)
                            elif atype == "append_to_state_bucket":
                                bucket = action["state_buckets"].get(state)
                                if bucket is None:
                                    raise ValueError(
                                        f"append_to_state_bucket: no bucket mapped "
                                        f"for state '{state}'"
                                    )
                                current[bucket].append(block_dict)
                            else:
                                raise ValueError(f"Unknown rule action type '{atype}'")
                            # Only run state transitions if the rule asked for it.
                            # Mirrors the original extract_spells behavior where the
                            # "Duration:" trigger only takes effect after a regular-text
                            # append, not after a field-label append that happened to
                            # contain the trigger text.
                            if rule.get("check_state_transitions_after", False):
                                state = _apply_state_transitions(current, state, state_transitions)
                            break  # rule matched; do not evaluate further rules

            # End of page: decide whether to carry the current record.
            if current is not None:
                if _carry_predicate_holds(carry_if, current):
                    # Keep current + state intact for next page.
                    pass
                else:
                    commit_current()

    if current is not None:
        records.append(current)

    if post_pass == "merge_nameless_into_previous":
        records = _post_pass_merge_nameless_into_previous(
            records, subfields, buckets, track_pages_list
        )
    elif post_pass is not None and post_pass != "merge_nameless_into_previous":
        raise ValueError(f"Unknown post_pass '{post_pass}' for font_stateful_walk")

    if keep_if is not None:
        records = [r for r in records if _keep_predicate_holds(keep_if, r)]

    return records
