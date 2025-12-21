"""Utilities for tracking section context across PDF pages."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(slots=True)
class ContextSnapshot:
    """Historical snapshot of extraction context."""

    page: int
    category: str | None
    subcategory: str | None


class ContextTracker:
    """Track hierarchical context (category/subcategory) across pages."""

    def __init__(self, initial_category: str | None = None) -> None:
        self._category = initial_category
        self._subcategory: str | None = None
        self._page: int | None = None
        self.history: list[ContextSnapshot] = []

    def start_page(self, page_num: int) -> None:
        """Set the active page before processing begins."""

        self._page = page_num

    def current(self) -> dict[str, str | None]:
        """Return the currently active context."""

        return {"category": self._category, "subcategory": self._subcategory}

    def context_for_position(
        self,
        markers: Iterable[tuple[float, dict[str, str | None]]],
        table_y: float,
    ) -> dict[str, str | None]:
        """Derive context for an element located at the given vertical position."""

        context = self.current()
        for marker_y, marker_section in markers:
            if marker_y < table_y:
                context = self._apply_marker(context, marker_section)
        return context

    def propagate(self, marker_sections: Iterable[dict[str, str | None]]) -> None:
        """Update persistent context after processing a page."""

        for section in marker_sections:
            self._category = section.get("category", self._category)
            if section.get("category"):
                self._subcategory = section.get("subcategory")
            elif section.get("subcategory") is not None:
                self._subcategory = section.get("subcategory")

        self._record_history()

    def _apply_marker(
        self, context: dict[str, str | None], marker: dict[str, str | None]
    ) -> dict[str, str | None]:
        result = dict(context)
        category = marker.get("category")
        subcategory = marker.get("subcategory")

        if category:
            result["category"] = category
            result["subcategory"] = subcategory
        elif subcategory is not None:
            result["subcategory"] = subcategory

        return result

    def _record_history(self) -> None:
        self.history.append(
            ContextSnapshot(
                page=self._page if self._page is not None else -1,
                category=self._category,
                subcategory=self._subcategory,
            )
        )
