#!/usr/bin/env python3
"""Check ESP pull mode using a fake local ESP server."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from system.services.hardware_gateway.esp_pull_client import EspPullClient
from system.services.hardware_gateway.hardware_state import HardwareStateStore


SAMPLE = {
    "device": "nexa_totem_esp8266",
    "presence": True,
    "distance_cm": 10,
    "joystick": "CENTER",
    "joystick_x": 517,
    "joystick_y": 503,
    "temperature_c": 28.9,
    "humidity_percent": 41.9,
    "pressure_hpa": 1016.6,
    "gas_kohms": 21.4,
    "air_status": "VENTILATE",
}


class FakeEspHandler(BaseHTTPRequestHandler):
    response_body = json.dumps(SAMPLE).encode("utf-8")

    def log_message(self, format, *args):  # noqa: A002
        return

    def do_GET(self):  # noqa: N802
        if self.path != "/api/state":
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(self.response_body)))
        self.end_headers()
        self.wfile.write(self.response_body)


def run_fake_server(body: bytes):
    class Handler(FakeEspHandler):
        response_body = body

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    return server, thread, f"http://{host}:{port}/api/state"


def wait_for_api() -> bool:
    for _ in range(20):
        try:
            with urlopen("http://127.0.0.1:8769/health", timeout=0.5):
                return True
        except (OSError, URLError):
            time.sleep(0.2)
    return False


def check_api_bridge(fake_esp_url: str) -> dict:
    env = os.environ.copy()
    env["NEXA_HARDWARE_MODE"] = "pull_esp_server"
    env["NEXA_ESP_STATE_URL"] = fake_esp_url
    env["NEXA_ESP_POLL_INTERVAL_SECONDS"] = "1.0"
    process = subprocess.Popen(
        [sys.executable, "scripts/run/run_diagnostics_api.py"],
        cwd=str(ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        if not wait_for_api():
            stdout, stderr = process.communicate(timeout=2)
            raise RuntimeError("pull-mode diagnostics API did not start: " + stdout + stderr)
        with urlopen("http://127.0.0.1:8769/api/hardware/state", timeout=2) as response:
            payload = json.loads(response.read().decode("utf-8"))
        state = payload.get("state", {})
        return {
            "source": payload.get("source"),
            "temperature_c": state.get("temperature_c"),
            "connected": state.get("connected"),
        }
    finally:
        process.terminate()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=3)


def run_check() -> dict:
    server, thread, url = run_fake_server(json.dumps(SAMPLE).encode("utf-8"))
    try:
        store = HardwareStateStore()
        result = EspPullClient(url=url).fetch_and_update(store)
        if result.get("status") != "ok" or result["state"]["temperature_c"] != 28.9:
            raise RuntimeError("valid ESP pull did not normalize state")
        api_bridge = check_api_bridge(url)
        if api_bridge.get("temperature_c") != 28.9 or api_bridge.get("source") != "esp_pull":
            raise RuntimeError("pull-mode diagnostics API did not return fake ESP state")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    bad_server, bad_thread, bad_url = run_fake_server(b"{bad")
    try:
        bad_result = EspPullClient(url=bad_url).fetch_once()
        if bad_result.get("error") != "bad_json":
            raise RuntimeError("bad JSON did not return bad_json")
    finally:
        bad_server.shutdown()
        bad_server.server_close()
        bad_thread.join(timeout=2)

    return {
        "status": "ok",
        "changed_network": False,
        "source": result["source"],
        "connected": result["connected"],
        "temperature_c": result["state"]["temperature_c"],
        "air_status": result["state"]["air_status"],
        "api_bridge_source": api_bridge["source"],
        "api_bridge_temperature_c": api_bridge["temperature_c"],
        "bad_json_error": bad_result["error"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check ESP pull mode without Wi-Fi changes.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        result = run_check()
    except Exception as exc:  # pragma: no cover - script boundary
        result = {"status": "error", "error": str(exc), "changed_network": False}
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    elif result["status"] == "ok":
        print("ESP pull mode check passed.")
        print("- OK: fake ESP /api/state")
        print("- OK: state normalized through HardwareStateStore")
        print("- OK: diagnostics API pulls ESP data in pull mode")
        print("- OK: bad JSON handled safely")
        print("- OK: no Wi-Fi changes")
    else:
        print("ESP pull mode check failed: " + result.get("error", "unknown"))
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
