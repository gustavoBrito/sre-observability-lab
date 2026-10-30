"""Test bootstrap.

Runs BEFORE the app module is imported so that:
  - INVENTORY_URL points to a real HTTP stub (no external service needed);
  - OTel exporter init happens against the same env var contract as prod.
"""

import http.server
import json
import os
import socket
import socketserver
import threading


def _free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class _InventoryStub(http.server.BaseHTTPRequestHandler):
    """Always-healthy inventory replica for pricing's upstream call."""

    def do_GET(self):
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"sku": "SKU-42", "units": 5}).encode())

    def log_message(self, *args):  # silence in test output
        return


_PORT = _free_port()
os.environ["INVENTORY_URL"] = f"http://127.0.0.1:{_PORT}"
os.environ.setdefault("OTEL_SERVICE_NAME", "pricing-py-tests")

_server = socketserver.ThreadingTCPServer(("127.0.0.1", _PORT), _InventoryStub)
threading.Thread(target=_server.serve_forever, daemon=True).start()
