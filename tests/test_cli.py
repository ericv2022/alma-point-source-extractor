import unittest
from unittest.mock import patch
from apse.cli import main

class TestCLI(unittest.TestCase):
    def test_version(self):
        with self.assertRaises(SystemExit) as result:
            main(["--version"])
        self.assertEqual(result.exception.code, 0)

    def test_regression_options_forwarded(self):
        arguments = ["--offline", "--data-dir", "/tmp/apse-cache",
                     "--casa", "/usr/local/bin/casa",
                     "--write-candidate", "/tmp/candidate.json"]
        with patch("apse.regression.main", return_value=0) as run:
            self.assertEqual(main(["regression"] + arguments), 0)
        run.assert_called_once_with(arguments)

    def test_unknown_images_option_rejected(self):
        with self.assertRaises(SystemExit) as result:
            main(["images", "--pair", "a", "b", "--unknown-option"])
        self.assertEqual(result.exception.code, 2)
