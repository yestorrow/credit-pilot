"""Exercise the real HTTP handler without requiring a listening socket."""
import io
import json
import tempfile
import unittest

import desk
import pilot


class Request:
    def __init__(self, raw):
        self.input = io.BytesIO(raw)
        self.output = io.BytesIO()

    def makefile(self, *args):
        return self.input

    def sendall(self, data):
        self.output.write(data)


class Server:
    pass


class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = desk.Desk(self.temp.name)
        self.handler = desk.handler(self.store)
        self.handler.log_message = lambda *args: None

    def call(self, method, path, value=None, origin="http://localhost:8000"):
        body = json.dumps(value).encode() if value is not None else b""
        raw = (f"{method} {path} HTTP/1.0\r\nHost: localhost:8000\r\n"
               f"Origin: {origin}\r\nContent-Type: application/json\r\n"
               f"Content-Length: {len(body)}\r\n\r\n").encode() + body
        request = Request(raw)
        self.handler(request, ("127.0.0.1", 1234), Server())
        headers, data = request.output.getvalue().split(b"\r\n\r\n", 1)
        return int(headers.split(b" ")[1]), headers, data

    def test_http_cycle(self):
        status, _, body = self.call("GET", "/api/status")
        self.assertEqual(status, 200)
        self.assertFalse(json.loads(body)["automatic_dispatch"])
        status, _, body = self.call("POST", "/api/jobs", {
            "case": pilot.read(pilot.ROOT / "examples/abc.json"),
            "message": "Light test", "mode": "light"})
        self.assertEqual(status, 201)
        job = json.loads(body)
        status, _, body = self.call("GET", "/api/jobs/" + job["id"])
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["status"], "queued")
        _, _, body = self.call("GET", "/api/jobs")
        self.assertEqual(len(json.loads(body)), 1)

    def test_assets_and_restrictions(self):
        for path in ("/", "/app.js", "/styles.css"):
            status, headers, body = self.call("GET", path)
            self.assertEqual(status, 200)
            self.assertTrue(body)
            self.assertIn(b"Content-Security-Policy:", headers)
        self.assertEqual(self.call("GET", "/../../engine/desk-data/jobs")[0], 404)
        self.assertEqual(self.call("POST", "/api/jobs", {}, origin="https://other.example")[0], 403)
        self.assertEqual(self.call("POST", "/api/jobs", {})[0], 400)
        self.assertEqual(self.call("GET", "/api/jobs/missing")[0], 404)


if __name__ == "__main__":
    unittest.main()
