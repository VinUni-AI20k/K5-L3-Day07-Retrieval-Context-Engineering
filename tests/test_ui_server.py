"""Offline checks of the local UI server (app/server.py): no model, no network, no gold."""
import http.client
import json
import sys
import threading
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import server as U  # noqa: E402


class HelperTests(unittest.TestCase):
    def test_configs_and_traversal(self):
        self.assertIn("final", U.list_configs())
        self.assertEqual(U.load_config("final")["method"], "hybrid_rerank")
        for bad in ("../requirements", "final.json", ""):
            with self.assertRaises(KeyError):
                U.load_config(bad)

    def test_library_mode_is_builtin_and_first(self):
        with mock.patch.object(U, "library_available", return_value=True):
            self.assertEqual(U.list_configs()[0], "library")
            cfg = U.load_config("library")
            self.assertEqual((cfg["collection"], cfg["allow_chapter_filter"]), ("library", False))
        with mock.patch.object(U, "library_available", return_value=False):
            self.assertNotIn("library", U.list_configs())
            with self.assertRaises(KeyError):
                U.load_config("library")

    def test_samples_have_no_gold(self):
        for s in U.load_samples():
            self.assertEqual(set(s), {"id", "question"})

    def test_citation_rows_and_errors(self):
        tr = {"status": "answered", "citations": ["a", "z"], "final_context": [{"id": "a", "text": "t"}]}
        self.assertEqual([(r["id"], r["valid"]) for r in U.citation_rows(tr)], [("a", True), ("z", False)])
        self.assertIsNone(U.classify_error(tr))
        self.assertIn("quota", U.classify_error({"status": "error", "errors": ["429 RESOURCE_EXHAUSTED"]}).lower())


class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = U.make_server("127.0.0.1", 0)
        cls.port = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.srv.server_close()

    def req(self, method, path, body=None, headers=None):
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        c.request(method, path, body=body, headers=headers or {})
        r = c.getresponse()
        data = r.read()
        c.close()
        return r, data

    def test_index_and_static(self):
        r, data = self.req("GET", "/")
        self.assertEqual(r.status, 200)
        self.assertIn(b"RAG Agent Tester", data)
        self.assertIn("default-src 'self'", r.getheader("Content-Security-Policy"))
        self.assertEqual(self.req("GET", "/static/app.js")[0].status, 200)

    def test_static_traversal_blocked(self):
        for p in ("/static/../server.py", "/static/..%2fserver.py", "/static/../../.env"):
            self.assertEqual(self.req("GET", p)[0].status, 404, p)

    def test_status_never_contains_key(self):
        with mock.patch.object(U.A, "load_api_key", return_value="SECRET-KEY-VALUE"):
            r, data = self.req("GET", "/api/status")
        self.assertEqual(r.status, 200)
        self.assertNotIn(b"SECRET-KEY-VALUE", data)
        st = json.loads(data)
        self.assertTrue(st["api_key"])
        self.assertIn("final", st["configs"])

    def test_foreign_host_rejected(self):
        self.assertEqual(self.req("GET", "/api/status", headers={"Host": "evil.example"})[0].status, 403)

    def test_ask_validation(self):
        ok = {"Content-Type": "application/json"}
        self.assertEqual(self.req("POST", "/api/ask", b'{"question":"q","config":"final"}', {"Content-Type": "text/plain"})[0].status, 415)
        self.assertEqual(self.req("POST", "/api/ask", b'{"question":"  ","config":"final"}', ok)[0].status, 400)
        self.assertEqual(self.req("POST", "/api/ask", b'{"question":"q","config":"../x"}', ok)[0].status, 400)
        self.assertEqual(self.req("POST", "/api/ask", b"not json", ok)[0].status, 400)

    def test_ask_returns_trace(self):
        fake = {"status": "answered", "citations": ["a"], "final_context": [{"id": "a", "text": "t"}], "answer": "x [a]"}
        with mock.patch.object(U, "ask", return_value={**fake, "ui": {"citations": U.citation_rows(fake)}}) as m:
            r, data = self.req("POST", "/api/ask", b'{"question":" why? ","config":"final"}', {"Content-Type": "application/json"})
        self.assertEqual(r.status, 200)
        m.assert_called_once_with("why?", "final")
        self.assertTrue(json.loads(data)["ui"]["citations"][0]["valid"])


if __name__ == "__main__":
    unittest.main()
