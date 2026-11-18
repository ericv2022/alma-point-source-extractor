"""Orchestration tests do not require a running CASA instance."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from apse.pipeline import run_images

class TestPipeline(unittest.TestCase):
    def test_requires_pairs(self):
        with self.assertRaises(ValueError):
            run_images([])

    def test_rejects_unsafe_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                run_images([("a", "b")], output_dir=tmp, name="../oops")

    def test_backend_invocation_and_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            def fake_run(cmd, **kwargs):
                self.assertIsInstance(cmd, list)
                self.assertTrue(kwargs["check"])
                job = json.loads(Path(kwargs["env"]["APSE_JOB_FILE"]).read_text())
                Path(job["output"]).write_text(json.dumps({"0": {
                    "ispoint": True, "pixelcoords": [1, 2],
                    "pixelsperarcsec": [5, 5],
                    "shape": {"majoraxis": {"value": 1},
                              "minoraxis": {"value": 1},
                              "positionangle": {"value": 0},
                              "direction": {"RA": ["00:00:00"],
                                            "DEC": ["+00:00:00"]}},
                    "flux": {"value": [0.01], "error": [0.001]}}}))
            with patch("apse.pipeline._casa_path", return_value="/fake/casa"), \
                 patch("apse.pipeline.subprocess.run", side_effect=fake_run):
                paths = run_images([("a", "b")], output_dir=tmp)
            self.assertEqual(set(paths), {"raw", "filtered", "catalog"})
            self.assertEqual(json.loads(paths["catalog"].read_text())["0"]["FLUX"], .01)

if __name__ == "__main__":
    unittest.main()
