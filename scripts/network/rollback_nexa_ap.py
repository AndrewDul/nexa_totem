#!/usr/bin/env python3
"""Dry-run or remove only the NeXa-ToTem NetworkManager profile."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from typing import Any


SSID = "NeXa-ToTem"
ROLLBACK_FLAG = "--i-understand-this-changes-network"


def dry_run_summary() -> dict[str, Any]:
    return {
        "status": "ok",
        "dry_run": True,
        "changed_network": False,
        "commands": [
            f"nmcli connection down {SSID}",
            f"nmcli connection delete {SSID}",
        ],
        "manual_reconnect": "Reconnect to your normal Wi-Fi from the Raspberry Pi desktop, nmcli, or NetworkManager UI if needed.",
    }


def run_nmcli(args: list[str]) -> dict[str, Any]:
    if shutil.which("nmcli") is None:
        return {"command": ["nmcli"] + args, "returncode": 127, "stdout": "", "stderr": "nmcli not found"}
    completed = subprocess.run(["nmcli"] + args, capture_output=True, text=True, check=False)
    return {"command": ["nmcli"] + args, "returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr}


def apply_rollback() -> dict[str, Any]:
    results = [
        run_nmcli(["connection", "down", SSID]),
        run_nmcli(["connection", "delete", SSID]),
    ]
    return {
        "status": "ok",
        "dry_run": False,
        "changed_network": True,
        "results": results,
        "manual_reconnect": "Reconnect to your normal Wi-Fi from the Raspberry Pi desktop, nmcli, or NetworkManager UI if needed.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Rollback the NeXa-ToTem AP profile.")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--i-understand-this-changes-network", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if not args.apply:
        summary = dry_run_summary()
    elif not args.i_understand_this_changes_network:
        summary = {"status": "error", "error": "missing_warning_flag", "changed_network": False, "required_flag": ROLLBACK_FLAG}
    else:
        summary = apply_rollback()
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    elif summary["status"] == "ok" and summary.get("dry_run", False):
        print("NeXa-ToTem rollback dry-run")
        print("No network changes were made.")
        for command in summary["commands"]:
            print("- " + command)
        print(summary["manual_reconnect"])
    elif summary["status"] == "ok":
        print("NeXa-ToTem rollback command finished.")
        print(summary["manual_reconnect"])
    else:
        print("Rollback blocked: " + str(summary.get("error", "unknown")))
        if summary.get("required_flag"):
            print("Required flag: " + str(summary["required_flag"]))
    return 0 if summary["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
