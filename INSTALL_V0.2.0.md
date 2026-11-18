# Applying this overlay to your existing repository

The archive does not include `.git`, your existing tests, or a license.
Unpack into your repository **on `develop`**, preserving existing files.
The original source is copied unmodified into `src/apse/legacy.py`; `APSE.py`
is replaced by a compatibility shim. The original is always recoverable from
Git tag `v0.1.0`.

```sh
cd ~/Projects/alma-point-source-extractor
git switch develop
git status --short
unzip -o ~/Downloads/apse-v0.2.0.zip -d .
source .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -p 'test_*.py' -v
apse --version
apse --help
# after checking results:
git add APSE.py src pyproject.toml README.md .gitignore .github tests INSTALL_V0.2.0.md
git commit -m 'refactor: package APSE v0.2.0 with portable CASA runner'
git tag -a v0.2.0-rc1 -m 'APSE v0.2.0 release candidate'
```

**Important:** This is a release candidate, not a scientifically verified final
release. Before tagging `v0.2.0`, test a real ALMA FITS pair end to end and
compare source catalogs against v0.1.0.
