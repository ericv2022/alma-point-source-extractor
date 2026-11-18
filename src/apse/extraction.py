"""Compatibility interface for CASA source fitting.

Import this module only inside the CASA Python environment.
"""
from .casa_extraction import extractSourcesFromImage
__all__ = ["extractSourcesFromImage"]
