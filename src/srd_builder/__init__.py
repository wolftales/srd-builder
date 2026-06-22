"""srd-builder package root.

``__version__`` is read from ``pyproject.toml`` when running from source
so editing the version in pyproject takes effect at the next Python
process start — no ``pip install -e .`` step required. When running
from an installed wheel (where pyproject.toml is not shipped), it falls
back to ``importlib.metadata`` which reads the installed ``.dist-info``.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

_PYPROJECT = Path(__file__).resolve().parent.parent.parent / "pyproject.toml"


def _read_version() -> str:
    if _PYPROJECT.is_file():
        try:
            with _PYPROJECT.open("rb") as fh:
                data = tomllib.load(fh)
            return str(data["project"]["version"])
        except OSError, KeyError, TypeError, tomllib.TOMLDecodeError:
            pass
    try:
        from importlib.metadata import version

        return version("srd-builder")
    except Exception:
        return "0.0.0+unknown"


__version__ = _read_version()

__all__ = ["__version__"]
