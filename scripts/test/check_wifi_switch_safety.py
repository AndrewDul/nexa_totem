#!/usr/bin/env python3
"""Check Wi-Fi switch scripts in dry-run mode only."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def run_json(command: list[str]) -> dict:
    completed = subprocess.run(command, cwd=str(ROOT), capture_output=True, text=True, check=False, timeout=10)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or "command failed")
    return json.loads(completed.stdout)


def run_check() -> dict:
    connect = run_json([sys.executable, "scripts/network/connect_to_esp_network.py", "--json"])
    reconnect = run_json([sys.executable, "scripts/network/reconnect_home_wifi.py", "--json"])
    if connect.get("changed_network") or reconnect.get("changed_network"):
        raise RuntimeError("dry-run changed network")
    if connect.get("target_ssid") != "NeXa-ESP":
        raise RuntimeError("target SSID mismatch")
    if connect.get("previous_wifi_connection_path") != "var/data/network/previous_wifi_connection.json":
        raise RuntimeError("previous Wi-Fi path mismatch")
    return {
        "status": "ok",
        "changed_network": False,
        "connect_dry_run": connect["dry_run"],
        "reconnect_dry_run": reconnect["dry_run"],
        "target_ssid": connect["target_ssid"],
        "previous_wifi_connection_path": connect["previous_wifi_connection_path"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Wi-Fi switch dry-run safety.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        result = run_check()
    except Exception as exc:  # pragma: no cover - script boundary
        result = {"status": "error", "error": str(exc), "changed_network": False}
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    elif result["status"] == "ok":
        print("Wi-Fi switch safety check passed.")
        print("- OK: connect_to_esp_network.py dry-run")
        print("- OK: reconnect_home_wifi.py dry-run")
        print("- OK: changed_network false")
        print("- OK: NeXa-ESP and previous Wi-Fi path represented")
    else:
        print("Wi-Fi switch safety check failed: " + result.get("error", "unknown"))
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
