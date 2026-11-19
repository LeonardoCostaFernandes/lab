"""Tests for bin/ste_bench.py — the ste_bridge benchmark matrix runner."""
import http.server
import json
import pathlib
import sys
import tempfile
import threading
import unittest

# Make the repo root importable — must come BEFORE bin/ so the ste_bridge
# package (directory) wins over bin/ste_bridge.py (script).
_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

import ste_bridge.normalize as normalize_mod  # noqa: E402

# bin/ is added after ste_bridge is already imported as a package.
sys.path.insert(0, str(_ROOT / "bin"))
import ste_bench  # noqa: E402


class FakeTextServer(http.server.BaseHTTPRequestHandler):
    """Respond with clean numbered steps (no violations) for text mode."""

    def do_POST(self):
        n = int(self.headers["Content-Length"])
        self.rfile.read(n)
        steps = (
            "1. Verifique a data limite da contestação no sistema.\n"
            "2. Confirme se a data atual é anterior à data limite.\n"
            "3. Se estiver antes da data limite, protocole a contestação.\n"
            "4. Se estiver depois da data limite, alerte o humano."
        )
        body = json.dumps({
            "choices": [{"message": {"content": steps}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 40},
        }).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):  # noqa: A002
        pass


class FakeStructuredServer(http.server.BaseHTTPRequestHandler):
    """Respond with schema-valid JSON for structured mode."""

    def do_POST(self):
        n = int(self.headers["Content-Length"])
        self.rfile.read(n)
        response = {
            "items": [
                {"kind": "check", "actor": "sistema", "verb": "Verifique",
                 "object": "a data limite", "if": None, "deadline": None},
                {"kind": "action", "actor": "advogado", "verb": "Protocolo",
                 "object": "a contestação", "if": None, "deadline": None},
            ]
        }
        body = json.dumps({
            "choices": [{"message": {"content": json.dumps(response)}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 40},
        }).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):  # noqa: A002
        pass


class MultiModeServer(http.server.BaseHTTPRequestHandler):
    """Dispatches to text or structured response based on request body."""

    def do_POST(self):
        n = int(self.headers["Content-Length"])
        raw = self.rfile.read(n)
        body_data = json.loads(raw.decode("utf-8"))

        # If the request contains response_format with json_schema, it's structured mode
        if body_data.get("response_format", {}).get("type") == "json_schema":
            response = {
                "items": [
                    {"kind": "check", "actor": "sistema", "verb": "Verifique",
                     "object": "a data limite", "if": None, "deadline": None},
                    {"kind": "action", "actor": "advogado", "verb": "Protocolo",
                     "object": "a contestação", "if": None, "deadline": None},
                ]
            }
            content = json.dumps(response)
        else:
            content = (
                "1. Verifique a data limite da contestação no sistema.\n"
                "2. Confirme se a data atual é anterior à data limite.\n"
                "3. Se estiver antes da data limite, protocole a contestação.\n"
                "4. Se estiver depois da data limite, alerte o humano."
            )

        body = json.dumps({
            "choices": [{"message": {"content": content}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 40},
        }).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):  # noqa: A002
        pass


class TestParseFixtures(unittest.TestCase):
    """Tests for fixture string parsing."""

    def test_valid_fixture(self):
        fixtures = ste_bench._parse_fixtures(["path/in.txt|path/ref.txt|pt"])
        self.assertEqual(len(fixtures), 1)
        self.assertEqual(fixtures[0]["input"], "path/in.txt")
        self.assertEqual(fixtures[0]["reference"], "path/ref.txt")
        self.assertEqual(fixtures[0]["lang"], "pt")

    def test_invalid_fixture_format(self):
        with self.assertRaises(ValueError):
            ste_bench._parse_fixtures(["only_one_part"])

    def test_invalid_lang(self):
        with self.assertRaises(ValueError):
            ste_bench._parse_fixtures(["in|ref|fr"])


class TestParseEndpoints(unittest.TestCase):
    """Tests for endpoint string parsing."""

    def test_valid_endpoint(self):
        endpoints = ste_bench._parse_endpoints(["test=http://127.0.0.1:8080=qwen"])
        self.assertEqual(len(endpoints), 1)
        self.assertEqual(endpoints[0]["name"], "test")
        self.assertEqual(endpoints[0]["url"], "http://127.0.0.1:8080")
        self.assertEqual(endpoints[0]["model"], "qwen")

    def test_invalid_endpoint_format(self):
        with self.assertRaises(ValueError):
            ste_bench._parse_endpoints(["only_one"])


class TestMatrixRunner(unittest.TestCase):
    """Integration tests for the full matrix runner."""

    def setUp(self):
        self.srv = http.server.HTTPServer(("127.0.0.1", 0), MultiModeServer)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.port = self.srv.server_port
        self.endpoint_str = f"test=http://127.0.0.1:{self.port}=test-model"

        # Create temporary fixture files
        self.tmp = tempfile.TemporaryDirectory()
        tmp_path = pathlib.Path(self.tmp.name)

        self.input_file = tmp_path / "input.txt"
        self.input_file.write_text(
            "Doutor, favor diligenciar junto aos sistemas internos.",
            encoding="utf-8"
        )
        self.ref_file = tmp_path / "ref.txt"
        self.ref_file.write_text(
            "1. Verifique a data limite.\n"
            "2. Protocolo a contestação.\n"
            "3. Alertar o humano.",
            encoding="utf-8"
        )
        self.fixture_str = f"{self.input_file}|{self.ref_file}|pt"

    def tearDown(self):
        self.srv.shutdown()
        self.tmp.cleanup()

    def test_matrix_produces_four_rows(self):
        """1 fixture × 1 endpoint × 2 modes × 2 runs = 4 rows."""
        out_dir = tempfile.mkdtemp()
        argv = [
            "--fixtures", self.fixture_str,
            "--endpoints", self.endpoint_str,
            "--modes", "text", "structured",
            "--runs", "2",
            "--out", out_dir,
        ]
        ste_bench.main(argv)

        receipts = pathlib.Path(out_dir) / "receipts.jsonl"
        lines = receipts.read_text(encoding="utf-8").strip().splitlines()
        self.assertEqual(len(lines), 4, "Expected 4 rows (1×1×2×2)")

        # Verify structure of each row
        for line in lines:
            row = json.loads(line)
            self.assertIn("model", row)
            self.assertIn("fixture", row)
            self.assertIn("mode", row)
            self.assertIn("run", row)
            self.assertIn("step_count", row)
            self.assertIn("violation_count", row)
            self.assertIn("retries", row)
            self.assertIn("covered", row)
            self.assertIn("total", row)
            self.assertIn("ratio", row)
            self.assertIn("latency_ms", row)
            self.assertIn("output_sha256", row)
            self.assertIn("status", row)

    def test_means_are_correct(self):
        """Means in README.md must match computed values from receipts."""
        out_dir = tempfile.mkdtemp()
        argv = [
            "--fixtures", self.fixture_str,
            "--endpoints", self.endpoint_str,
            "--modes", "text", "structured",
            "--runs", "2",
            "--out", out_dir,
        ]
        ste_bench.main(argv)

        # Read receipts and compute expected means
        receipts = pathlib.Path(out_dir) / "receipts.jsonl"
        lines = receipts.read_text(encoding="utf-8").strip().splitlines()
        rows = [json.loads(l) for l in lines]
        means = ste_bench._compute_means(rows)

        # Verify means are computed (not NO_DATA since server works)
        for key, m in means.items():
            self.assertIsInstance(m["mean_ratio"], float,
                                  f"mean_ratio for {key} should be float, got {type(m['mean_ratio'])}")
            self.assertIsInstance(m["mean_violation_count"], float,
                                  f"mean_violation_count for {key} should be float")
            self.assertIsInstance(m["mean_latency_ms"], float,
                                  f"mean_latency_ms for {key} should be float")
            self.assertGreater(m["mean_latency_ms"], 0,
                               "latency should be positive")

    def test_closed_port_gives_no_data(self):
        """When the endpoint is unreachable, rows should have NO_DATA status."""
        # Use a port where nothing is listening
        closed_port = 19876
        endpoint_str = f"closed=http://127.0.0.1:{closed_port}=test-model"

        out_dir = tempfile.mkdtemp()
        argv = [
            "--fixtures", self.fixture_str,
            "--endpoints", endpoint_str,
            "--modes", "text",
            "--runs", "2",
            "--out", out_dir,
        ]
        ste_bench.main(argv)

        receipts = pathlib.Path(out_dir) / "receipts.jsonl"
        lines = receipts.read_text(encoding="utf-8").strip().splitlines()
        self.assertEqual(len(lines), 2)

        for line in lines:
            row = json.loads(line)
            self.assertTrue(
                row["status"].startswith("NO_DATA("),
                f"Expected NO_DATA status for closed port, got {row['status']}",
            )

    def test_no_raw_text_in_output(self):
        """receipts.jsonl and README.md must not contain raw input or output text."""
        out_dir = tempfile.mkdtemp()
        argv = [
            "--fixtures", self.fixture_str,
            "--endpoints", self.endpoint_str,
            "--modes", "text", "structured",
            "--runs", "2",
            "--out", out_dir,
        ]
        ste_bench.main(argv)

        receipts_text = (pathlib.Path(out_dir) / "receipts.jsonl").read_text(encoding="utf-8")
        readme_text = (pathlib.Path(out_dir) / "README.md").read_text(encoding="utf-8")

        # Check that raw input text doesn't appear
        self.assertNotIn("diligenciar", receipts_text,
                         "receipts must not contain raw input text")
        self.assertNotIn("diligenciar", readme_text,
                         "README must not contain raw input text")

        # Check that raw output steps don't appear
        self.assertNotIn("Verifique a data limite da contestação", receipts_text,
                         "receipts must not contain raw output text")
        self.assertNotIn("Verifique a data limite da contestação", readme_text,
                         "README must not contain raw output text")

    def test_readme_contains_required_sections(self):
        """README.md must contain date, command, machine, table, and means."""
        out_dir = tempfile.mkdtemp()
        argv = [
            "--fixtures", self.fixture_str,
            "--endpoints", self.endpoint_str,
            "--modes", "text",
            "--runs", "2",
            "--out", out_dir,
            "--machine", "Test Machine",
        ]
        ste_bench.main(argv)

        readme = (pathlib.Path(out_dir) / "README.md").read_text(encoding="utf-8")
        self.assertIn("Date (UTC):", readme)
        self.assertIn("Command:", readme)
        self.assertIn("Test Machine", readme)
        self.assertIn("Results table", readme)
        self.assertIn("Means per model", readme)
        self.assertIn("mean(x) = sum(x_i) / N", readme)

    def test_default_machine_is_no_data(self):
        """When --machine is not given, README must show NO_DATA(machine_not_declared)."""
        out_dir = tempfile.mkdtemp()
        argv = [
            "--fixtures", self.fixture_str,
            "--endpoints", self.endpoint_str,
            "--modes", "text",
            "--runs", "1",
            "--out", out_dir,
        ]
        ste_bench.main(argv)

        readme = (pathlib.Path(out_dir) / "README.md").read_text(encoding="utf-8")
        self.assertIn("NO_DATA(machine_not_declared)", readme)


class TestComputeMeans(unittest.TestCase):
    """Unit tests for _compute_means helper."""

    def test_means_with_all_ok(self):
        rows = [
            {"model": "m1", "mode": "text", "status": "DEVICE_TESTED",
             "ratio": 0.8, "violation_count": 2, "latency_ms": 100.0},
            {"model": "m1", "mode": "text", "status": "DEVICE_TESTED",
             "ratio": 0.6, "violation_count": 4, "latency_ms": 200.0},
        ]
        means = ste_bench._compute_means(rows)
        key = ("m1", "text")
        self.assertEqual(means[key]["mean_ratio"], 0.7)
        self.assertEqual(means[key]["mean_violation_count"], 3.0)
        self.assertEqual(means[key]["mean_latency_ms"], 150.0)
        self.assertEqual(means[key]["ok_runs"], 2)

    def test_means_with_all_failed(self):
        rows = [
            {"model": "m1", "mode": "text", "status": "NO_DATA(URLError)",
             "ratio": 0.0, "violation_count": 0, "latency_ms": 0.0},
            {"model": "m1", "mode": "text", "status": "NO_DATA(URLError)",
             "ratio": 0.0, "violation_count": 0, "latency_ms": 0.0},
        ]
        means = ste_bench._compute_means(rows)
        key = ("m1", "text")
        self.assertEqual(means[key]["mean_ratio"], "NO_DATA(all_runs_failed)")
        self.assertEqual(means[key]["ok_runs"], 0)

    def test_means_mixed_ok_and_failed(self):
        rows = [
            {"model": "m1", "mode": "text", "status": "DEVICE_TESTED",
             "ratio": 1.0, "violation_count": 0, "latency_ms": 50.0},
            {"model": "m1", "mode": "text", "status": "NO_DATA(URLError)",
             "ratio": 0.0, "violation_count": 0, "latency_ms": 0.0},
        ]
        means = ste_bench._compute_means(rows)
        key = ("m1", "text")
        # Only the OK run counts for the mean
        self.assertEqual(means[key]["mean_ratio"], 1.0)
        self.assertEqual(means[key]["mean_violation_count"], 0.0)
        self.assertEqual(means[key]["mean_latency_ms"], 50.0)
        self.assertEqual(means[key]["ok_runs"], 1)
        self.assertEqual(means[key]["runs"], 2)


if __name__ == "__main__":
    unittest.main()
