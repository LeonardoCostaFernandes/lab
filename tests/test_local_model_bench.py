import http.server
import json
import pathlib
import sys
import tempfile
import threading
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "bin"))
import local_model_bench as b  # noqa: E402


class FakeServer(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        n = int(self.headers["Content-Length"])
        req = json.loads(self.rfile.read(n))
        assert req["temperature"] == 0
        body = json.dumps({"choices": [{"message": {"content": "ok answer"}}],
                           "usage": {"prompt_tokens": 5, "completion_tokens": 2}}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


class TestLoopback(unittest.TestCase):
    def test_accepts_loopback(self):
        self.assertEqual(b.check_loopback("http://127.0.0.1:8080"), "http://127.0.0.1:8080")
        self.assertEqual(b.check_loopback("http://[::1]:11434/"), "http://[::1]:11434")

    def test_rejects_non_loopback(self):
        for bad in ["http://localhost:8080", "http://192.168.1.5:8080", "https://127.0.0.1:8080",
                    "http://127.0.0.1", "http://8.8.8.8:80", "http://127.0.0.1:8080/v1"]:
            with self.assertRaises(ValueError, msg=bad):
                b.check_loopback(bad)


class TestRun(unittest.TestCase):
    def setUp(self):
        self.srv = http.server.HTTPServer(("127.0.0.1", 0), FakeServer)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.tmp = tempfile.TemporaryDirectory()
        self.prompts = pathlib.Path(self.tmp.name) / "p.txt"
        self.prompts.write_text("first secret prompt\nsecond\n", encoding="utf-8")

    def tearDown(self):
        self.srv.shutdown()
        self.tmp.cleanup()

    def test_receipt_has_hashes_not_text(self):
        out = pathlib.Path(self.tmp.name) / "r" / "receipt.json"
        rc = b.main(["--endpoint", f"http://127.0.0.1:{self.srv.server_port}", "--model", "m",
                     "--prompts", str(self.prompts), "--machine", "test", "--out", str(out)])
        self.assertEqual(rc, 0)
        raw = out.read_text(encoding="utf-8")
        self.assertNotIn("secret", raw)
        self.assertNotIn("ok answer", raw)
        data = json.loads(raw)
        self.assertEqual(data["status"], "DEVICE_TESTED")
        self.assertEqual(len(data["runs"]), 2)
        self.assertEqual(data["runs"][0]["prompt_sha256"], b.sha256("first secret prompt"))

    def test_unreachable_is_no_data(self):
        port = self.srv.server_port
        self.srv.shutdown()
        self.srv.server_close()
        out = pathlib.Path(self.tmp.name) / "receipt.json"
        rc = b.main(["--endpoint", f"http://127.0.0.1:{port}", "--model", "m", "--timeout", "2",
                     "--prompts", str(self.prompts), "--machine", "test", "--out", str(out)])
        self.assertEqual(rc, 1)
        self.assertTrue(json.loads(out.read_text())["status"].startswith("NO_DATA("))
        self.srv = http.server.HTTPServer(("127.0.0.1", 0), FakeServer)  # for tearDown
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()


if __name__ == "__main__":
    unittest.main()
