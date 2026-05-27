#!/usr/bin/env python3
"""Smoke-check the safe local hardware gateway API."""

from __future__ import annotations

import argparse
import json
import sys
import threading
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run.run_hardware_gateway_dev import make_server


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
    "wifi_rssi": -45,
    "last_arduino_raw": "presence=1|distance_cm=10|joystick=CENTER|x=517|y=503",
}


def request(base_url: str, method: str, path: str, payload=None):
    body = None
    headers = {}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(base_url + path, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=3) as response:
        content = response.read().decode("utf-8")
        if response.headers.get("Content-Type", "").startswith("application/json"):
            return json.loads(content)
        return content


def run_check():
    server = make_server("127.0.0.1", 0, 5.0, False)
    host, port = server.server_address
    base_url = f"http://{host}:{port}"
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        initial = request(base_url, "GET", "/api/hardware/state")
        if initial["state"]["connected"] or not initial["state"]["stale"]:
            raise RuntimeError("initial state should be disconnected and stale")
        post = request(base_url, "POST", "/api/hardware", SAMPLE)
        if post.get("status") != "ok" or not post.get("received"):
            raise RuntimeError("hardware POST failed")
        latest = request(base_url, "GET", "/api/hardware/state")
        state = latest["state"]
        if not state["connected"] or state["temperature_c"] != 28.9 or state["joystick"] != "CENTER":
            raise RuntimeError("latest hardware state did not match sample")
        dashboard = request(base_url, "GET", "/hardware-dashboard")
        if "Temperature" not in dashboard or "Presence" not in dashboard or "Environment" not in dashboard:
            raise RuntimeError("dashboard did not contain expected labels")
        bad_json_status = 0
        try:
            req = urllib.request.Request(base_url + "/api/hardware", data=b"{bad", headers={"Content-Type": "application/json"}, method="POST")
            urllib.request.urlopen(req, timeout=3)
        except urllib.error.HTTPError as exc:
            bad_json_status = exc.code
            error_payload = json.loads(exc.read().decode("utf-8"))
            if error_payload.get("error") != "invalid_json":
                raise RuntimeError("bad JSON returned wrong error")
        if bad_json_status != 400:
            raise RuntimeError("bad JSON did not return 400")
        return {
            "status": "ok",
            "base_url": base_url,
            "initial_connected": initial["state"]["connected"],
            "post_received": post["received"],
            "latest_connected": state["connected"],
            "temperature_c": state["temperature_c"],
            "dashboard": "ok",
            "bad_json_status": bad_json_status,
        }
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def main():
    parser = argparse.ArgumentParser(description="Check NeXa hardware gateway API.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        result = run_check()
    except Exception as exc:  # pragma: no cover - script boundary
        result = {"status": "error", "error": str(exc)}
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    elif result["status"] == "ok":
        print("Hardware gateway API check passed.")
        print("- OK: GET /api/hardware/state before data")
        print("- OK: POST /api/hardware")
        print("- OK: GET /api/hardware/state after data")
        print("- OK: GET /hardware-dashboard")
        print("- OK: bad JSON returns 400")
    else:
        print("Hardware gateway API check failed: " + result.get("error", "unknown"))
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
