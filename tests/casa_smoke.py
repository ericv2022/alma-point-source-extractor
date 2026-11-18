"""Check that CASA provides the tools required by APSE."""

import sys
from casatools import image, quanta

assert callable(image)
assert callable(quanta)

print("CASA Python:", sys.version.split()[0])
print("casatools.image: OK")
print("casatools.quanta: OK")
print("APSE CASA smoke test: PASSED")
