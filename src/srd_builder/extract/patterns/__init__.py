"""Pattern-based extraction engines.

Public surface (re-exported here so existing imports
`from srd_builder.extract.patterns import X` continue to work):

    - RawTable
    - extract_by_config
    - extract_records_by_config

Per-pattern engines live in sibling modules
(standard_grid, split_column, ..., font_stateful_walk) and shared
helpers in _shared. The dispatch routing lives in _dispatch.
"""

from __future__ import annotations

from ._dispatch import extract_by_config, extract_records_by_config
from ._types import RawTable

__all__ = [
    "RawTable",
    "extract_by_config",
    "extract_records_by_config",
]
