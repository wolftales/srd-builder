try:
    from importlib.metadata import version

    __version__ = version("srd-builder")
except Exception:
    __version__ = "0.0.0+unknown"

__all__ = ["__version__"]
