import tempfile
import unittest
from pathlib import Path
from apse.regression import compare, discover_pairs, ensure_data, UID, PARAMETERS

class TestRegression(unittest.TestCase):
    def test_missing_data_offline(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(RuntimeError):
                ensure_data(tmp, offline=True)
    def test_incomplete_cache_fails_without_download(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "partial.fits").touch()
            with self.assertRaises(RuntimeError):
                ensure_data(tmp)
    def test_detects_missing_spw(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(RuntimeError):
                discover_pairs(tmp)
    def test_compare_identical(self):
        src={"ra_rad": .5,"dec_rad": .2,"flux_jy": .001,"fluxerr_jy": .0001,
             "peak_jy_per_beam": .0009,"ispoint": True}
        result={"uid": UID, "parameters": PARAMETERS,
                "spws": {str(i): {"raw_count": 1, "filtered_count": 1, "sources": [src]}
                         for i in range(4)}}
        self.assertEqual(compare(result, result), [])
        other={**result,"spws": {**result["spws"],"2": {"raw_count": 0,"filtered_count": 0,"sources": []}}}
        self.assertTrue(compare(result, other))

if __name__ == "__main__": unittest.main()
