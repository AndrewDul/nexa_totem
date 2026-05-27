#!/usr/bin/env python3
"""Check the NeXa access point safety scripts without applying networking."""

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
    safety = run_json([sys.executable, "scripts/network/check_network_safety.py", "--json"])
    setup = run_json([sys.executable, "scripts/network/setup_nexa_ap.py", "--json"])
    rollback = run_json([sys.executable, "scripts/network/rollback_nexa_ap.py", "--json"])
    if not setup.get("dry_run") or setup.get("changed_network"):
        raise RuntimeError("setup dry-run changed network")
    if not rollback.get("dry_run") or rollback.get("changed_network"):
        raise RuntimeError("rollback dry-run changed network")
    if safety.get("changed_network"):
        raise RuntimeError("safety check changed network")
    expected = {
        "ssid": "NeXa-ToTem",
        "ip": "10.42.0.1",
        "hardware_post_url": "http://10.42.0.1:8080/api/hardware",
    }
    for key, value in expected.items():
        if setup.get(key) != value:
            raise RuntimeError(f"setup {key} mismatch")
    return {
        "status": "ok",
        "changed_network": False,
        "setup_dry_run": setup["dry_run"],
        "rollback_dry_run": rollback["dry_run"],
        "safety_dry_run": safety["dry_run"],
        "ssid": setup["ssid"],
        "ip": setup["ip"],
        "hardware_post_url": setup["hardware_post_url"],
        "wlan0_is_default_route": safety["analysis"]["wlan0_is_default_route"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check NeXa AP safety scripts.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        result = run_check()
    except Exception as exc:  # pragma: no cover - script boundary
        result = {"status": "error", "error": str(exc), "changed_network": False}
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    elif result["status"] == "ok":
        print("Network AP safety check passed.")
        print("- OK: check_network_safety.py --json")
        print("- OK: setup_nexa_ap.py --json dry-run")
        print("- OK: rollback_nexa_ap.py --json dry-run")
        print("- OK: no apply was performed")
        print("- OK: NeXa-ToTem SSID/IP/URL are correct")
    else:
        print("Network AP safety check failed: " + result.get("error", "unknown"))
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
