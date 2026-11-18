# APSE v0.3.0 — focused maintenance release

- The CASA fitting function is copied unchanged from the validated legacy code
  into `casa_extraction.py`; the CASA backend imports it directly.
- Catalog functions are copied unchanged into `catalog.py`; importing APSE no
  longer loads the legacy downloader and its optional dependency warnings.
- Legacy implementation is retained for independent verification.
- Adds AST equivalence tests for the four scientific functions.
- Updates README, package version, and instructions.

**Release only after both unit tests and real CASA regression pass.**
This release is not a complete removal of the legacy module or downloader.
