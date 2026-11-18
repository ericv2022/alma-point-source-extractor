import unittest
from apse.cli import main

class TestCLI(unittest.TestCase):
    def test_version(self):
        with self.assertRaises(SystemExit) as result:
            main(["--version"])
        self.assertEqual(result.exception.code, 0)
