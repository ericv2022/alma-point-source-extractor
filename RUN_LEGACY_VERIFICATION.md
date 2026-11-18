# Original APSE v0.1.0 versus v0.2.0 scientific verification

The reference is **not** derived by blessing the new implementation's output. The script extracts the original `extractSourcesFromImage`, `create_ellipse`, and `filterSources` functions directly from `main:APSE.py` via `git show`, executes the original extractor under CASA, executes the original filter in the host venv, then runs the new regression and compares all four SPWs.

```bash
cd ~/Projects/alma-point-source-extractor
source .venv/bin/activate
unzip -o ~/Downloads/apse-legacy-verification.zip -d .
python tools/verify_legacy_regression.py --offline --data-dir data/uid___A001_X121_X46c --casa /usr/local/bin/casa
```

If `main:APSE.py` is not the original validated source, use `--legacy-ref v0.1.0:APSE.py` (if the tag exists) or the correct immutable commit and path. Do not substitute the new refactored `src/apse/legacy.py` for the original.

On success, commit `tests/reference/mous_A001_X121_X46c.json` and `tools/`. The FITS images are never committed. Later run `apse regression --offline --data-dir data/uid___A001_X121_X46c --casa /usr/local/bin/casa`.

The first successful run verifies algorithmic equivalence at the configured tolerances, not independent astronomical truth. CASA-version sensitivity and broader source completeness still warrant testing.
