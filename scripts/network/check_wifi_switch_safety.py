#!/usr/bin/env python3
"""Read-only check for switching Raspberry Pi Wi-Fi to NeXa-ESP."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.network.check_network_safety import collect_network_state
from scripts.network.connect_to_esp_network import detect_active_wifi_connection
from system.network.wifi_switch.wifi_switch_plan import mode_summary


def build_report() -> dict:
    raw = collect_network_state()
    active = detect_active_wifi_connection(raw)
    summary = mode_summary()
    return {
        "status": "ok",
        "dry_run": True,
        "changed_network": False,
        "active_wifi": active,
        "esp": summary,
        "warning": "Connecting to NeXa-ESP may disconnect normal internet/SSH until home Wi-Fi is restored.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check ESP Wi-Fi switch safety without changing networking.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = build_report()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    print("NeXa ESP Wi-Fi switch safety check")
    print("Dry-run/read-only: no network changes were made.")
    print("Active Wi-Fi connection: " + str(report["active_wifi"].get("connection_name", "unknown")))
    print("Target ESP SSID: " + report["esp"]["ssid"])
    print("Target ESP URL: " + report["esp"]["state_url"])
    print(report["warning"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
