"""Tests for lm-context-diet.py, run against the examples shipped with the repository.

Run from the repository root:

    python -m unittest discover tests
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPT = os.path.join(ROOT, "lm-context-diet.py")
EXAMPLES = os.path.join(ROOT, "examples")


def run(*args):
    """Run the tool with the given arguments and return (exit code, stdout+stderr)."""
    result = subprocess.run(
        [sys.executable, SCRIPT, *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.returncode, result.stdout + result.stderr


class ContextDietTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.baseline = os.path.join(self.tmp.name, "baseline.json")
        before = os.path.join(EXAMPLES, "CLAUDE.before.md")
        code, out = run("baseline", before, "-o", self.baseline)
        self.assertEqual(code, 0, out)

    def tearDown(self):
        self.tmp.cleanup()

    def test_measure_reports_the_example(self):
        code, out = run("measure", os.path.join(EXAMPLES, "CLAUDE.before.md"))
        self.assertEqual(code, 0, out)
        self.assertIn("imperative lines", out)
        self.assertIn("14", out)

    def test_baseline_is_valid_json(self):
        with open(self.baseline, encoding="utf-8") as f:
            json.load(f)  # raises if the file is not valid JSON

    def test_check_identical_file_exits_zero(self):
        code, out = run("check", os.path.join(EXAMPLES, "CLAUDE.before.md"), self.baseline)
        self.assertEqual(code, 0, out)

    def test_check_good_extraction_reports_five_disappeared(self):
        code, out = run("check", os.path.join(EXAMPLES, "CLAUDE.after.md"), self.baseline)
        self.assertIn("disappeared 5", out)

    def test_check_broken_extraction_exits_one(self):
        code, out = run("check", os.path.join(EXAMPLES, "CLAUDE.after-broken.md"), self.baseline)
        self.assertEqual(code, 1, out)
        self.assertIn("disappeared 6", out)

    def test_links_on_examples_has_no_dead_link(self):
        code, out = run("links", os.path.join(EXAMPLES, "CLAUDE.before.md"))
        self.assertEqual(code, 0, out)
        self.assertIn("no dead relative link", out)

    def test_links_detects_a_dead_link(self):
        path = os.path.join(self.tmp.name, "CLAUDE.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write("See [missing](does-not-exist.md) for details.\n")
        code, out = run("links", path)
        self.assertNotEqual(code, 0, out)
        self.assertIn("does-not-exist.md", out)


if __name__ == "__main__":
    unittest.main()
