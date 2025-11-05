"""Table extraction module.

Refactored from monolithic extract_tables.py into modular pattern-based extraction.
"""

from .extractor import TableExtractor, extract_tables_to_json
from .patterns import RawTable

__all__ = ["TableExtractor", "RawTable", "extract_tables_to_json"]
