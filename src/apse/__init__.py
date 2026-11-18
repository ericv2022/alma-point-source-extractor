"""APSE package. Keep package import lightweight for CASA's Python environment."""
__version__ = "0.3.0"
__all__ = ["create_ellipse", "filterSources", "makeSourceList", "run_images", "run_mous"]

def __getattr__(name):
    if name in ("create_ellipse", "filterSources", "makeSourceList"):
        from . import catalog
        return getattr(catalog, name)
    if name in ("run_images", "run_mous"):
        from . import pipeline
        return getattr(pipeline, name)
    raise AttributeError("module 'apse' has no attribute %r" % name)
