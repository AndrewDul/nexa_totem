#!/usr/bin/env python3
"""Dry-run or connect Raspberry Pi Wi-Fi to the ESP8266 network."""

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

from scripts.network.check_network_safety import collect_network_state, run_read_only
from system.network.wifi_switch.wifi_switch_plan import (
    NEXA_ESP_SSID,
    PREVIOUS_WIFI_CONNECTION_PATH,
    build_connect_commands,
    mode_summary,
)


APPLY_FLAG = "--i-understand-this-will-disconnect-internet"


def detect_active_wifi_connection(raw_state: dict[str, Any] | None = None) -> dict[str, str]:
    raw = raw_state if raw_state is not None else collect_network_state()
    active_text = str(raw.get("nmcli_active_connections", {}).get("stdout", ""))
    device_text = str(raw.get("nmcli_device_status", {}).get("stdout", ""))
    for line in active_text.splitlines()[1:]:
        if " wifi " in (" " + line + " ") or " wlan0 " in (" " + line + " "):
            parts = line.split()
            if parts:
                return {"connection_name": parts[0], "raw": line}
    for line in device_text.splitlines()[1:]:
        if line.startswith("wlan") or " wifi " in (" " + line + " "):
            parts = line.split()
            if len(parts) >= 4 and parts[2] == "connected":
                return {"connection_name": " ".join(parts[3:]), "raw": line}
    return {"connection_name": "", "raw": ""}


def dry_run_summary(interface: str = "wlan0") -> dict:
    raw = collect_network_state()
    active = detect_active_wifi_connection(raw)
    summary = mode_summary()
    return {
        "status": "ok",
        "dry_run": True,
        "changed_network": False,
        "target_ssid": NEXA_ESP_SSID,
        "active_wifi": active,
        "previous_wifi_connection_path": PREVIOUS_WIFI_CONNECTION_PATH,
        "connect_commands": build_connect_commands(interface),
        "esp": summary,
        "warning": "Connecting to NeXa-ESP may disconnect normal internet/SSH until home Wi-Fi is restored.",
        "reconnect_command": "python3 scripts/network/reconnect_home_wifi.py --apply --i-understand-this-changes-network",
    }


def _backup_network_state(raw_state: dict[str, Any], commands: list[str]) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = ROOT / "var/backups/network" / stamp
    backup_dir.mkdir(parents=True, exist_ok=True)
    for name, result in raw_state.items():
        (backup_dir / f"{name}.txt").write_text(str(result.get("stdout", "")) + "\n" + str(result.get("stderr", "")), encoding="utf-8")
    all_connections = run_read_only(["nmcli", "connection", "show"])
    (backup_dir / "nmcli_connection_show.txt").write_text(str(all_connections.get("stdout", "")) + "\n" + str(all_connections.get("stderr", "")), encoding="utf-8")
    (backup_dir / "planned_connect_to_esp_commands.txt").write_text("\n".join(commands) + "\n", encoding="utf-8")
    return backup_dir


def _save_previous_wifi(active_wifi: dict[str, str]) -> Path:
    path = ROOT / PREVIOUS_WIFI_CONNECTION_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "saved_at": datetime.now().isoformat(timespec="seconds"),
        "connection_name": active_wifi.get("connection_name", ""),
        "raw": active_wifi.get("raw", ""),
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def apply_connect(interface: str = "wlan0") -> dict:
    raw = collect_network_state()
    active = detect_active_wifi_connection(raw)
    commands = build_connect_commands(interface)
    previous_path = _save_previous_wifi(active)
    backup_dir = _backup_network_state(raw, commands)
    results = []
    for command in commands:
        completed = subprocess.run(shlex.split(command), capture_output=True, text=True, check=False)
        results.append({"command": command, "returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr})
        if completed.returncode != 0:
            return {
                "status": "error",
                "error": "nmcli_command_failed",
                "changed_network": True,
                "previous_wifi_connection_path": str(previous_path),
                "backup_dir": str(backup_dir),
                "results": results,
            }
    return {
        "status": "ok",
        "dry_run": False,
        "changed_network": True,
        "previous_wifi_connection_path": str(previous_path),
        "backup_dir": str(backup_dir),
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Dry-run or connect to the NeXa-ESP Wi-Fi network.")
    parser.add_argument("--interface", default="wlan0")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--i-understand-this-will-disconnect-internet", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if not args.apply:
        result = dry_run_summary(args.interface)
    elif not args.i_understand_this_will_disconnect_internet:
        result = {"status": "error", "error": "missing_warning_flag", "changed_network": False, "required_flag": APPLY_FLAG}
    else:
        result = apply_connect(args.interface)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    elif result.get("status") == "ok" and result.get("dry_run", False):
        print("Connect to NeXa-ESP dry-run")
        print("No network changes were made.")
        print("Current Wi-Fi: " + str(result["active_wifi"].get("connection_name", "unknown")))
        print("Previous Wi-Fi save path: " + result["previous_wifi_connection_path"])
        print("Target SSID: " + result["target_ssid"])
        print("Planned commands:")
        for command in result["connect_commands"]:
            print("- " + command)
        print(result["warning"])
        print("Apply with: python3 scripts/network/connect_to_esp_network.py --apply --i-understand-this-will-disconnect-internet")
    elif result.get("status") == "ok":
        print("Connected to NeXa-ESP command sequence finished.")
        print("Previous Wi-Fi saved at: " + str(result.get("previous_wifi_connection_path", "")))
    else:
        print("Connect blocked: " + str(result.get("error", "unknown")))
        if result.get("required_flag"):
            print("Required flag: " + str(result["required_flag"]))
    return 0 if result.get("status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
