#!/usr/bin/env python3
"""Check To Do API with a temporary SQLite database."""

import argparse
import json
import os
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime
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
    parser = argparse.ArgumentParser(description="Check To Do API.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as temp_dir:
        global API_URL
        old_db = os.environ.get("NEXA_TODO_DB_PATH")
        os.environ["NEXA_TODO_DB_PATH"] = str(Path(temp_dir) / "todo.db")
        server = ThreadingHTTPServer((HOST, 0), DiagnosticsHandler)
        API_URL = "http://127.0.0.1:" + str(server.server_port)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            if not wait_for_api():
                raise RuntimeError("Diagnostics API did not start.")
            now = datetime.now().replace(microsecond=0)
            results = {}
            results["overview"] = fetch("/api/todo/overview")
            results["lists_initial"] = fetch("/api/todo/lists")
            inbox_id = results["lists_initial"]["lists"][0]["id"]
            results["create_list"] = post("/api/todo/lists/create", {"name": "Study", "emoji": "📚"})
            list_id = results["create_list"]["list"]["id"]
            results["create_task"] = post("/api/todo/tasks/create", {
                "list_id": list_id,
                "title": "Finish Java notes",
                "notes": "",
                "due_date": now.date().isoformat(),
                "due_time": now.strftime("%H:%M"),
                "reminder_enabled": True,
                "repeat_unit": "none",
                "repeat_interval": 0,
            })
            task_id = results["create_task"]["task"]["id"]
            results["tasks_after_create"] = fetch(f"/api/todo/tasks?list_id={list_id}")
            results["mark_done"] = post("/api/todo/tasks/mark-done", {"id": task_id})
            results["tasks_after_done"] = fetch(f"/api/todo/tasks?list_id={list_id}")
            results["mark_active"] = post("/api/todo/tasks/mark-active", {"id": task_id})
            results["create_due"] = post("/api/todo/tasks/create", {
                "list_id": list_id,
                "title": "Due To Do",
                "due_date": now.date().isoformat(),
                "due_time": now.strftime("%H:%M"),
                "reminder_enabled": True,
            })
            due_id = results["create_due"]["task"]["id"]
            results["due"] = fetch("/api/todo/due")
            results["snooze"] = post("/api/todo/snooze", {"task_id": due_id, "minutes": 10})
            results["due_after_snooze"] = fetch("/api/todo/due")
            results["create_repeating"] = post("/api/todo/tasks/create", {
                "list_id": inbox_id,
                "title": "Repeat task",
                "due_date": now.date().isoformat(),
                "due_time": now.strftime("%H:%M"),
                "reminder_enabled": True,
                "repeat_unit": "hours",
                "repeat_interval": 6,
            })
            repeat_id = results["create_repeating"]["task"]["id"]
            results["dismiss_repeating"] = post("/api/todo/dismiss", {"task_id": repeat_id})
            results["delete_blocked"] = post("/api/todo/tasks/delete", {"id": task_id})
            results["delete"] = post("/api/todo/tasks/delete", {"id": task_id, "confirm_text": "DELETE_TODO_TASK"})
            results["stats"] = fetch("/api/todo/settings/stats")
            status = "ok"
            for key, value in results.items():
                if key == "delete_blocked":
                    if value.get("error") != "confirmation_required":
                        status = "error"
                elif value.get("status") != "ok":
                    status = "error"
            if not any(row.get("name") == "Inbox" for row in results["lists_initial"].get("lists", [])):
                status = "error"
            if not results["tasks_after_create"].get("active"):
                status = "error"
            if not results["tasks_after_done"].get("completed"):
                status = "error"
            if not any(int(row.get("task_id", 0)) == int(due_id) for row in results["due"].get("due", [])):
                status = "error"
            if any(int(row.get("task_id", 0)) == int(due_id) for row in results["due_after_snooze"].get("due", [])):
                status = "error"
            if not results["dismiss_repeating"].get("next_reminder_at"):
                status = "error"
            output = {"status": status, "started_server": True, "port": server.server_port, "results": results}
            if args.json:
                print(json.dumps(output, indent=2, sort_keys=True))
            else:
                print("To Do API check passed.")
                for key in results:
                    print(f"- OK: {key}")
            return 0 if status == "ok" else 1
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)
            if old_db is None:
                os.environ.pop("NEXA_TODO_DB_PATH", None)
            else:
                os.environ["NEXA_TODO_DB_PATH"] = old_db


if __name__ == "__main__":
    raise SystemExit(main())

