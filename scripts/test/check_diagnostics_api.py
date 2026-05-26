#!/usr/bin/env python3
"""Check the localhost diagnostics API without leaving a background server."""

import argparse
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
API_URL = "http://127.0.0.1:8769"
ENDPOINTS = [
    "/health",
    "/api/overview",
    "/api/control-center",
    "/api/camera/preview/status",
]


def fetch(path, timeout=3):
    with urllib.request.urlopen(API_URL + path, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def wait_for_api():
    for _ in range(20):
        try:
            fetch("/health", timeout=1)
            return True
        except (OSError, urllib.error.URLError, TimeoutError):
            time.sleep(0.2)
    return False


def main():
    parser = argparse.ArgumentParser(description="Check NeXa diagnostics API.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    started = False
    proc = None
    try:
        try:
            fetch("/health", timeout=1)
        except Exception:
            proc = subprocess.Popen(
                [sys.executable, str(ROOT / "scripts/run/run_diagnostics_api.py")],
                cwd=str(ROOT),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            started = True
            if not wait_for_api():
                raise RuntimeError("Diagnostics API did not start.")

        results = {}
        for endpoint in ENDPOINTS:
            results[endpoint] = fetch(endpoint)

        output = {"status": "ok", "started_server": started, "results": results}
        if args.json:
            print(json.dumps(output, indent=2, sort_keys=True))
        else:
            print("Diagnostics API check passed.")
            for endpoint in ENDPOINTS:
                print(f"- OK: {endpoint}")
        return 0
    finally:
        if started and proc:
            try:
                urllib.request.urlopen(API_URL + "/api/camera/preview/stop", data=b"{}", timeout=1)
            except Exception:
                pass
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=3)


if __name__ == "__main__":
    raise SystemExit(main())
