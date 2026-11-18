"""Run ONLY the original v0.1.0 extraction function under CASA, without importing its optional dependencies."""
import ast
import json
import os
from pathlib import Path
import numpy as np
from casatools import image as iatool, quanta as qatool


def main():
    job = json.loads(Path(os.environ['APSE_LEGACY_JOB']).read_text())
    source = Path(job['legacy_source']).read_text()
    tree = ast.parse(source)
    matches = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == 'extractSourcesFromImage']
    if len(matches) != 1:
        raise RuntimeError('Expected one original extractSourcesFromImage function')
    namespace = {'np': np, 'os': os, 'iatool': iatool, 'qatool': qatool}
    exec(compile(ast.Module(body=matches, type_ignores=[]), job['legacy_source'], 'exec'), namespace)
    result = namespace['extractSourcesFromImage'](*job['pair'], **job['parameters'])
    Path(job['output']).write_text(json.dumps(result))
    print('Original v0.1.0 CASA extraction: %d sources' % len(result), flush=True)


if __name__ == '__main__':
    main()
