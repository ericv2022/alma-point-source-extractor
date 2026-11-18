"""Command-line entry point."""
import argparse
from .pipeline import run_images, run_mous

def main(argv=None):
    parser = argparse.ArgumentParser(prog="apse", description="ALMA Point Source Extractor")
    parser.add_argument("--version", action="version", version="APSE 0.2.0")
    sub = parser.add_subparsers(dest="command", required=True)
    images = sub.add_parser("images", help="Extract from local FITS pairs")
    images.add_argument("--pair", nargs=2, action="append", required=True,
                        metavar=("PBCOR_FITS", "PB_FITS"))
    mous = sub.add_parser("mous", help="Download and process an ALMA MOUS")
    mous.add_argument("uid")
    regression = sub.add_parser("regression", help="Opt-in local CASA scientific regression")
    for p in (images, mous):
        p.add_argument("--output-dir", default=".")
        p.add_argument("--name")
        p.add_argument("--casa", default="casa")
        p.add_argument("--min-snr", type=float, default=6)
        p.add_argument("--fit-width", type=int, default=10)
        p.add_argument("--nmax-src", type=int, default=1000)
        p.add_argument("--zerooff-snr", type=float, default=3)
        p.add_argument("--no-filter", action="store_true")
        p.add_argument("--no-catalog", action="store_true")
    args, extra = parser.parse_known_args(argv)
    if args.command == "regression":
        from .regression import main as regression_main
        return regression_main(extra)
    if extra:
        parser.error("unrecognized arguments: " + " ".join(extra))
    common = dict(output_dir=args.output_dir, casa_executable=args.casa,
                  min_snr=args.min_snr, fit_width=args.fit_width,
                  nmax_src=args.nmax_src, zerooff_snr=args.zerooff_snr,
                  run_filter=not args.no_filter, run_catalog=not args.no_catalog)
    if args.name is not None:
        common["name"] = args.name
    if args.command == "images":
        result = run_images(args.pair, **common)
    else:
        result = run_mous(args.uid, **common)
    for label, path in result.items():
        print("%s: %s" % (label, path))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
