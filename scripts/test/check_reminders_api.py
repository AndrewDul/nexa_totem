#!/usr/bin/env python3
"""Check Reminders API with a temporary SQLite database."""

import argparse
import json
import os
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from http.server import ThreadingHTTPServer


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from system.services.diagnostics.live_api import DiagnosticsHandler, HOST  # noqa: E402
from system.services.settings import settings_store  # noqa: E402


API_URL = ""


def fetch(path, timeout=3):
    with urllib.request.urlopen(API_URL + path, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def post(path, payload, timeout=3):
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(API_URL + path, data=body, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def wait_for_api():
    for _ in range(25):
        try:
            fetch("/health", timeout=1)
            return True
        except (OSError, urllib.error.URLError, TimeoutError):
            time.sleep(0.2)
    return False


def iso_delta(**kwargs):
    return (datetime.now(timezone.utc).replace(microsecond=0) + timedelta(**kwargs)).isoformat()


def main():
    parser = argparse.ArgumentParser(description="Check Reminders API.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as temp_dir:
        global API_URL
        old_db = os.environ.get("NEXA_REMINDERS_DB_PATH")
        old_settings = os.environ.get("NEXA_SETTINGS_PATH")
        os.environ["NEXA_REMINDERS_DB_PATH"] = str(Path(temp_dir) / "reminders.db")
        settings_path = Path(temp_dir) / "settings.json"
        os.environ["NEXA_SETTINGS_PATH"] = str(settings_path)
        server = ThreadingHTTPServer((HOST, 0), DiagnosticsHandler)
        API_URL = "http://127.0.0.1:" + str(server.server_port)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            if not wait_for_api():
                raise RuntimeError("Diagnostics API did not start.")
            results = {}
            upcoming = post("/api/reminders/create", {"title": "Upcoming reminder", "notes": "", "due_at": iso_delta(minutes=30), "is_private": False})
            past = post("/api/reminders/create", {"title": "Past reminder", "notes": "", "due_at": iso_delta(minutes=-10), "is_private": False})
            due = post("/api/reminders/create", {"title": "Due reminder", "notes": "", "due_at": iso_delta(minutes=-1), "is_private": False})
            dismissed_past = post("/api/reminders/create", {"title": "Dismissed past reminder", "notes": "", "due_at": iso_delta(minutes=-12), "is_private": False})
            results["create_upcoming"] = upcoming
            results["create_past"] = past
            results["list_initial"] = fetch("/api/reminders/list")
            results["update_past_future"] = post("/api/reminders/update", {"id": past["reminder"]["id"], "title": "Past reused", "notes": "", "due_at": iso_delta(minutes=45), "is_private": False})
            results["dismiss_past_before_reuse"] = post("/api/reminders/dismiss", {"id": dismissed_past["reminder"]["id"]})
            results["update_dismissed_past_future"] = post("/api/reminders/update", {"id": dismissed_past["reminder"]["id"], "title": "Dismissed past reused", "notes": "", "due_at": iso_delta(minutes=50), "is_private": False})
            results["list_after_past_reuse"] = fetch("/api/reminders/list")
            results["due"] = fetch("/api/reminders/due")
            results["list_while_due"] = fetch("/api/reminders/list")
            results["mark_triggered"] = post("/api/reminders/mark-triggered", {"id": due["reminder"]["id"]})
            results["due_after_mark_triggered"] = fetch("/api/reminders/due")
            results["dismiss"] = post("/api/reminders/dismiss", {"id": due["reminder"]["id"]})
            results["due_after_dismiss"] = fetch("/api/reminders/due")
            results["list_after_dismiss"] = fetch("/api/reminders/list")
            snooze_target = post("/api/reminders/create", {"title": "Snooze reminder", "due_at": iso_delta(minutes=-1)})
            results["snooze"] = post("/api/reminders/snooze", {"id": snooze_target["reminder"]["id"], "minutes": 5})
            results["list_after_snooze"] = fetch("/api/reminders/list")
            settings_store.set_pin("1234", settings_path)
            settings_store.update_setting("notifications", "private_reminders_enabled", True, settings_path)
            settings_store.lock_private(settings_path)
            private_due = post("/api/reminders/create", {"title": "Private due reminder", "due_at": iso_delta(minutes=-1), "is_private": True})
            results["private_due_create"] = private_due
            results["private_due_locked"] = fetch("/api/reminders/due")
            settings_store.verify_pin("1234", settings_path)
            results["private_due_unlocked"] = fetch("/api/reminders/due")
            results["delete_blocked"] = post("/api/reminders/delete", {"id": upcoming["reminder"]["id"]})
            results["delete"] = post("/api/reminders/delete", {"id": upcoming["reminder"]["id"], "confirm_text": "DELETE_REMINDER"})
            results["stats"] = fetch("/api/reminders/settings/stats")
            status = "ok"
            for key, value in results.items():
                if key == "delete_blocked":
                    if value.get("error") != "confirmation_required":
                        status = "error"
                elif value.get("status") != "ok":
                    status = "error"
            if int(results["due"].get("count", 0)) < 1:
                status = "error"
            if results["update_past_future"].get("reminder", {}).get("status") != "active":
                status = "error"
            if results["update_dismissed_past_future"].get("reminder", {}).get("status") != "active":
                status = "error"
            if results["update_dismissed_past_future"].get("reminder", {}).get("dismissed_at") is not None:
                status = "error"
            if not any(int(item.get("id", 0)) == int(past["reminder"]["id"]) for item in results["list_after_past_reuse"].get("upcoming", [])):
                status = "error"
            if any(int(item.get("id", 0)) == int(past["reminder"]["id"]) for item in results["list_after_past_reuse"].get("past", [])):
                status = "error"
            if not any(int(item.get("id", 0)) == int(dismissed_past["reminder"]["id"]) for item in results["list_after_past_reuse"].get("upcoming", [])):
                status = "error"
            if any(int(item.get("id", 0)) == int(dismissed_past["reminder"]["id"]) for item in results["list_after_past_reuse"].get("past", [])):
                status = "error"
            if not any(int(item.get("id", 0)) == int(due["reminder"]["id"]) for item in results["list_while_due"].get("past", [])):
                status = "error"
            if int(results["due_after_mark_triggered"].get("count", 0)) < 1:
                status = "error"
            if any(int(item.get("id", 0)) == int(due["reminder"]["id"]) for item in results["due_after_dismiss"].get("due", [])):
                status = "error"
            if not any(int(item.get("id", 0)) == int(due["reminder"]["id"]) for item in results["list_after_dismiss"].get("past", [])):
                status = "error"
            if not any(int(item.get("id", 0)) == int(snooze_target["reminder"]["id"]) for item in results["list_after_snooze"].get("upcoming", [])):
                status = "error"
            locked_due = results["private_due_locked"].get("due", [])
            if not any(item.get("title") == "Private reminder locked" and item.get("requires_pin") for item in locked_due):
                status = "error"
            unlocked_due = results["private_due_unlocked"].get("due", [])
            if not any(item.get("title") == "Private due reminder" and not item.get("requires_pin") for item in unlocked_due):
                status = "error"
            output = {"status": status, "started_server": True, "port": server.server_port, "results": results}
            if args.json:
                print(json.dumps(output, indent=2, sort_keys=True))
            else:
                print("Reminders API check passed.")
                for key in results:
                    print(f"- OK: {key}")
            return 0 if status == "ok" else 1
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)
            if old_db is None:
                os.environ.pop("NEXA_REMINDERS_DB_PATH", None)
            else:
                os.environ["NEXA_REMINDERS_DB_PATH"] = old_db
            if old_settings is None:
                os.environ.pop("NEXA_SETTINGS_PATH", None)
            else:
                os.environ["NEXA_SETTINGS_PATH"] = old_settings


if __name__ == "__main__":
    raise SystemExit(main())
