#!/usr/bin/env python3
"""Run the safe local hardware gateway development server."""

from __future__ import annotations

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from system.services.hardware_gateway.hardware_dashboard import render_dashboard
from system.services.hardware_gateway.hardware_state import HardwareStateStore


class HardwareGatewayHandler(BaseHTTPRequestHandler):
    server_version = "NeXaHardwareGateway/0.1"

    def log_message(self, format, *args):  # noqa: A002
        if getattr(self.server, "debug", False):
            super().log_message(format, *args)

    def _json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _html(self, body_text: str, status: int = 200) -> None:
        body = body_text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _body_json(self) -> tuple[dict, bool]:
        length = int(self.headers.get("Content-Length", "0") or "0")
        if not length:
            return {}, True
        try:
            data = json.loads(self.rfile.read(length).decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {}, False
        return (data if isinstance(data, dict) else {}), isinstance(data, dict)

    def do_GET(self):  # noqa: N802
        path = urlparse(self.path).path
        if path in {"/", "/hardware-dashboard"}:
            self._html(render_dashboard(self.server.store.as_dict()))
        elif path == "/api/hardware/state":
            self._json({"status": "ok", "state": self.server.store.as_dict()})
        else:
            self._json({"status": "error", "error": "not_found"}, 404)

    def do_POST(self):  # noqa: N802
        path = urlparse(self.path).path
        if path != "/api/hardware":
            self._json({"status": "error", "error": "not_found"}, 404)
            return
        data, valid = self._body_json()
        if not valid:
            self._json({"status": "error", "error": "invalid_json"}, 400)
            return
        state = self.server.store.update(data)
        if getattr(self.server, "debug", False):
            print("received hardware state from " + str(state.get("device", "unknown")))
        self._json({"status": "ok", "connected": bool(state.get("connected", False)), "received": True})


def make_server(host: str, port: int, stale_after_seconds: float, debug: bool = False) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer((host, port), HardwareGatewayHandler)
    server.store = HardwareStateStore(stale_after_seconds=stale_after_seconds)
    server.debug = debug
    return server


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the NeXa ToTem hardware gateway development server.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--stale-after-seconds", type=float, default=5.0)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    server = make_server(args.host, args.port, args.stale_after_seconds, args.debug)
    print(f"Hardware gateway listening at http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nHardware gateway stopped.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
