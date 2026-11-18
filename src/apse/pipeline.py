"""Portable orchestration; CASA runs in its own Python environment."""
import json
import os
import shutil
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path
from .catalog import filterSources, makeSourceList

@contextmanager
def _in_directory(path):
    """Legacy ALMA downloader writes to the process working directory."""
    old = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old)

def _casa_path(executable):
    executable = os.fspath(executable)
    found = shutil.which(executable)
    if found is None:
        raise FileNotFoundError("CASA executable not found: %s" % executable)
    return found

def run_images(pairs, output_dir=".", name="apse", casa_executable="casa",
               min_snr=6, fit_width=10, nmax_src=1000, zerooff_snr=3,
               run_filter=True, run_catalog=True):
    """Extract sources from (PB-corrected FITS, PB FITS) image pairs.

    Scientific parameters and algorithms match the original implementation.
    Writes raw, filtered and catalog JSON files; returns their paths.
    """
    pairs = [(str(Path(a).resolve()), str(Path(b).resolve())) for a,b in pairs]
    if not pairs:
        raise ValueError("At least one image pair is required")
    for a, b in pairs:
        if not Path(a).is_file() or not Path(b).is_file():
            raise FileNotFoundError("Missing FITS image pair: %s / %s" % (a, b))
    output = Path(output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    if not name or Path(name).name != name or name in (".", ".."):
        raise ValueError("name must be a simple filename prefix")
    raw = output / (name + ".sources.raw.json")
    filtered = output / (name + ".sources.json")
    catalog = output / (name + ".sourcelist.json")
    job = {"pairs": pairs, "output": str(raw), "parameters": {
        "min_snr": min_snr, "fit_width": fit_width,
        "nmax_src": nmax_src, "zerooff_snr": zerooff_snr}}
    backend = Path(__file__).with_name("casa_backend.py")
    # The installed package location is supplied explicitly to CASA's interpreter.
    package_root = str(backend.parent.parent)
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(filter(None, [package_root, env.get("PYTHONPATH", "")]))
    with tempfile.TemporaryDirectory(prefix="apse-job-") as tmp:
        job_file = Path(tmp) / "job.json"
        job_file.write_text(json.dumps(job))
        # Remove prior output to prevent stale results being mistaken for success.
        raw.unlink(missing_ok=True)
        env["APSE_JOB_FILE"] = str(job_file)
        subprocess.run([_casa_path(casa_executable), "--nogui", "--nologger",
                        "--nologfile", "-c", str(backend)],
                       cwd=str(output), env=env, check=True)
    if not raw.is_file():
        raise RuntimeError("CASA returned successfully but did not write " + str(raw))
    sources = json.loads(raw.read_text())
    results = {"raw": raw}
    if run_filter:
        sources = filterSources(sources)
        filtered.write_text(json.dumps(sources, indent=2))
        results["filtered"] = filtered
    if run_catalog:
        catalog.write_text(json.dumps(makeSourceList(sources), indent=2))
        results["catalog"] = catalog
    return results

def run_mous(mous_uid, output_dir=".", name=None, casa_executable="casa",
             mfs_only=True, sci_only=True, download_weblog=True, reuse_existing=True, **kwargs):
    """Download legacy ALMA products then process their PB-corrected FITS pairs.

    The downloader retains original behavior, including known security and
    compatibility limitations. Use only with trusted archive products.
    """
    from .alma import downloadImagesPerMOUS
    output = Path(output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    if reuse_existing and list(output.glob("*.pbcor.fits")):
        images = [p.name for p in sorted(output.glob("*.pbcor.fits"))]
        if any(not (output / p.replace(".pbcor.fits", ".pb.fits")).is_file() for p in images):
            raise RuntimeError("Incomplete existing FITS pairs; refusing to re-download interactively")
    else:
        with _in_directory(output):
            images = downloadImagesPerMOUS(mous_uid, mfsOnly=mfs_only,
                                           sciOnly=sci_only, PLweblog=download_weblog)
    pairs = [(output / image, output / image.replace(".pbcor.fits", ".pb.fits"))
             for image in images]
    safe_name = "member." + mous_uid.replace("://", "___").replace("/", "_")
    return run_images(pairs, output_dir=output, name=name or safe_name,
                      casa_executable=casa_executable, **kwargs)
