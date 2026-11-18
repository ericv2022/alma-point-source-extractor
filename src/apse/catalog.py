"""Legacy-compatible source filtering and catalog creation.

The original algorithms are intentionally unchanged in v0.2.0.
"""
from .legacy import create_ellipse, filterSources, makeSourceList
__all__ = ["create_ellipse", "filterSources", "makeSourceList"]
