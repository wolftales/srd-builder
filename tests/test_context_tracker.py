from __future__ import annotations

from srd_builder.utils.context_tracker import ContextTracker


def test_context_tracker_propagates_latest_marker() -> None:
    tracker = ContextTracker(initial_category="gear")
    tracker.start_page(63)

    markers = [
        (100.0, {"category": "armor", "subcategory": "light"}),
        (200.0, {"category": "armor", "subcategory": "medium"}),
    ]

    context_before = tracker.context_for_position(markers, 150.0)
    assert context_before == {"category": "armor", "subcategory": "light"}

    tracker.propagate([marker for _, marker in markers])

    assert tracker.current() == {"category": "armor", "subcategory": "medium"}
    assert tracker.history[-1].page == 63
    assert tracker.history[-1].subcategory == "medium"
