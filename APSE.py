"""Compatibility module for the legacy APSE public API.

New code should import from the ``apse`` package instead.
"""
from apse.legacy import (downloadImagesPerMOUS, fetch_url, readPLweblog,
    readPLweblogPage, extractSourcesFromImage, create_ellipse, filterSources,
    makeSourceList, extractMetadata)
from apse.pipeline import run_images, run_mous

def extractSourcesPerMOUS(MOUSuid, runFilterSources=True, runMakeSourceList=True,
                          casa_executable="casa", output_dir="."):
    return run_mous(MOUSuid, output_dir=output_dir,
                    casa_executable=casa_executable,
                    run_filter=runFilterSources,
                    run_catalog=runMakeSourceList)

def extractSources(uidListFile="", casa_executable="casa", output_dir="."):
    """Process all MOUS IDs, propagate failures, return output paths."""
    from pathlib import Path
    identifiers = [line.strip() for line in Path(uidListFile).read_text().splitlines()
                   if line.strip() and not line.lstrip().startswith("#")]
    return [extractSourcesPerMOUS(uid, casa_executable=casa_executable,
                                  output_dir=output_dir) for uid in identifiers]
