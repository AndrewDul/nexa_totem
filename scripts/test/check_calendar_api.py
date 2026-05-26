#!/usr/bin/env python3
"""Check Calendar API with a temporary SQLite database."""

import argparse
import json
import os
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path
from http.server import ThreadingHTTPServer


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from system.services.diagnostics.live_api import DiagnosticsHandler, HOST  # noqa: E402


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


def main():
    parser = argparse.ArgumentParser(description="Check Calendar API.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as temp_dir:
        global API_URL
        old_db = os.environ.get("NEXA_CALENDAR_DB_PATH")
        os.environ["NEXA_CALENDAR_DB_PATH"] = str(Path(temp_dir) / "calendar.db")
        server = ThreadingHTTPServer((HOST, 0), DiagnosticsHandler)
        API_URL = "http://127.0.0.1:" + str(server.server_port)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            if not wait_for_api():
                raise RuntimeError("Diagnostics API did not start.")
            today = date.today()
            now_time = datetime.now().strftime("%H:%M")
            results = {}
            results["month_initial"] = fetch(f"/api/calendar/month?year={today.year}&month={today.month}")
            created = post("/api/calendar/events/create", {"title": "Study Java", "description": "OOP", "start_date": today.isoformat(), "start_time": "18:00", "reminder_minutes_before": 15, "repeat_type": "weekly", "snooze_minutes": 10})
            results["create"] = created
            results["month_after_create"] = fetch(f"/api/calendar/month?year={today.year}&month={today.month}")
            results["day"] = fetch(f"/api/calendar/day?date={today.isoformat()}")
            results["update"] = post("/api/calendar/events/update", {"id": created["event"]["id"], "title": "Study Java updated", "description": "Inheritance", "start_date": today.isoformat(), "start_time": "19:00", "reminder_minutes_before": 5, "repeat_type": "none"})
            recurring = post("/api/calendar/events/create", {"title": "Recurring standup", "start_date": today.isoformat(), "start_time": "09:00", "reminder_minutes_before": -1, "repeat_type": "daily"})
            results["create_recurring"] = recurring
            results["month_after_recurring"] = fetch(f"/api/calendar/month?year={today.year}&month={today.month}")
            due_event = post("/api/calendar/events/create", {"title": "Due calendar", "start_date": today.isoformat(), "start_time": now_time, "reminder_minutes_before": 0, "repeat_type": "none"})
            results["create_due"] = due_event
            results["due"] = fetch("/api/calendar/due")
            due_rows = results["due"].get("due", [])
            due_row = next((row for row in due_rows if int(row.get("id", 0)) == int(due_event["event"]["id"])), {})
            results["dismiss"] = post("/api/calendar/dismiss", {"event_id": due_event["event"]["id"], "occurrence_start": due_row.get("occurrence_start", "")})
            results["due_after_dismiss"] = fetch("/api/calendar/due")
            snooze_due = post("/api/calendar/events/create", {"title": "Snooze calendar", "start_date": today.isoformat(), "start_time": now_time, "reminder_minutes_before": 0, "repeat_type": "none"})
            results["create_snooze_due"] = snooze_due
            results["snooze"] = post("/api/calendar/snooze", {"event_id": snooze_due["event"]["id"], "minutes": 10})
            results["due_after_snooze"] = fetch("/api/calendar/due")
            results["delete_blocked"] = post("/api/calendar/events/delete", {"id": created["event"]["id"]})
            results["delete"] = post("/api/calendar/events/delete", {"id": created["event"]["id"], "confirm_text": "DELETE_CALENDAR_EVENT"})
            results["stats"] = fetch("/api/calendar/settings/stats")
            status = "ok"
            for key, value in results.items():
                if key == "delete_blocked":
                    if value.get("error") != "confirmation_required":
                        status = "error"
                elif value.get("status") != "ok":
                    status = "error"
            cells = [cell for week in results["month_initial"].get("weeks", []) for cell in week.get("cells", [])]
            if len(cells) != 42:
                status = "error"
            if not any(cell.get("events_count", 0) > 0 for week in results["month_after_create"].get("weeks", []) for cell in week.get("cells", []) if cell.get("full_date") == today.isoformat()):
                status = "error"
            if not results["day"].get("events"):
                status = "error"
            if not any(event.get("title") == "Recurring standup" for events in results["month_after_recurring"].get("events_by_date", {}).values() for event in events):
                status = "error"
            if not due_row:
                status = "error"
            if any(int(row.get("id", 0)) == int(due_event["event"]["id"]) for row in results["due_after_dismiss"].get("due", [])):
                status = "error"
            if any(int(row.get("id", 0)) == int(snooze_due["event"]["id"]) for row in results["due_after_snooze"].get("due", [])):
                status = "error"
            output = {"status": status, "started_server": True, "port": server.server_port, "results": results}
            if args.json:
                print(json.dumps(output, indent=2, sort_keys=True))
            else:
                print("Calendar API check passed.")
                for key in results:
                    print(f"- OK: {key}")
            return 0 if status == "ok" else 1
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)
            if old_db is None:
                os.environ.pop("NEXA_CALENDAR_DB_PATH", None)
            else:
                os.environ["NEXA_CALENDAR_DB_PATH"] = old_db


if __name__ == "__main__":
    raise SystemExit(main())

