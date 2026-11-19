import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "bin"))
import verify_structure as v  # noqa: E402


class TestStructure(unittest.TestCase):
    def test_repo_is_clean(self):
        self.assertEqual(v.problems(), [])

    def test_detects_raw_field(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            for p in v.REQUIRED:
                (root / p).mkdir(parents=True, exist_ok=True) if "." not in p else (root / p).write_text("x")
            rec = root / "benchmarks" / "x" / "receipt.json"
            rec.parent.mkdir(parents=True)
            rec.write_text(json.dumps({"runs": [{"prompt": "leak"}]}))
            self.assertTrue(any("raw field" in p for p in v.problems(root)))

    def test_single_policy_file(self):
        root = v.ROOT
        self.assertIn("AGENTS.md", (root / "CLAUDE.md").read_text())
        self.assertIn("AGENTS.md", (root / ".junie" / "guidelines.md").read_text())


if __name__ == "__main__":
    unittest.main()
