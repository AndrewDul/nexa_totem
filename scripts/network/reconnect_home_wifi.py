#!/usr/bin/env python3
"""Dry-run or reconnect to the saved previous Wi-Fi connection."""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from system.network.wifi_switch.wifi_switch_plan import (
    NEXA_ESP_SSID,
    PREVIOUS_WIFI_CONNECTION_PATH,
    build_reconnect_commands,
)


APPLY_FLAG = "--i-understand-this-changes-network"


def load_previous_wifi() -> dict:
    path = ROOT / PREVIOUS_WIFI_CONNECTION_PATH
    if not path.exists():
        return {"connection_name": "", "path": str(path), "exists": False}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"connection_name": "", "path": str(path), "exists": True, "error": "bad_json"}
    payload["path"] = str(path)
    payload["exists"] = True
    return payload


def dry_run_summary(delete_esp_profile: bool = False) -> dict:
    previous = load_previous_wifi()
    commands = build_reconnect_commands(previous.get("connection_name") or None, delete_esp_profile)
    return {
        "status": "ok",
        "dry_run": True,
        "changed_network": False,
        "target_ssid": NEXA_ESP_SSID,
        "previous_wifi": previous,
        "previous_wifi_connection_path": PREVIOUS_WIFI_CONNECTION_PATH,
        "delete_esp_profile": delete_esp_profile,
        "reconnect_commands": commands,
        "manual_instructions": "If reconnect fails, use Raspberry Pi network settings or nmcli to reconnect your normal Wi-Fi.",
    }


def apply_reconnect(delete_esp_profile: bool = False) -> dict:
    previous = load_previous_wifi()
    commands = build_reconnect_commands(previous.get("connection_name") or None, delete_esp_profile)
    if not previous.get("connection_name"):
        return {
            "status": "error",
            "error": "previous_wifi_unknown",
            "changed_network": False,
            "previous_wifi": previous,
            "manual_instructions": "Use Raspberry Pi network settings or nmcli to reconnect your normal Wi-Fi manually.",
        }
    results = []
    for command in commands:
        completed = subprocess.run(shlex.split(command), capture_output=True, text=True, check=False)
        results.append({"command": command, "returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr})
    return {
        "status": "ok",
        "dry_run": False,
        "changed_network": True,
        "previous_wifi": previous,
        "results": results,
        "manual_instructions": "If reconnect failed, use Raspberry Pi network settings or nmcli to reconnect your normal Wi-Fi manually.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Dry-run or reconnect home Wi-Fi after ESP mode.")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--i-understand-this-changes-network", action="store_true")
    parser.add_argument("--delete-esp-profile", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if not args.apply:
        result = dry_run_summary(args.delete_esp_profile)
    elif not args.i_understand_this_changes_network:
        result = {"status": "error", "error": "missing_warning_flag", "changed_network": False, "required_flag": APPLY_FLAG}
    else:
        result = apply_reconnect(args.delete_esp_profile)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    elif result.get("status") == "ok" and result.get("dry_run", False):
        print("Reconnect home Wi-Fi dry-run")
        print("No network changes were made.")
        print("Previous Wi-Fi: " + str(result["previous_wifi"].get("connection_name", "unknown")))
        print("Previous Wi-Fi save path: " + result["previous_wifi_connection_path"])
        print("Planned commands:")
        for command in result["reconnect_commands"]:
            print("- " + command)
        print(result["manual_instructions"])
    elif result.get("status") == "ok":
        print("Reconnect command sequence finished.")
        print(result["manual_instructions"])
    else:
        print("Reconnect blocked: " + str(result.get("error", "unknown")))
        if result.get("required_flag"):
            print("Required flag: " + str(result["required_flag"]))
        if result.get("manual_instructions"):
            print(result["manual_instructions"])
    return 0 if result.get("status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
