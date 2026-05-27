#!/usr/bin/env python3
"""Read-only safety check before using wlan0 as the NeXa access point."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from typing import Any


READ_ONLY_COMMANDS = {
    "ip_route": ["ip", "route"],
    "ip_addr": ["ip", "addr"],
    "nmcli_device_status": ["nmcli", "device", "status"],
    "nmcli_active_connections": ["nmcli", "connection", "show", "--active"],
    "hostname_I": ["hostname", "-I"],
}


def run_read_only(command: list[str]) -> dict[str, Any]:
    if shutil.which(command[0]) is None:
        return {"command": command, "returncode": 127, "stdout": "", "stderr": command[0] + " not found"}
    completed = subprocess.run(command, capture_output=True, text=True, timeout=5, check=False)
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def collect_network_state() -> dict[str, Any]:
    return {name: run_read_only(command) for name, command in READ_ONLY_COMMANDS.items()}


def analyze_network_state(raw: dict[str, Any]) -> dict[str, Any]:
    route_text = str(raw.get("ip_route", {}).get("stdout", ""))
    addr_text = str(raw.get("ip_addr", {}).get("stdout", ""))
    device_text = str(raw.get("nmcli_device_status", {}).get("stdout", ""))
    active_text = str(raw.get("nmcli_active_connections", {}).get("stdout", ""))
    default_lines = [line for line in route_text.splitlines() if line.startswith("default ")]
    wlan0_default = any(" dev wlan0" in line or line.endswith("dev wlan0") for line in default_lines)
    safer_interfaces = []
    for name in ["eth0", "usb0", "wlan1"]:
        if name in route_text or name in addr_text or name in device_text or name in active_text:
            safer_interfaces.append(name)
    for line in route_text.splitlines() + addr_text.splitlines() + device_text.splitlines():
        for token in line.split():
            if token.startswith("enx") and token not in safer_interfaces:
                safer_interfaces.append(token)
    safer_available = any(name != "wlan0" for name in safer_interfaces)
    warning = ""
    if wlan0_default:
        warning = "WARNING: wlan0 appears to be your current internet route. Turning wlan0 into NeXa-ToTem AP may disconnect internet/SSH. Use Ethernet, USB tethering, local monitor/keyboard, or a second Wi-Fi adapter before applying."
    recommendation = "Safer: internet appears available outside wlan0." if safer_available else "Use Ethernet, USB tethering, local monitor/keyboard, or a second Wi-Fi adapter before applying."
    return {
        "default_routes": default_lines,
        "wlan0_is_default_route": wlan0_default,
        "eth0_seen": "eth0" in safer_interfaces,
        "usb_tether_seen": any(name == "usb0" or name.startswith("enx") for name in safer_interfaces),
        "second_wifi_seen": "wlan1" in safer_interfaces,
        "safer_internet_outside_wlan0": safer_available,
        "warning": warning,
        "recommendation": recommendation,
    }


def build_report() -> dict[str, Any]:
    raw = collect_network_state()
    analysis = analyze_network_state(raw)
    return {"status": "ok", "dry_run": True, "changed_network": False, "analysis": analysis, "raw": raw}


def main() -> int:
    parser = argparse.ArgumentParser(description="Check if it is safe to turn wlan0 into the NeXa-ToTem AP.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = build_report()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    analysis = report["analysis"]
    print("NeXa-ToTem AP network safety check")
    print("Dry-run/read-only: no network changes were made.")
    print("Default route:")
    for line in analysis["default_routes"] or ["No default route detected"]:
        print("- " + line)
    if analysis["warning"]:
        print(analysis["warning"])
    print(analysis["recommendation"])
    print("eth0 seen: " + str(analysis["eth0_seen"]))
    print("USB tether/enx seen: " + str(analysis["usb_tether_seen"]))
    print("wlan1 seen: " + str(analysis["second_wifi_seen"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
