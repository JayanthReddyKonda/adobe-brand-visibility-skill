"""Mock network helper for simulating HTTP responses and SSRF boundaries."""

import http.server
import threading
from typing import Dict, Optional, Tuple


class MockHTTPHandler(http.server.BaseHTTPRequestHandler):
    """Configurable in-memory HTTP handler."""

    # Dictionary mapping paths to (status_code, content_type, body_bytes, headers)
    routes: Dict[str, Tuple[int, str, bytes, Dict[str, str]]] = {}

    def do_GET(self):
        path = self.path.split("?")[0]
        if path in self.routes:
            status, ctype, body, headers = self.routes[path]
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            for k, v in headers.items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Not Found")

    def log_message(self, format, *args):
        # Suppress server logging during tests
        pass


class MockHTTPServer:
    """Lightweight localhost HTTP server for deterministic network tests."""

    def __init__(self, routes: Optional[Dict[str, Tuple[int, str, bytes, Dict[str, str]]]] = None):
        self.routes = routes or {}
        self.server: Optional[http.server.HTTPServer] = None
        self.thread: Optional[threading.Thread] = None
        self.port: int = 0

    def start(self):
        handler = MockHTTPHandler
        handler.routes = self.routes
        self.server = http.server.HTTPServer(("127.0.0.1", 0), handler)
        self.port = self.server.server_port
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def stop(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.server = None

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self.port}"
