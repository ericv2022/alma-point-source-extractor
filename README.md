# APSE — ALMA Point Source Extractor

**Version 0.3.0**. The original v0.1.0 scientific algorithms are preserved.
Version 0.2.0 was validated against the original on ALMA MOUS
`uid://A001/X121/X46c` (four SPWs, one fitted and filtered source).
Version 0.3.0 isolates CASA fitting and catalog operations from the legacy
downloader; the v0.3.0 scientific regression must pass before release.

## Installation

Use a dedicated virtual environment (Python 3.9+):

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

CASA 6.7 (or a compatible version) must be installed separately and available
on PATH, or specified with `--casa /path/to/casa`. CASA has its own Python.
Do **not** install APSE dependencies into CASA. The runner adds the installed
APSE package path to CASA's `PYTHONPATH` for backend execution.

## Local FITS image extraction

```sh
apse images --pair observation.pbcor.fits observation.pb.fits \
  --output-dir results --name observation --casa /usr/local/bin/casa
```

Multiple `--pair` arguments are supported. Outputs:
`observation.sources.raw.json`, `observation.sources.json`, and
`observation.sourcelist.json`. Original scientific defaults: `min_snr=6`,
`fit_width=10`, `nmax_src=1000`, `zerooff_snr=3`.

## Download an ALMA MOUS

```sh
apse mous 'uid://A001/X123/X456' --output-dir results
```

This uses the **legacy** ALMA downloader. It is not yet hardened against
untrusted archive contents or changes in ALMA's data-link service. The
local-image workflow is recommended for initial validation.

## Python API

```python
from apse import run_images, filterSources, makeSourceList
outputs = run_images([("observation.pbcor.fits", "observation.pb.fits")],
                     output_dir="results", casa_executable="casa")
```

`import APSE` remains available as a compatibility module when run from the
repository root. Legacy `extractSources` and `extractSourcesPerMOUS` are
redirected to the new runner; their return values and file naming may differ.
Other original functions are retained in `apse.legacy`.

## Tests

```sh
python -m unittest discover -s tests -p 'test_*.py' -v
casa --nogui --nologger --nologfile -c tests/casa_smoke.py
```

## Known scientific / technical issues

- The isolation ellipse conversion (`3*bMaj/pixelsperarcsec`) needs verification;
  the original source-extraction fit uses multiplication for similar units.
- Isolation rejects both members of an overlapping pair and compares pixel
  positions without checking that they share a WCS.
- `makeSourceList(addKeywords=True)` does not add metadata in the original code.
- The original extraction does not validate convergence of the second
  uncorrected-image fit before using its offset.
- The original ALMA downloader uses shell gunzip and unguarded tar extraction;
  do not use with untrusted archives.
- Original metadata ROBUST regular expression has a capturing-group defect.
- No end-to-end ALMA-image regression dataset is bundled; scientific equivalence
  must be checked before declaring v0.2.0 scientifically validated.

## License

No license was provided with the source archive. The repository owner must
choose a license before third-party redistribution.

## Scientific regression (release gate)

Run the unit tests, then run the real CASA regression against the committed
legacy reference. The FITS images are cached locally and **not committed**.

```sh
python -m unittest discover -s tests -p 'test_*.py' -v
apse regression --offline --data-dir data/uid___A001_X121_X46c --casa /usr/local/bin/casa
```

Omit `--offline` to allow downloading the reference MOUS when the cache is
missing. The small verified JSON reference is in `tests/reference/`.

Version 0.3.0 changes code organization, not the source-fitting or filtering
algorithms. The legacy implementation remains in `apse.legacy` for comparison.
