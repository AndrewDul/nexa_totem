"""SQLite-backed local Calendar store."""

from __future__ import annotations

import calendar as calendar_lib
import os
import sqlite3
from datetime import date, datetime, time, timedelta
from pathlib import Path


DEFAULT_DB_PATH = Path("var/data/calendar/nexa_calendar.db")
SCHEMA_VERSION = 1
DELETE_CONFIRM = "DELETE_CALENDAR_EVENT"
REPEAT_TYPES = {"none", "daily", "weekly", "monthly", "yearly"}
REMINDER_OPTIONS = {-1, 0, 5, 15, 60}


class ClosingConnection(sqlite3.Connection):
    def __exit__(self, exc_type, exc_value, traceback):
        result = super().__exit__(exc_type, exc_value, traceback)
        self.close()
        return result


def db_path():
    return Path(os.environ.get("NEXA_CALENDAR_DB_PATH", DEFAULT_DB_PATH))


def now_iso():
    return datetime.now().replace(microsecond=0).isoformat()


def _connect(path=None):
    target = Path(path) if path is not None else db_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(target, factory=ClosingConnection)
    conn.row_factory = sqlite3.Row
    return conn


def _call(fn, path=None):
    try:
        initialize(path)
        return fn()
    except sqlite3.DatabaseError as exc:
        return {"status": "error", "error": "calendar_database_error", "message": str(exc)}
    except Exception as exc:  # pragma: no cover - API safety boundary
        return {"status": "error", "error": "calendar_error", "message": str(exc)}


def initialize(path=None):
    with _connect(path) as conn:
        conn.executescript(
            """
            PRAGMA user_version = 1;
            CREATE TABLE IF NOT EXISTS calendar_events (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                start_date TEXT NOT NULL,
                start_time TEXT NOT NULL,
                repeat_type TEXT NOT NULL DEFAULT 'none',
                is_deleted INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS calendar_reminders (
                id INTEGER PRIMARY KEY,
                event_id INTEGER NOT NULL,
                enabled INTEGER NOT NULL DEFAULT 1,
                reminder_minutes_before INTEGER NOT NULL DEFAULT 0,
                triggered_at TEXT,
                dismissed_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS calendar_snoozes (
                id INTEGER PRIMARY KEY,
                event_id INTEGER NOT NULL,
                snoozed_until TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )
        return {"status": "ok", "schema_version": SCHEMA_VERSION, "db_path": str(Path(path) if path else db_path())}


def _rows(rows):
    return [dict(row) for row in rows]


def _parse_date(value):
    try:
        return datetime.strptime(str(value or ""), "%Y-%m-%d").date()
    except ValueError:
        return None


def _parse_time(value):
    try:
        return datetime.strptime(str(value or ""), "%H:%M").time()
    except ValueError:
        return None


def _event_datetime(event, occurrence_date=None):
    start_date = occurrence_date or _parse_date(event["start_date"])
    start_time = _parse_time(event["start_time"])
    return datetime.combine(start_date, start_time)


def _sanitize_event(event, occurrence_date=None, reminder=None):
    item = dict(event)
    item["is_deleted"] = bool(item.get("is_deleted", 0))
    item["occurrence_date"] = (occurrence_date or item["start_date"])
    item["occurrence_start"] = _event_datetime(item, _parse_date(item["occurrence_date"])).isoformat()
    reminder_item = dict(reminder) if reminder else {}
    item["has_reminder"] = bool(reminder_item and int(reminder_item.get("enabled", 0)) == 1)
    item["reminder_minutes_before"] = int(reminder_item.get("reminder_minutes_before", -1)) if reminder_item else -1
    return item


def _validate(title, start_date, start_time, repeat_type, reminder_minutes_before=None):
    name = str(title or "").strip()
    if not name:
        return None, {"status": "error", "error": "title_required", "message": "Event title is required."}
    parsed_date = _parse_date(start_date)
    if parsed_date is None:
        return None, {"status": "error", "error": "invalid_start_date", "message": "Use YYYY-MM-DD."}
    parsed_time = _parse_time(start_time)
    if parsed_time is None:
        return None, {"status": "error", "error": "invalid_start_time", "message": "Use HH:MM."}
    repeat = str(repeat_type or "none").lower()
    if repeat not in REPEAT_TYPES:
        return None, {"status": "error", "error": "invalid_repeat_type"}
    if reminder_minutes_before is not None and int(reminder_minutes_before) not in REMINDER_OPTIONS:
        return None, {"status": "error", "error": "invalid_reminder"}
    return (name, parsed_date, parsed_time, repeat), None


def _reminder_for(conn, event_id):
    return conn.execute("SELECT * FROM calendar_reminders WHERE event_id=? ORDER BY id DESC LIMIT 1", (int(event_id),)).fetchone()


def create(title, description="", start_date="", start_time="", reminder_minutes_before=0, repeat_type="none", snooze_minutes=0, path=None):
    def inner():
        validated, error = _validate(title, start_date, start_time, repeat_type, reminder_minutes_before)
        if error:
            return error
        name, parsed_date, parsed_time, repeat = validated
        reminder_minutes = int(reminder_minutes_before)
        stamp = now_iso()
        with _connect(path) as conn:
            cur = conn.execute(
                "INSERT INTO calendar_events(title,description,start_date,start_time,repeat_type,is_deleted,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)",
                (name, str(description or ""), parsed_date.isoformat(), parsed_time.strftime("%H:%M"), repeat, 0, stamp, stamp),
            )
            enabled = 0 if reminder_minutes < 0 else 1
            conn.execute(
                "INSERT INTO calendar_reminders(event_id,enabled,reminder_minutes_before,created_at,updated_at) VALUES(?,?,?,?,?)",
                (cur.lastrowid, enabled, max(0, reminder_minutes), stamp, stamp),
            )
            row = conn.execute("SELECT * FROM calendar_events WHERE id=?", (cur.lastrowid,)).fetchone()
            return {"status": "ok", "event": _sanitize_event(row, reminder=_reminder_for(conn, cur.lastrowid)), "snooze_minutes": int(snooze_minutes or 0)}
    return _call(inner, path)


def update(event_id, title, description="", start_date="", start_time="", reminder_minutes_before=0, repeat_type="none", path=None):
    def inner():
        validated, error = _validate(title, start_date, start_time, repeat_type, reminder_minutes_before)
        if error:
            return error
        name, parsed_date, parsed_time, repeat = validated
        reminder_minutes = int(reminder_minutes_before)
        stamp = now_iso()
        with _connect(path) as conn:
            row = conn.execute("SELECT * FROM calendar_events WHERE id=? AND is_deleted=0", (int(event_id or 0),)).fetchone()
            if not row:
                return {"status": "error", "error": "event_not_found"}
            conn.execute(
                "UPDATE calendar_events SET title=?, description=?, start_date=?, start_time=?, repeat_type=?, updated_at=? WHERE id=?",
                (name, str(description or ""), parsed_date.isoformat(), parsed_time.strftime("%H:%M"), repeat, stamp, int(event_id)),
            )
            enabled = 0 if reminder_minutes < 0 else 1
            if _reminder_for(conn, event_id):
                conn.execute(
                    "UPDATE calendar_reminders SET enabled=?, reminder_minutes_before=?, triggered_at=NULL, dismissed_at=NULL, updated_at=? WHERE event_id=?",
                    (enabled, max(0, reminder_minutes), stamp, int(event_id)),
                )
            else:
                conn.execute(
                    "INSERT INTO calendar_reminders(event_id,enabled,reminder_minutes_before,created_at,updated_at) VALUES(?,?,?,?,?)",
                    (int(event_id), enabled, max(0, reminder_minutes), stamp, stamp),
                )
            updated = conn.execute("SELECT * FROM calendar_events WHERE id=?", (int(event_id),)).fetchone()
            return {"status": "ok", "event": _sanitize_event(updated, reminder=_reminder_for(conn, event_id))}
    return _call(inner, path)


def delete(event_id, confirm_text="", path=None):
    def inner():
        if confirm_text != DELETE_CONFIRM:
            return {"status": "error", "error": "confirmation_required"}
        stamp = now_iso()
        with _connect(path) as conn:
            conn.execute("UPDATE calendar_events SET is_deleted=1, updated_at=? WHERE id=?", (stamp, int(event_id or 0)))
            return {"status": "ok", "deleted": int(event_id or 0)}
    return _call(inner, path)


def _events(conn):
    return _rows(conn.execute("SELECT * FROM calendar_events WHERE is_deleted=0 ORDER BY start_date ASC, start_time ASC, id ASC"))


def _occurs_on(event, target_date):
    start = _parse_date(event["start_date"])
    if target_date < start:
        return False
    repeat = str(event.get("repeat_type", "none"))
    if repeat == "none":
        return target_date == start
    if repeat == "daily":
        return True
    if repeat == "weekly":
        return target_date.weekday() == start.weekday()
    if repeat == "monthly":
        return target_date.day == start.day
    if repeat == "yearly":
        return target_date.month == start.month and target_date.day == start.day
    return False


def _expand_events(conn, start, end):
    reminders = {int(row["event_id"]): dict(row) for row in conn.execute("SELECT * FROM calendar_reminders")}
    out = []
    for event in _events(conn):
        current = start
        while current <= end:
            if _occurs_on(event, current):
                out.append(_sanitize_event(event, current.isoformat(), reminders.get(int(event["id"]))))
            current += timedelta(days=1)
    out.sort(key=lambda item: (item["occurrence_date"], item["start_time"], item["id"]))
    return out


def month(year=None, month=None, selected_date="", path=None):
    def inner():
        today = date.today()
        y = int(year or today.year)
        m = int(month or today.month)
        first = date(y, m, 1)
        grid_start = first - timedelta(days=first.weekday())
        grid_end = grid_start + timedelta(days=41)
        selected = _parse_date(selected_date) if selected_date else None
        with _connect(path) as conn:
            occurrences = _expand_events(conn, grid_start, grid_end)
            events_by_date = {}
            for item in occurrences:
                events_by_date.setdefault(item["occurrence_date"], []).append(item)
            weeks = []
            for week_index in range(6):
                cells = []
                for day_index in range(7):
                    current = grid_start + timedelta(days=week_index * 7 + day_index)
                    day_events = events_by_date.get(current.isoformat(), [])
                    cells.append({
                        "day_number": current.day,
                        "full_date": current.isoformat(),
                        "is_current_month": current.month == m,
                        "is_today": current == today,
                        "is_selected": current == selected,
                        "is_sunday": current.weekday() == 6,
                        "events_count": len(day_events),
                        "has_reminder": any(bool(item.get("has_reminder", False)) for item in day_events),
                    })
                weeks.append({"cells": cells})
            return {
                "status": "ok",
                "year": y,
                "month": m,
                "month_name": calendar_lib.month_name[m],
                "weeks": weeks,
                "events_by_date": events_by_date,
                "today": today.isoformat(),
            }
    return _call(inner, path)


def day(day_date="", path=None):
    def inner():
        target = _parse_date(day_date) or date.today()
        with _connect(path) as conn:
            events = [item for item in _expand_events(conn, target, target) if item["occurrence_date"] == target.isoformat()]
        return {
            "status": "ok",
            "date": target.isoformat(),
            "display_date": target.strftime("%A, %d %B %Y"),
            "events": events,
        }
    return _call(inner, path)


def _latest_snooze(conn, event_id):
    row = conn.execute(
        "SELECT * FROM calendar_snoozes WHERE event_id=? AND status='active' ORDER BY snoozed_until DESC, id DESC LIMIT 1",
        (int(event_id),),
    ).fetchone()
    return dict(row) if row else None


def due(path=None):
    def inner():
        now = datetime.now().replace(microsecond=0)
        start = (now - timedelta(days=1)).date()
        end = (now + timedelta(days=1)).date()
        due_items = []
        stamp = now_iso()
        with _connect(path) as conn:
            occurrences = _expand_events(conn, start, end)
            for item in occurrences:
                event_id = int(item["id"])
                reminder = _reminder_for(conn, event_id)
                if not reminder or int(reminder["enabled"]) != 1:
                    continue
                occurrence_start = datetime.fromisoformat(item["occurrence_start"])
                reminder_time = occurrence_start - timedelta(minutes=int(reminder["reminder_minutes_before"]))
                snooze_row = _latest_snooze(conn, event_id)
                if snooze_row:
                    snooze_until = datetime.fromisoformat(snooze_row["snoozed_until"])
                    if snooze_until > now:
                        continue
                    reminder_time = snooze_until
                dismissed_at = str(reminder["dismissed_at"] or "")
                if dismissed_at == item["occurrence_start"]:
                    continue
                if reminder_time <= now and occurrence_start >= now - timedelta(days=1):
                    conn.execute(
                        "UPDATE calendar_reminders SET triggered_at=COALESCE(triggered_at, ?), updated_at=? WHERE event_id=?",
                        (item["occurrence_start"], stamp, event_id),
                    )
                    item["reminder_minutes_before"] = int(reminder["reminder_minutes_before"])
                    item["notification_id"] = "calendar:%d:%s" % (event_id, item["occurrence_start"])
                    item["starts_label"] = item["start_time"]
                    due_items.append(item)
            due_items.sort(key=lambda row: (row["occurrence_start"], row["id"]))
            return {"status": "ok", "due": due_items, "count": len(due_items), "now": now.isoformat()}
    return _call(inner, path)


def dismiss(event_id, occurrence_start="", path=None):
    def inner():
        stamp = now_iso()
        with _connect(path) as conn:
            row = conn.execute("SELECT * FROM calendar_events WHERE id=? AND is_deleted=0", (int(event_id or 0),)).fetchone()
            if not row:
                return {"status": "error", "error": "event_not_found"}
            dismissed_value = str(occurrence_start or _event_datetime(row).isoformat())
            conn.execute("UPDATE calendar_reminders SET dismissed_at=?, updated_at=? WHERE event_id=?", (dismissed_value, stamp, int(event_id)))
            return {"status": "ok"}
    return _call(inner, path)


def snooze(event_id, minutes=10, path=None):
    def inner():
        stamp = now_iso()
        snoozed_until = (datetime.now().replace(microsecond=0) + timedelta(minutes=int(minutes or 10))).isoformat()
        with _connect(path) as conn:
            conn.execute("UPDATE calendar_snoozes SET status='dismissed', updated_at=? WHERE event_id=? AND status='active'", (stamp, int(event_id or 0)))
            conn.execute(
                "INSERT INTO calendar_snoozes(event_id,snoozed_until,status,created_at,updated_at) VALUES(?,?,?,?,?)",
                (int(event_id or 0), snoozed_until, "active", stamp, stamp),
            )
            return {"status": "ok", "event_id": int(event_id or 0), "snoozed_until": snoozed_until}
    return _call(inner, path)


def settings_stats(path=None):
    def inner():
        target = Path(path) if path else db_path()
        with _connect(path) as conn:
            return {
                "status": "ok",
                "schema_version": SCHEMA_VERSION,
                "total_events": conn.execute("SELECT COUNT(*) AS c FROM calendar_events WHERE is_deleted=0").fetchone()["c"],
                "deleted_events": conn.execute("SELECT COUNT(*) AS c FROM calendar_events WHERE is_deleted=1").fetchone()["c"],
                "database_path": str(target),
                "database_size_bytes": target.stat().st_size if target.exists() else 0,
            }
    return _call(inner, path)
