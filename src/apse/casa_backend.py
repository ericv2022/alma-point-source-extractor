"""Executed by CASA with a JSON job file as the sole argument."""
import json
import os
import sys
from pathlib import Path

def main():
    if not os.environ.get("APSE_JOB_FILE"):
        raise SystemExit("APSE_JOB_FILE environment variable is required")
    job_path = Path(os.environ["APSE_JOB_FILE"]).resolve()
    job = json.loads(job_path.read_text())
    from apse.legacy import extractSourcesFromImage
    result = {}
    next_id = 0
    for pbcor, pb in job["pairs"]:
        if not Path(pbcor).is_file() or not Path(pb).is_file():
            raise FileNotFoundError("Missing FITS image pair: %s / %s" % (pbcor, pb))
        sources = extractSourcesFromImage(pbcor, pb, **job["parameters"])
        for source in sources.values():
            result[next_id] = source
            next_id += 1
    output = Path(job["output"])
    temporary = output.with_name(output.name + ".tmp")
    with temporary.open("w") as handle:
        json.dump(result, handle)
    temporary.replace(output)
    print("APSE CASA extraction completed: %d fitted sources" % len(result))

if __name__ == "__main__":
    main()
