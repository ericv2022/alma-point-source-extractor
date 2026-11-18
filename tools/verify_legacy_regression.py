"""Independently run original APSE v0.1.0 against the new extractor on the same cached MOUS."""
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from apse.regression import UID, SPWS, PARAMETERS, compact_source, compare, discover_pairs, ensure_data


def original_functions(source):
    """Load original filtering verbatim, without importing the legacy file's optional dependencies."""
    from shapely.geometry import Point
    from shapely.affinity import scale, rotate
    tree = ast.parse(source)
    wanted = ('create_ellipse', 'filterSources')
    functions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in wanted]
    if {f.name for f in functions} != set(wanted):
        raise RuntimeError('Original source missing filtering functions')
    namespace = {'Point': Point, 'scale': scale, 'rotate': rotate}
    exec(compile(ast.Module(body=functions, type_ignores=[]), '<original APSE.py>', 'exec'), namespace)
    return namespace['filterSources']


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data-dir', default='data/uid___A001_X121_X46c')
    p.add_argument('--casa', default='/usr/local/bin/casa')
    p.add_argument('--offline', action='store_true', default=False)
    p.add_argument('--legacy-ref', default='main:APSE.py', help='git revision:path of validated original APSE')
    p.add_argument('--reference', default='tests/reference/mous_A001_X121_X46c.json')
    p.add_argument('--candidate', default='/tmp/apse-regression-candidate.json')
    args = p.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    folder = (root / args.data_dir).resolve()
    pairs = ensure_data(folder, offline=args.offline)
    original_bytes = subprocess.check_output(['git', 'show', args.legacy_ref], cwd=root)
    source = original_bytes.decode('utf-8')
    filter_sources = original_functions(source)
    original_sha = hashlib.sha256(original_bytes).hexdigest()
    original_commit = subprocess.check_output(['git', 'rev-parse', args.legacy_ref.split(':')[0]], cwd=root, text=True).strip()
    with tempfile.TemporaryDirectory(prefix='apse-legacy-compare-') as tmp:
        temp = Path(tmp)
        legacy_file = temp / 'APSE-v0.1.0-original.py'
        legacy_file.write_bytes(original_bytes)
        baseline = {'schema': 1, 'uid': UID, 'parameters': PARAMETERS, 'spws': {}, 'total_raw': 0, 'total_filtered': 0}
        runner = root / 'tools' / 'legacy_casa_runner.py'
        for spw, pair in zip(SPWS, pairs):
            output = temp / ('legacy_spw%d.json' % spw)
            job = temp / 'job.json'
            job.write_text(json.dumps({'legacy_source': str(legacy_file), 'pair': [str(p) for p in pair], 'parameters': PARAMETERS, 'output': str(output)}))
            env = os.environ.copy()
            env['APSE_LEGACY_JOB'] = str(job)
            print('Original v0.1.0: SPW%d' % spw, flush=True)
            subprocess.run([args.casa, '--nogui', '--nologger', '--nologfile', '-c', str(runner)], cwd=str(temp), env=env, check=True)
            raw = json.loads(output.read_text())
            filtered = filter_sources(raw)
            sources = sorted((compact_source(s) for s in filtered.values()), key=lambda s: (s['ra_rad'], s['dec_rad']))
            baseline['spws'][str(spw)] = {'raw_count': len(raw), 'filtered_count': len(filtered), 'sources': sources}
            baseline['total_raw'] += len(raw)
            baseline['total_filtered'] += len(filtered)
        print('New v0.2.0: all four SPWs', flush=True)
        candidate_path = (root / args.candidate).resolve()
        subprocess.run([sys.executable, '-m', 'apse.regression', '--offline', '--data-dir', str(folder), '--casa', args.casa, '--write-candidate', str(candidate_path)], cwd=root, check=True)
        candidate = json.loads(candidate_path.read_text())
        errors = compare(candidate, baseline)
        if errors:
            print('FAILED: original and new extraction differ:', file=sys.stderr)
            for error in errors:
                print(' - ' + error, file=sys.stderr)
            return 1
        baseline['provenance'] = {
            'origin': 'Original v0.1.0 extractSourcesFromImage and filterSources functions from git',
            'git_ref': args.legacy_ref,
            'git_commit': original_commit,
            'original_source_sha256': original_sha,
            'generated_utc': datetime.now(timezone.utc).isoformat(),
            'casa_executable': args.casa,
            'image_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for pair in pairs for p in pair},
            'comparison': 'per-SPW raw/filtered counts, sky positions (0.05 arcsec), fluxes (2% or 1 microJy), point classification',
        }
        target = (root / args.reference).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            old = json.loads(target.read_text())
            prior_errors = compare(baseline, old)
            if prior_errors:
                print('FAILED: existing committed reference differs from original run:', file=sys.stderr)
                for error in prior_errors: print(' - ' + error, file=sys.stderr)
                return 1
            print('PASS: existing reference matches original and new implementations; not overwritten')
        else:
            target.write_text(json.dumps(baseline, indent=2, sort_keys=True) + '\n')
            print('PASS: original v0.1.0 matches new v0.2.0. Verified legacy reference written to %s' % target)
        print('Counts: %d raw, %d filtered over four SPWs' % (baseline['total_raw'], baseline['total_filtered']))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
