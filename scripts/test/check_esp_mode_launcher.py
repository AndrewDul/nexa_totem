#!/usr/bin/env python3
"""Check the ESP mode launcher without switching Wi-Fi."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LAUNCHER = ROOT / "scripts/run/run_nexa_totem_esp_mode.sh"
NORMAL_LAUNCHER = ROOT / "scripts/run/run_godot_ui_with_api_dev.sh"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def run_no_confirm() -> dict:
    env = os.environ.copy()
    env.pop("CONFIRM_NEXA_ESP_WIFI_SWITCH", None)
    completed = subprocess.run(
        ["bash", str(LAUNCHER)],
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=5,
    )
    output = completed.stdout + completed.stderr
    return {
        "returncode": completed.returncode,
        "output": output,
        "mentions_confirmation": "CONFIRM_NEXA_ESP_WIFI_SWITCH=RUN" in output,
        "no_changes_message": "No Wi-Fi changes were made." in output,
        "attempted_connect": "Connecting Raspberry Pi Wi-Fi to NeXa-ESP" in output,
    }


def check() -> dict:
    launcher_text = read(LAUNCHER)
    normal_text = read(NORMAL_LAUNCHER)
    no_confirm = run_no_confirm()
    checks = {
        "launcher_exists": LAUNCHER.exists(),
        "requires_confirmation_env": "CONFIRM_NEXA_ESP_WIFI_SWITCH" in launcher_text and '!= "RUN"' in launcher_text,
        "warning_present": "ESP mode will disconnect Raspberry Pi from normal Wi-Fi/internet and connect to NeXa-ESP." in launcher_text,
        "connect_apply_command": "connect_to_esp_network.py --apply --i-understand-this-will-disconnect-internet" in launcher_text,
        "pull_mode_export": "export NEXA_HARDWARE_MODE=pull_esp_server" in launcher_text,
        "esp_url_export": "export NEXA_ESP_STATE_URL=http://192.168.4.1/api/state" in launcher_text,
        "poll_interval_export": "export NEXA_ESP_POLL_INTERVAL_SECONDS=0.2" in launcher_text,
        "uses_safe_api_launcher": "run_godot_ui_with_api_dev.sh" in launcher_text,
        "trap_cleanup": "trap cleanup EXIT INT TERM" in launcher_text,
        "reconnect_apply_command": "reconnect_home_wifi.py --apply --i-understand-this-changes-network" in launcher_text,
        "normal_launcher_no_connect": "connect_to_esp_network.py" not in normal_text,
        "normal_launcher_no_reconnect": "reconnect_home_wifi.py" not in normal_text,
        "no_confirm_exits_nonzero": no_confirm["returncode"] != 0,
        "no_confirm_mentions_confirmation": no_confirm["mentions_confirmation"],
        "no_confirm_says_no_changes": no_confirm["no_changes_message"],
        "no_confirm_did_not_attempt_connect": not no_confirm["attempted_connect"],
    }
    return {
        "status": "ok" if all(checks.values()) else "error",
        "changed_network": False,
        "checks": checks,
        "no_confirm_returncode": no_confirm["returncode"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check ESP mode launcher safety without applying Wi-Fi changes.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = check()
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    elif result["status"] == "ok":
        print("ESP mode launcher check passed.")
        print("- OK: launcher exists")
        print("- OK: confirmation is required")
        print("- OK: no-confirm path exits before Wi-Fi changes")
        print("- OK: pull-mode environment is exported")
        print("- OK: cleanup reconnect is represented")
        print("- OK: normal dev launcher does not switch Wi-Fi")
    else:
        print("ESP mode launcher check failed.")
        for name, passed in result["checks"].items():
            if not passed:
                print("- FAIL: " + name)
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
