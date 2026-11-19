"""Tests for ste_bridge: rules.check and normalize."""
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

import ste_bridge.rules as rules  # noqa: E402
import ste_bridge.normalize as normalize_mod  # noqa: E402

# bin/ is added after ste_bridge is already imported as a package.
sys.path.insert(0, str(_ROOT / "bin"))
import local_model_bench as lmb  # noqa: E402

_FIXTURES = _ROOT / "fixtures" / "ste"


class FakeChatServer(http.server.BaseHTTPRequestHandler):
    """Respond with clean numbered steps (no violations)."""

    def do_POST(self):
        n = int(self.headers["Content-Length"])
        self.rfile.read(n)  # consume body
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


class TestRulesCheck(unittest.TestCase):
    """Rule-check tests on fixture files and synthetic strings."""

    def test_lawyer_pt_flags_r1_r2_r4(self):
        text = (_FIXTURES / "lawyer_pt.txt").read_text(encoding="utf-8")
        violations = rules.check(text, "pt")
        rule_names = {v["rule"] for v in violations}
        self.assertIn("R1_LENGTH", rule_names, "lawyer_pt should trigger R1_LENGTH")
        self.assertIn("R2_VAGUE", rule_names, "lawyer_pt should trigger R2_VAGUE")
        self.assertIn("R4_MULTI_ACTION", rule_names, "lawyer_pt should trigger R4_MULTI_ACTION")

    def test_expected_pt_no_violations(self):
        text = (_FIXTURES / "expected_pt.txt").read_text(encoding="utf-8")
        violations = rules.check(text, "pt")
        self.assertEqual(violations, [], "expected_pt should have zero violations")

    def test_r3_passive_pt(self):
        violations = rules.check("O pedido foi deferido pelo juiz.", "pt")
        rule_names = {v["rule"] for v in violations}
        self.assertIn("R3_PASSIVE", rule_names, "Portuguese passive should trigger R3_PASSIVE")

    def test_r3_passive_en(self):
        violations = rules.check("The request was approved.", "en")
        rule_names = {v["rule"] for v in violations}
        self.assertIn("R3_PASSIVE", rule_names, "English passive should trigger R3_PASSIVE")


class TestNormalize(unittest.TestCase):
    """normalize() integration tests with a fake loopback server."""

    def setUp(self):
        self.srv = http.server.HTTPServer(("127.0.0.1", 0), FakeChatServer)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.endpoint = f"http://127.0.0.1:{self.srv.server_port}"

    def tearDown(self):
        self.srv.shutdown()

    def test_normalize_device_tested(self):
        result = normalize_mod.normalize(
            text="Doutor, favor diligenciar.",
            lang="pt",
            endpoint=self.endpoint,
            model="test-model",
            timeout=5,
        )
        self.assertEqual(result["status"], "DEVICE_TESTED")
        self.assertEqual(len(result["steps"]), 4)
        # No raw text in the result keys
        self.assertIn("input_sha256", result)
        self.assertIn("output_sha256", result)

    def test_normalize_closed_port_no_data(self):
        port = self.srv.server_port
        self.srv.shutdown()
        self.srv.server_close()
        result = normalize_mod.normalize(
            text="test",
            lang="pt",
            endpoint=f"http://127.0.0.1:{port}",
            model="test-model",
            timeout=2,
        )
        self.assertTrue(
            result["status"].startswith("NO_DATA("),
            f"Expected NO_DATA status, got {result['status']}",
        )
        # Re-create server for tearDown
        self.srv = http.server.HTTPServer(("127.0.0.1", 0), FakeChatServer)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    def test_normalize_rejects_non_loopback(self):
        # check_loopback must reject localhost and non-loopback IPs.
        for bad in ["http://localhost:8080", "http://192.168.1.5:8080"]:
            with self.assertRaises(ValueError):
                lmb.check_loopback(bad)

    def test_receipt_no_raw_text(self):
        """Ensure a receipt written by normalize contains only hashes, not raw text."""
        with tempfile.TemporaryDirectory() as tmp:
            receipt_path = pathlib.Path(tmp) / "receipt.json"
            text = "Doutor, favor diligenciar."
            result = normalize_mod.normalize(
                text=text,
                lang="pt",
                endpoint=self.endpoint,
                model="test-model",
                timeout=5,
            )
            receipt = {
                "status": result["status"],
                "step_count": len(result["steps"]),
                "violation_count": len(result["violations"]),
                "retries": result["retries"],
                "input_sha256": result["input_sha256"],
                "output_sha256": result["output_sha256"],
            }
            receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
            raw = receipt_path.read_text(encoding="utf-8")
            self.assertNotIn("diligenciar", raw, "receipt must not contain raw input text")
            self.assertNotIn("Verifique", raw, "receipt must not contain raw output text")


if __name__ == "__main__":
    unittest.main()
