#!/usr/bin/env python3
"""Smoke-check the localhost Settings API without requiring hardware."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


BASE_URL = "http://127.0.0.1:8769"
SETTINGS_FILE = Path("var/data/nexa_settings.json")


def request(method, endpoint, payload=None):
    body = None
    headers = {}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(BASE_URL + endpoint, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=3) as response:
        return json.loads(response.read().decode("utf-8"))


def api_available():
    try:
        request("GET", "/health")
        return True
    except (OSError, urllib.error.URLError, TimeoutError):
        return False


def start_api():
    process = subprocess.Popen([sys.executable, "scripts/run/run_diagnostics_api.py"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    deadline = time.time() + 4
    while time.time() < deadline:
        if api_available():
            return process
        time.sleep(0.1)
    process.terminate()
    raise RuntimeError("settings API did not start")


def run_check():
    backup = None
    if SETTINGS_FILE.exists():
        backup = SETTINGS_FILE.with_suffix(".json.check-backup")
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(SETTINGS_FILE, backup)
    process = None
    started = False
    try:
        if not api_available():
            process = start_api()
            started = True
        settings = request("GET", "/api/settings")
        if "pin_hash" in json.dumps(settings) or "pin_salt" in json.dumps(settings):
            raise RuntimeError("settings API exposed PIN hash/salt")
        updated = request("POST", "/api/settings/update", {"section": "display", "key": "text_size", "value": "Large"})
        if updated.get("status") != "ok":
            raise RuntimeError("settings update failed")
        refreshed = request("GET", "/api/settings")
        if refreshed["settings"]["display"]["text_size"] != "Large":
            raise RuntimeError("settings update did not persist")
        many = request("POST", "/api/settings/update-many", {"updates": [
            {"section": "appearance", "key": "preset", "value": "Night Red"},
            {"section": "appearance", "key": "eye_color", "value": "Red"},
            {"section": "appearance", "key": "mouth_color", "value": "Red"},
            {"section": "appearance", "key": "tile_accent_color", "value": "Red"},
            {"section": "appearance", "key": "background_color", "value": "Black"},
            {"section": "appearance", "key": "led_color", "value": "Red"},
        ]})
        if many.get("status") != "ok":
            raise RuntimeError("settings update-many failed")
        pin_set = request("POST", "/api/privacy/pin/set", {"pin": "1234"})
        verified = request("POST", "/api/privacy/pin/verify", {"pin": "1234"})
        locked = request("POST", "/api/privacy/lock")
        privacy = request("GET", "/api/privacy/status")
        if pin_set.get("status") != "ok" or not verified.get("unlocked") or locked.get("unlocked"):
            raise RuntimeError("PIN flow failed")
        return {
            "status": "ok",
            "started_server": started,
            "settings_update": refreshed["settings"]["display"]["text_size"],
            "update_many": many.get("status"),
            "pin_verified": verified.get("unlocked"),
            "privacy_unlocked": privacy.get("unlocked"),
            "hash_exposed": False,
        }
    finally:
        if process is not None:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
        if backup is not None and backup.exists():
            SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(backup), str(SETTINGS_FILE))
        elif SETTINGS_FILE.exists():
            SETTINGS_FILE.unlink()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        result = run_check()
    except Exception as exc:  # pragma: no cover - script boundary
        result = {"status": "error", "error": str(exc)}
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    elif result["status"] == "ok":
        print("Settings API check passed.")
        print("- OK: /api/settings")
        print("- OK: /api/settings/update")
        print("- OK: /api/settings/update-many")
        print("- OK: /api/privacy/pin/set")
        print("- OK: /api/privacy/pin/verify")
        print("- OK: /api/privacy/lock")
        print("- OK: PIN hash/salt hidden")
    else:
        print("Settings API check failed: " + result.get("error", "unknown"))
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
