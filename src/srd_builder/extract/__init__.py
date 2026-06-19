"""PDF extraction.

Two layers under this package:
- top level (``extract/``) — config-driven table extraction engine
  (``engine.py``, ``patterns.py``, ``table_targets.py``,
  ``extraction_metadata.py``, ``text_parser_utils.py``). Named ``engine``
  for cross-stage consistency with ``postprocess/engine.py``.
- ``extract/datasets/`` — bespoke per-dataset PDF extractors that
  predate the engine. Will migrate onto the engine pattern as feature
  work allows.

Shared prose utilities live in ``utils/prose.py``.
"""

from .engine import TableExtractor, extract_tables_to_json
from .patterns import RawTable

__all__ = ["TableExtractor", "RawTable", "extract_tables_to_json"]
