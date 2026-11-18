"""Ensure extracted algorithms remain byte-for-byte equivalent in AST form."""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1] / "src" / "apse"

def function_ast(path, name):
    tree = ast.parse(path.read_text())
    return next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)

class TestScientificParity(unittest.TestCase):
    def test_casa_extraction_unchanged(self):
        old = function_ast(ROOT / "legacy.py", "extractSourcesFromImage")
        new = function_ast(ROOT / "casa_extraction.py", "extractSourcesFromImage")
        self.assertEqual(ast.dump(old, include_attributes=False),
                         ast.dump(new, include_attributes=False))

    def test_catalog_algorithms_unchanged(self):
        for name in ("create_ellipse", "filterSources", "makeSourceList"):
            with self.subTest(name=name):
                old = function_ast(ROOT / "legacy.py", name)
                new = function_ast(ROOT / "catalog.py", name)
                self.assertEqual(ast.dump(old, include_attributes=False),
                                 ast.dump(new, include_attributes=False))
