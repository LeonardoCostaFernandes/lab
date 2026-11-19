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

    def test_detects_authorization_header(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            for p in v.REQUIRED:
                (root / p).mkdir(parents=True, exist_ok=True) if "." not in p else (root / p).write_text("x")
            leak = root / "benchmarks" / "leak.txt"
            leak.parent.mkdir(parents=True)
            leak.write_text("Authorization: Bearer secret123\n")
            pro = v.problems(root)
            self.assertTrue(any("forbidden header" in p for p in pro))

    def test_detects_secret_key_pattern(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            for p in v.REQUIRED:
                (root / p).mkdir(parents=True, exist_ok=True) if "." not in p else (root / p).write_text("x")
            leak = root / "benchmarks" / "leak.txt"
            leak.parent.mkdir(parents=True)
            leak.write_text("key=sk-abcdefghijklmnopqrstuvwxyz\n")
            pro = v.problems(root)
            self.assertTrue(any("possible secret key" in p for p in pro))

    def test_benchmarks_clean_of_secrets(self):
        pro = v.problems()
        self.assertFalse(any("forbidden header" in p for p in pro), "Authorization header found in benchmarks/")
        self.assertFalse(any("possible secret key" in p for p in pro), "Secret key pattern found in benchmarks/")

    def test_single_policy_file(self):
        root = v.ROOT
        self.assertIn("AGENTS.md", (root / "CLAUDE.md").read_text())
        self.assertIn("AGENTS.md", (root / ".junie" / "guidelines.md").read_text())


if __name__ == "__main__":
    unittest.main()
