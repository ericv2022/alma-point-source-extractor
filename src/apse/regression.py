"""Opt-in scientific regression on the canonical ALMA MOUS; no network in unit tests."""
import argparse
import json
import math
import os
from pathlib import Path
import re
import sys

UID = "uid://A001/X121/X46c"
SPWS = (0, 1, 2, 3)
PARAMETERS = {"min_snr": 6, "fit_width": 10, "nmax_src": 1000, "zerooff_snr": 3}


def discover_pairs(folder):
    folder = Path(folder)
    pairs = []
    for spw in SPWS:
        images = sorted(folder.glob("*.spw%d_*.pbcor.fits" % spw))
        if len(images) != 1:
            raise RuntimeError("Expected exactly one SPW%d science FITS in %s; found %d" % (spw, folder, len(images)))
        science = images[0]
        pb = science.with_name(science.name.replace(".pbcor.fits", ".pb.fits"))
        if not pb.is_file():
            raise FileNotFoundError("Missing primary beam: %s" % pb)
        pairs.append((science, pb))
    return pairs


def ensure_data(folder, offline=False):
    folder = Path(folder).expanduser().resolve()
    folder.mkdir(parents=True, exist_ok=True)
    try:
        return discover_pairs(folder)
    except (RuntimeError, FileNotFoundError):
        if offline:
            raise
    # The validated legacy downloader writes into cwd and has no cache-aware
    # completeness check; only invoke it if no FITS files are present.
    if list(folder.glob("*.fits")):
        raise RuntimeError("Incomplete FITS cache at %s. Repair or clear it manually; refusing interactive overwrite." % folder)
    from .alma import downloadImagesPerMOUS
    from .pipeline import _in_directory
    with _in_directory(folder):
        downloadImagesPerMOUS(UID, mfsOnly=True, sciOnly=True, PLweblog=False)
    return discover_pairs(folder)


def compact_source(source):
    direction = source["shape"]["direction"]
    return {
        "ra_rad": float(direction["m0"]["value"]),
        "dec_rad": float(direction["m1"]["value"]),
        "flux_jy": float(source["flux"]["value"][0]),
        "fluxerr_jy": float(source["flux"]["error"][0]),
        "peak_jy_per_beam": float(source["peak"]["value"]),
        "ispoint": bool(source["ispoint"]),
    }


def summarize(folder):
    folder = Path(folder)
    result = {"schema": 1, "uid": UID, "parameters": PARAMETERS,
              "spws": {}, "total_raw": 0, "total_filtered": 0}
    for spw in SPWS:
        prefix = "regression_spw%d" % spw
        raw = json.loads((folder / (prefix + ".sources.raw.json")).read_text())
        filtered = json.loads((folder / (prefix + ".sources.json")).read_text())
        # Order is not meaningful; sort by celestial position for stable comparisons.
        sources = sorted((compact_source(s) for s in filtered.values()),
                         key=lambda s: (s["ra_rad"], s["dec_rad"]))
        result["spws"][str(spw)] = {"raw_count": len(raw),
                                    "filtered_count": len(filtered), "sources": sources}
        result["total_raw"] += len(raw)
        result["total_filtered"] += len(filtered)
    return result


def compare(actual, expected, position_tolerance_arcsec=0.05,
            flux_relative_tolerance=0.02, flux_absolute_tolerance_jy=1e-6):
    errors = []
    if actual.get("uid") != expected.get("uid"):
        errors.append("MOUS UID mismatch")
    if actual.get("parameters") != expected.get("parameters"):
        errors.append("Extraction parameters differ")
    for spw in SPWS:
        key = str(spw)
        a = actual["spws"].get(key)
        b = expected.get("spws", {}).get(key)
        if a is None or b is None:
            errors.append("SPW%s missing" % key)
            continue
        for count in ("raw_count", "filtered_count"):
            if a[count] != b[count]:
                errors.append("SPW%s %s: %s != %s" % (key, count, a[count], b[count]))
        if len(a["sources"]) != len(b["sources"]):
            continue
        # Sort by sky position, not by source IDs.
        for i, (x, y) in enumerate(zip(a["sources"], b["sources"])):
            separation_arcsec = math.hypot((x["ra_rad"]-y["ra_rad"])*math.cos(y["dec_rad"]),
                                           x["dec_rad"]-y["dec_rad"]) * 206264.806247
            if separation_arcsec > position_tolerance_arcsec:
                errors.append("SPW%s source %d position: %.5f arcsec" % (key, i, separation_arcsec))
            if x["ispoint"] != y["ispoint"]:
                errors.append("SPW%s source %d point classification changed" % (key, i))
            for field in ("flux_jy", "fluxerr_jy", "peak_jy_per_beam"):
                if not math.isclose(x[field], y[field], rel_tol=flux_relative_tolerance,
                                    abs_tol=flux_absolute_tolerance_jy):
                    errors.append("SPW%s source %d %s: %g != %g" % (key, i, field, x[field], y[field]))
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description="Local opt-in CASA scientific regression")
    parser.add_argument("--data-dir", default=str(Path.home() / ".cache" / "apse" / "uid___A001_X121_X46c"))
    parser.add_argument("--casa", default="casa")
    parser.add_argument("--offline", action="store_true", help="Never download; require cached FITS")
    parser.add_argument("--reference", default=str(Path(__file__).resolve().parents[2] / "tests" / "reference" / "mous_A001_X121_X46c.json"))
    parser.add_argument("--write-candidate", metavar="PATH", help="Write candidate reference for independent legacy verification; does not bless it")
    args = parser.parse_args(argv)
    from .pipeline import run_images
    folder = Path(args.data_dir).expanduser().resolve()
    pairs = ensure_data(folder, offline=args.offline)
    for spw, pair in zip(SPWS, pairs):
        print("Extracting SPW%d" % spw, flush=True)
        run_images([pair], output_dir=folder, name="regression_spw%d" % spw,
                   casa_executable=args.casa, **PARAMETERS)
    actual = summarize(folder)
    if args.write_candidate:
        target = Path(args.write_candidate).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(actual, indent=2, sort_keys=True) + "\n")
        print("Candidate written to %s (NOT a validated legacy reference)" % target)
        return 0
    reference = Path(args.reference).expanduser().resolve()
    if not reference.is_file():
        print("No independently verified legacy reference at %s" % reference, file=sys.stderr)
        print("Run with --write-candidate PATH for review; do not auto-approve new results.", file=sys.stderr)
        return 2
    expected = json.loads(reference.read_text())
    errors = compare(actual, expected)
    if errors:
        print("SCIENTIFIC REGRESSION FAILED:", file=sys.stderr)
        for error in errors:
            print(" - " + error, file=sys.stderr)
        return 1
    print("SCIENTIFIC REGRESSION PASSED: %d raw, %d filtered sources over 4 SPWs" %
          (actual["total_raw"], actual["total_filtered"]))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
