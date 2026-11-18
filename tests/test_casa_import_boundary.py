"""Guard against eager imports of non-CASA dependencies at package import time."""
import subprocess
import sys
import unittest

class TestCasaImportBoundary(unittest.TestCase):
    def test_package_import_does_not_load_catalog_or_pipeline(self):
        code = ("import apse, sys; "
                "assert 'apse.catalog' not in sys.modules; "
                "assert 'apse.pipeline' not in sys.modules; "
                "assert apse.__version__ == '0.3.0'")
        subprocess.run([sys.executable, "-c", code], check=True)
