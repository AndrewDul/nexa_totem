#!/usr/bin/env python3
"""Prepare or apply the NeXa-ToTem access point profile."""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.network.check_network_safety import READ_ONLY_COMMANDS, analyze_network_state, collect_network_state, run_read_only
from system.network.access_point.ap_profile import (
    NEXA_AP_IP,
    NEXA_AP_PASSWORD,
    NEXA_AP_PREFIX,
    NEXA_AP_SSID,
    NEXA_HARDWARE_POST_URL,
    NEXA_HARDWARE_SERVER_PORT,
    build_nmcli_commands,
    build_server_command,
    esp_config_summary,
)


APPLY_WARNING_FLAG = "--i-understand-this-may-disconnect-wifi"


def dry_run_summary(interface: str = "wlan0") -> dict[str, Any]:
    commands = build_nmcli_commands(interface)
    return {
        "status": "ok",
        "dry_run": True,
        "changed_network": False,
        "apply_required": True,
        "ssid": NEXA_AP_SSID,
        "password": NEXA_AP_PASSWORD,
        "ip": NEXA_AP_IP,
        "prefix": NEXA_AP_PREFIX,
        "hardware_server_port": NEXA_HARDWARE_SERVER_PORT,
        "hardware_post_url": NEXA_HARDWARE_POST_URL,
        "interface": interface,
        "nmcli_commands": commands,
        "server_command": build_server_command(),
        "warning": "Applying this profile may disconnect internet/SSH if wlan0 is your current internet route.",
    }


def _write_backup(command_plan: list[str], raw_state: dict[str, Any]) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = ROOT / "var/backups/network" / stamp
    backup_dir.mkdir(parents=True, exist_ok=True)
    for name, result in raw_state.items():
        (backup_dir / f"{name}.txt").write_text(str(result.get("stdout", "")) + "\n" + str(result.get("stderr", "")), encoding="utf-8")
    extra = run_read_only(["nmcli", "connection", "show"])
    (backup_dir / "nmcli_connection_show.txt").write_text(str(extra.get("stdout", "")) + "\n" + str(extra.get("stderr", "")), encoding="utf-8")
    (backup_dir / "planned_nexa_ap_commands.txt").write_text("\n".join(command_plan) + "\n", encoding="utf-8")
    return backup_dir


def apply_profile(interface: str, force_wlan0_ap: bool) -> dict[str, Any]:
    raw_state = collect_network_state()
    analysis = analyze_network_state(raw_state)
    if interface == "wlan0" and analysis["wlan0_is_default_route"] and not force_wlan0_ap:
        return {
            "status": "error",
            "error": "wlan0_is_default_route",
            "changed_network": False,
            "warning": analysis["warning"],
        }
    commands = build_nmcli_commands(interface)
    backup_dir = _write_backup(commands, raw_state)
    results = []
    for command in commands:
        completed = subprocess.run(shlex.split(command), capture_output=True, text=True, check=False)
        results.append({"command": command, "returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr})
        if completed.returncode != 0:
            return {
                "status": "error",
                "error": "nmcli_command_failed",
                "changed_network": True,
                "backup_dir": str(backup_dir),
                "results": results,
                "rollback": "python3 scripts/network/rollback_nexa_ap.py --apply --i-understand-this-changes-network",
            }
    return {
        "status": "ok",
        "dry_run": False,
        "changed_network": True,
        "backup_dir": str(backup_dir),
        "results": results,
        "rollback": "python3 scripts/network/rollback_nexa_ap.py --apply --i-understand-this-changes-network",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Dry-run or apply the NeXa-ToTem NetworkManager AP profile.")
    parser.add_argument("--interface", default="wlan0")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--i-understand-this-may-disconnect-wifi", action="store_true")
    parser.add_argument("--force-wlan0-ap", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if not args.apply:
        summary = dry_run_summary(args.interface)
    elif not args.i_understand_this_may_disconnect_wifi:
        summary = {
            "status": "error",
            "error": "missing_warning_flag",
            "changed_network": False,
            "required_flag": APPLY_WARNING_FLAG,
        }
    else:
        summary = apply_profile(args.interface, args.force_wlan0_ap)

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    elif summary["status"] == "ok" and summary.get("dry_run", False):
        print("NeXa-ToTem AP setup dry-run")
        print("No network changes were made.")
        print(esp_config_summary())
        print("Planned NetworkManager commands:")
        for command in summary["nmcli_commands"]:
            print("- " + command)
        print("Hardware server command:")
        print(summary["server_command"])
        print(summary["warning"])
        print("Apply later with:")
        print("python3 scripts/network/setup_nexa_ap.py --apply --interface wlan0 --i-understand-this-may-disconnect-wifi")
        print("If wlan0 is your internet route, add: --force-wlan0-ap")
    elif summary["status"] == "ok":
        print("NeXa-ToTem AP profile applied.")
        print("Backup: " + str(summary.get("backup_dir", "")))
        print("Rollback: " + str(summary.get("rollback", "")))
    else:
        print("NeXa-ToTem AP setup blocked: " + str(summary.get("error", "unknown")))
        if summary.get("warning"):
            print(str(summary["warning"]))
        if summary.get("required_flag"):
            print("Required flag: " + str(summary["required_flag"]))
    return 0 if summary["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
