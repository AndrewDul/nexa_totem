"""SQLite-backed local Reminders store."""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from system.services.settings import settings_store


DEFAULT_DB_PATH = Path("var/data/reminders/nexa_reminders.db")
SCHEMA_VERSION = 1
DELETE_CONFIRM = "DELETE_REMINDER"


class ClosingConnection(sqlite3.Connection):
    def __exit__(self, exc_type, exc_value, traceback):
        result = super().__exit__(exc_type, exc_value, traceback)
        self.close()
        return result


def db_path():
    return Path(os.environ.get("NEXA_REMINDERS_DB_PATH", DEFAULT_DB_PATH))


def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _connect(path=None):
    target = Path(path) if path is not None else db_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(target, factory=ClosingConnection)
    conn.row_factory = sqlite3.Row
    return conn


def _row(row):
    return dict(row) if row is not None else None


def _rows(rows):
    return [dict(row) for row in rows]


def _call(fn, path=None):
    try:
        initialize(path)
        return fn()
    except sqlite3.DatabaseError as exc:
        return {"status": "error", "error": "reminders_database_error", "message": str(exc)}
    except Exception as exc:  # pragma: no cover - API safety boundary
        return {"status": "error", "error": "reminders_error", "message": str(exc)}


def initialize(path=None):
    with _connect(path) as conn:
        conn.executescript(
            """
            PRAGMA user_version = 1;
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                notes TEXT,
                due_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                is_private INTEGER NOT NULL DEFAULT 0,
                triggered_at TEXT,
                dismissed_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS reminder_events (
                id INTEGER PRIMARY KEY,
                reminder_id INTEGER,
                event_type TEXT NOT NULL,
                summary TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        return {"status": "ok", "schema_version": SCHEMA_VERSION, "db_path": str(Path(path) if path else db_path())}


def _event(conn, reminder_id, event_type, summary):
    conn.execute(
        "INSERT INTO reminder_events(reminder_id,event_type,summary,created_at) VALUES(?,?,?,?)",
        (reminder_id, event_type, summary, now_iso()),
    )


def _parse_datetime(value):
    text = str(value or "").strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        # Naive UI values are local wall time from Godot's system clock.
        parsed = parsed.astimezone()
    return parsed.astimezone(timezone.utc).replace(microsecond=0)


def _sanitize(row, hide_private=False):
    item = dict(row)
    item["is_private"] = bool(item.get("is_private", 0))
    item["requires_pin"] = False
    if hide_private and item["is_private"]:
        item["title"] = "Private reminder locked"
        item["notes"] = ""
        item["requires_pin"] = True
    return item


def _hide_private():
    settings_path = os.environ.get("NEXA_SETTINGS_PATH")
    if settings_path:
        return settings_store.should_hide_private_reminders(settings_store.load_settings(Path(settings_path)))
    return settings_store.should_hide_private_reminders()


def _refresh_due(conn, now_dt):
    stamp = now_dt.isoformat()
    rows = conn.execute(
        "SELECT * FROM reminders WHERE status='active' AND due_at<=?",
        (stamp,),
    ).fetchall()
    for row in rows:
        conn.execute(
            "UPDATE reminders SET status='due', triggered_at=COALESCE(triggered_at, ?), updated_at=? WHERE id=?",
            (stamp, stamp, row["id"]),
        )
        _event(conn, row["id"], "due", "Reminder became due")


def create(title, notes="", due_at="", is_private=False, path=None):
    def inner():
        name = str(title or "").strip()
        parsed = _parse_datetime(due_at)
        if not name:
            return {"status": "error", "error": "title_required", "message": "Reminder text is required."}
        if parsed is None:
            return {"status": "error", "error": "invalid_due_at", "message": "Valid due_at is required."}
        stamp = now_iso()
        due_text = parsed.isoformat()
        status = "active" if parsed > datetime.now(timezone.utc) else "due"
        with _connect(path) as conn:
            cur = conn.execute(
                "INSERT INTO reminders(title,notes,due_at,status,is_private,triggered_at,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)",
                (name, str(notes or ""), due_text, status, 1 if is_private else 0, stamp if status == "due" else None, stamp, stamp),
            )
            _event(conn, cur.lastrowid, "created", f"Created reminder: {name}")
            return {"status": "ok", "reminder": _sanitize(conn.execute("SELECT * FROM reminders WHERE id=?", (cur.lastrowid,)).fetchone(), _hide_private())}
    return _call(inner, path)


def update(reminder_id, title, notes="", due_at="", is_private=False, path=None):
    def inner():
        name = str(title or "").strip()
        parsed = _parse_datetime(due_at)
        if not name:
            return {"status": "error", "error": "title_required", "message": "Reminder text is required."}
        if parsed is None:
            return {"status": "error", "error": "invalid_due_at", "message": "Valid due_at is required."}
        status = "active" if parsed > datetime.now(timezone.utc) else "due"
        stamp = now_iso()
        with _connect(path) as conn:
            row = conn.execute("SELECT * FROM reminders WHERE id=?", (int(reminder_id or 0),)).fetchone()
            if not row:
                return {"status": "error", "error": "reminder_not_found"}
            conn.execute(
                "UPDATE reminders SET title=?, notes=?, due_at=?, status=?, is_private=?, triggered_at=?, dismissed_at=NULL, updated_at=? WHERE id=?",
                (name, str(notes or ""), parsed.isoformat(), status, 1 if is_private else 0, stamp if status == "due" else None, stamp, row["id"]),
            )
            _event(conn, row["id"], "updated", f"Updated reminder: {name}")
            return {"status": "ok", "reminder": _sanitize(conn.execute("SELECT * FROM reminders WHERE id=?", (row["id"],)).fetchone(), _hide_private())}
    return _call(inner, path)


def list_reminders(path=None):
    def inner():
        now_dt = datetime.now(timezone.utc).replace(microsecond=0)
        hide_private = _hide_private()
        with _connect(path) as conn:
            _refresh_due(conn, now_dt)
            upcoming = _rows(conn.execute("SELECT * FROM reminders WHERE due_at>? ORDER BY due_at ASC, id ASC", (now_dt.isoformat(),)))
            past = _rows(conn.execute("SELECT * FROM reminders WHERE due_at<=? ORDER BY due_at DESC, id DESC", (now_dt.isoformat(),)))
            return {
                "status": "ok",
                "upcoming": [_sanitize(item, hide_private) for item in upcoming],
                "past": [_sanitize(item, hide_private) for item in past],
                "selected": None,
                "next_due_at": upcoming[0]["due_at"] if upcoming else "",
                "now": now_dt.isoformat(),
            }
    return _call(inner, path)


def due(path=None):
    def inner():
        now_dt = datetime.now(timezone.utc).replace(microsecond=0)
        hide_private = _hide_private()
        with _connect(path) as conn:
            _refresh_due(conn, now_dt)
            rows = conn.execute(
                "SELECT * FROM reminders WHERE due_at<=? AND status IN ('active','due') AND dismissed_at IS NULL ORDER BY due_at ASC, id ASC",
                (now_dt.isoformat(),),
            ).fetchall()
            next_row = conn.execute("SELECT due_at FROM reminders WHERE status='active' AND due_at>? ORDER BY due_at ASC, id ASC LIMIT 1", (now_dt.isoformat(),)).fetchone()
            return {"status": "ok", "due": [_sanitize(row, hide_private) for row in rows], "count": len(rows), "next_due_at": next_row["due_at"] if next_row else "", "now": now_dt.isoformat()}
    return _call(inner, path)


def mark_triggered(reminder_id, path=None):
    def inner():
        stamp = now_iso()
        with _connect(path) as conn:
            conn.execute("UPDATE reminders SET status='due', triggered_at=COALESCE(triggered_at, ?), updated_at=? WHERE id=?", (stamp, stamp, int(reminder_id or 0)))
            _event(conn, int(reminder_id or 0), "triggered", "Reminder notification shown")
            row = conn.execute("SELECT * FROM reminders WHERE id=?", (int(reminder_id or 0),)).fetchone()
            return {"status": "ok", "reminder": _sanitize(row, _hide_private())}
    return _call(inner, path)


def dismiss(reminder_id, path=None):
    def inner():
        stamp = now_iso()
        with _connect(path) as conn:
            conn.execute("UPDATE reminders SET status='dismissed', dismissed_at=?, updated_at=? WHERE id=?", (stamp, stamp, int(reminder_id or 0)))
            _event(conn, int(reminder_id or 0), "dismissed", "Dismissed reminder")
            return {"status": "ok"}
    return _call(inner, path)


def snooze(reminder_id, minutes=5, path=None):
    def inner():
        due_text = (datetime.now(timezone.utc).replace(microsecond=0) + timedelta(minutes=int(minutes or 5))).isoformat()
        stamp = now_iso()
        with _connect(path) as conn:
            conn.execute("UPDATE reminders SET due_at=?, status='active', triggered_at=NULL, dismissed_at=NULL, updated_at=? WHERE id=?", (due_text, stamp, int(reminder_id or 0)))
            _event(conn, int(reminder_id or 0), "snoozed", f"Snoozed reminder +{int(minutes or 5)}m")
            row = conn.execute("SELECT * FROM reminders WHERE id=?", (int(reminder_id or 0),)).fetchone()
            return {"status": "ok", "reminder": _sanitize(row, _hide_private())}
    return _call(inner, path)


def delete(reminder_id, confirm_text="", path=None):
    def inner():
        if confirm_text != DELETE_CONFIRM:
            return {"status": "error", "error": "confirmation_required"}
        with _connect(path) as conn:
            conn.execute("DELETE FROM reminders WHERE id=?", (int(reminder_id or 0),))
            _event(conn, int(reminder_id or 0), "deleted", "Deleted reminder")
            return {"status": "ok", "deleted": int(reminder_id or 0)}
    return _call(inner, path)


def overview(path=None):
    payload = list_reminders(path)
    if payload.get("status") != "ok":
        return payload
    due_payload = due(path)
    payload["due_count"] = int(due_payload.get("count", 0))
    payload["next_due_at"] = payload["upcoming"][0]["due_at"] if payload.get("upcoming") else ""
    return payload


def settings_stats(path=None):
    def inner():
        with _connect(path) as conn:
            return {
                "status": "ok",
                "schema_version": SCHEMA_VERSION,
                "total_reminders": conn.execute("SELECT COUNT(*) AS c FROM reminders").fetchone()["c"],
                "active_reminders": conn.execute("SELECT COUNT(*) AS c FROM reminders WHERE status='active'").fetchone()["c"],
                "past_reminders": conn.execute("SELECT COUNT(*) AS c FROM reminders WHERE status!='active'").fetchone()["c"],
                "database_path": str(Path(path) if path else db_path()),
                "database_size_bytes": (Path(path) if path else db_path()).stat().st_size if (Path(path) if path else db_path()).exists() else 0,
            }
    return _call(inner, path)
