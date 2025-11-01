"""Column mapper for equipment table parsing.

Maps table column positions to semantic field names using header analysis
and content heuristics. Handles varying table formats across armor, weapons,
and gear sections.
"""

from __future__ import annotations

import re


class ColumnMapper:
    """Maps table columns to semantic field names.

    Strategies (in order):
    1. Header-based: Parse actual column headers when available
    2. Heuristic: Analyze cell content patterns for headerless tables
    3. Category-based: Use known column patterns per equipment category
    """

    def __init__(self, category: str = "gear"):
        """Initialize indexer for equipment category.

        Args:
            category: Equipment category (armor, weapon, gear, mount, trade_good)
        """
        self.category = category
        self._column_map: dict[str, int] = {}

    def build_map(self, headers: list[str] | None, sample_row: list[str]) -> dict[str, int]:
        """Build column map from headers or sample row.

        Args:
            headers: Column header strings (if available)
            sample_row: Sample data row for heuristic detection

        Returns:
            Dictionary mapping field names to column indices
        """
        self._column_map = {}

        # Strategy 1: Use headers if available
        if headers:
            self._map_from_headers(headers)

        # Strategy 2: Fill gaps with heuristics
        if sample_row:
            self._fill_from_heuristics(sample_row)

        # Strategy 3: Apply category defaults
        self._apply_category_defaults(sample_row)

        return self._column_map.copy()

    def _map_from_headers(self, headers: list[str]) -> None:
        """Map columns from header row."""
        for idx, header in enumerate(headers):
            field_name = self._classify_header(header)
            if field_name and field_name not in self._column_map:
                self._column_map[field_name] = idx

    def _classify_header(self, header: str) -> str | None:
        """Classify header text to field name.

        Args:
            header: Raw header text

        Returns:
            Standardized field name or None if unrecognized
        """
        normalized = re.sub(r"[^a-z0-9]+", " ", header.lower()).strip()

        # Direct matches
        header_patterns = {
            "armor_class": ["armor class", "ac"],
            "cost": ["cost", "price"],
            "weight": ["weight", "wt"],
            "damage": ["damage", "dmg"],
            "properties": ["properties", "property", "special"],
            "strength": ["strength", "str", "str req"],
            "stealth": ["stealth"],
            "type": ["type", "category"],
            "range": ["range"],
        }

        for field, patterns in header_patterns.items():
            for pattern in patterns:
                if pattern in normalized:
                    return field

        return None

    def _fill_from_heuristics(self, row: list[str]) -> None:  # noqa: C901
        """Fill unmapped columns using content heuristics.

        Only maps columns not already identified from headers.
        """
        used_indices = set(self._column_map.values())

        # Map cost column (contains gp/sp/cp)
        if "cost" not in self._column_map:
            for idx, cell in enumerate(row):
                if idx in used_indices:
                    continue
                if self._is_cost_value(cell):
                    self._column_map["cost"] = idx
                    used_indices.add(idx)
                    break

        # Map weight column (contains "lb")
        if "weight" not in self._column_map:
            for idx, cell in enumerate(row):
                if idx in used_indices:
                    continue
                if "lb" in cell.lower() and not self._is_cost_value(cell):
                    self._column_map["weight"] = idx
                    used_indices.add(idx)
                    break

        # Map armor_class column (for armor category)
        if self.category == "armor" and "armor_class" not in self._column_map:
            for idx, cell in enumerate(row):
                if idx in used_indices:
                    continue
                if self._is_armor_class_value(cell):
                    self._column_map["armor_class"] = idx
                    used_indices.add(idx)
                    break

        # Map damage column (for weapon category)
        if self.category == "weapon" and "damage" not in self._column_map:
            for idx, cell in enumerate(row):
                if idx in used_indices:
                    continue
                if self._is_damage_value(cell):
                    self._column_map["damage"] = idx
                    used_indices.add(idx)
                    break

    def _apply_category_defaults(self, row: list[str]) -> None:
        """Apply category-specific column defaults.

        Last resort for columns that couldn't be detected.
        """
        # Assume first column is always the item name
        if row and "name" not in self._column_map:
            self._column_map["name"] = 0

        # Properties/special is usually the last column
        if "properties" not in self._column_map and len(row) > 2:
            # Don't map if last column looks like weight or cost
            last_col = row[-1]
            if not self._is_cost_value(last_col) and "lb" not in last_col.lower():
                self._column_map["properties"] = len(row) - 1

    def _is_cost_value(self, cell: str) -> bool:
        """Check if cell contains a cost value (e.g., '15 gp')."""
        return bool(re.search(r"\d+\s*(cp|sp|ep|gp|pp)", cell.lower()))

    def _is_armor_class_value(self, cell: str) -> bool:
        """Check if cell contains an armor class value."""
        normalized = cell.lower()
        # AC values: "13", "11 + Dex", "16 (Dex modifier)"
        if "ac" in normalized or "dex" in normalized:
            return True
        # Just a number between 10-20 in armor context
        if self.category == "armor" and re.match(r"^\d{2}$", cell.strip()):
            ac_val = int(cell.strip())
            return 10 <= ac_val <= 20
        return False

    def _is_damage_value(self, cell: str) -> bool:
        """Check if cell contains damage dice (e.g., '1d8 slashing')."""
        return bool(re.search(r"\d+d\d+", cell))

    def get(self, field: str, default: int | None = None) -> int | None:
        """Get column index for field name.

        Args:
            field: Field name (e.g., 'cost', 'weight')
            default: Default value if field not mapped

        Returns:
            Column index or default
        """
        return self._column_map.get(field, default)

    def has(self, field: str) -> bool:
        """Check if field is mapped to a column.

        Args:
            field: Field name to check

        Returns:
            True if field has a column mapping
        """
        return field in self._column_map

    @property
    def mapped_fields(self) -> list[str]:
        """Get list of all mapped field names."""
        return list(self._column_map.keys())

    def __repr__(self) -> str:
        """Debug representation."""
        fields = ", ".join(f"{k}={v}" for k, v in sorted(self._column_map.items()))
        return f"ColumnMapper(category={self.category!r}, {fields})"
