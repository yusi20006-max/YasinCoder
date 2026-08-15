"""Public package interface for YasinCoder.

The implementation remains split into the project's stable top-level modules
and subpackages for backwards compatibility, while this package provides a
real importable distribution boundary.
"""
from __future__ import annotations

try:
    from importlib.metadata import version as _distribution_version

    __version__ = _distribution_version("yasincoder")
except Exception:  # pragma: no cover - source-tree fallback
    __version__ = "0.1.0"

__all__ = ["__version__"]
