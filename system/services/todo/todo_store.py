"""SQLite-backed local To Do store."""

from __future__ import annotations

import os
import sqlite3
from datetime import date, datetime, time, timedelta
from pathlib import Path


DEFAULT_DB_PATH = Path("var/data/todo/nexa_todo.db")
SCHEMA_VERSION = 1
DELETE_TASK_CONFIRM = "DELETE_TODO_TASK"
DELETE_LIST_CONFIRM = "DELETE_TODO_LIST"
TASK_STATUSES = {"active", "completed", "paused", "archived"}
REPEAT_UNITS = {"none", "hours", "days", "weekly", "monthly", "yearly"}


class ClosingConnection(sqlite3.Connection):
    def __exit__(self, exc_type, exc_value, traceback):
        result = super().__exit__(exc_type, exc_value, traceback)
        self.close()
        return result


def db_path():
    return Path(os.environ.get("NEXA_TODO_DB_PATH", DEFAULT_DB_PATH))


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
        return {"status": "error", "error": "todo_database_error", "message": str(exc)}
    except Exception as exc:  # pragma: no cover - API safety boundary
        return {"status": "error", "error": "todo_error", "message": str(exc)}


def initialize(path=None):
    with _connect(path) as conn:
        conn.executescript(
            """
            PRAGMA user_version = 1;
            CREATE TABLE IF NOT EXISTS todo_lists (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                emoji TEXT NOT NULL DEFAULT '📥',
                sort_order INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                is_deleted INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS todo_tasks (
                id INTEGER PRIMARY KEY,
                list_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                notes TEXT,
                status TEXT NOT NULL DEFAULT 'active',
                due_date TEXT,
                due_time TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                completed_at TEXT,
                is_deleted INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS todo_reminders (
                id INTEGER PRIMARY KEY,
                task_id INTEGER NOT NULL,
                enabled INTEGER NOT NULL DEFAULT 0,
                next_reminder_at TEXT,
                last_reminded_at TEXT,
                repeat_unit TEXT NOT NULL DEFAULT 'none',
                repeat_interval INTEGER NOT NULL DEFAULT 0,
                repeat_until TEXT,
                snoozed_until TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS todo_notification_log (
                id INTEGER PRIMARY KEY,
                task_id INTEGER NOT NULL,
                notification_id TEXT,
                shown_at TEXT NOT NULL,
                action_taken TEXT,
                snoozed_until TEXT,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS todo_events (
                id INTEGER PRIMARY KEY,
                event_type TEXT NOT NULL,
                list_id INTEGER,
                task_id INTEGER,
                summary TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        _ensure_inbox(conn)
        return {"status": "ok", "schema_version": SCHEMA_VERSION, "db_path": str(Path(path) if path else db_path())}


def _ensure_inbox(conn):
    row = conn.execute("SELECT id FROM todo_lists WHERE is_deleted=0 LIMIT 1").fetchone()
    if row:
        return
    stamp = now_iso()
    conn.execute(
        "INSERT INTO todo_lists(name,emoji,sort_order,created_at,updated_at,is_deleted) VALUES(?,?,?,?,?,0)",
        ("Inbox", "📥", 0, stamp, stamp),
    )


def _rows(rows):
    return [dict(row) for row in rows]


def _parse_date(value):
    if value in (None, ""):
        return None
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except ValueError:
        return None


def _parse_time(value):
    if value in (None, ""):
        return None
    try:
        return datetime.strptime(str(value), "%H:%M").time()
    except ValueError:
        return None


def _task_due_at(task):
    parsed_date = _parse_date(task.get("due_date"))
    parsed_time = _parse_time(task.get("due_time"))
    if parsed_date is None or parsed_time is None:
        return None
    return datetime.combine(parsed_date, parsed_time)


def _validate_list(name):
    clean = str(name or "").strip()
    if not clean:
        return None, {"status": "error", "error": "name_required", "message": "List name is required."}
    return clean[:64], None


def _validate_repeat(repeat_unit, repeat_interval):
    unit = str(repeat_unit or "none").lower()
    if unit not in REPEAT_UNITS:
        return None, None, {"status": "error", "error": "invalid_repeat_unit"}
    interval = int(repeat_interval or 0)
    if unit in {"hours", "days"}:
        if interval < 1 or interval > 999:
            return None, None, {"status": "error", "error": "invalid_repeat_interval"}
    elif unit != "none":
        interval = 1
    else:
        interval = 0
    return unit, interval, None


def _validate_task(title, due_date, due_time, reminder_enabled, repeat_unit, repeat_interval, status="active"):
    clean = str(title or "").strip()
    if not clean:
        return None, {"status": "error", "error": "title_required", "message": "Task title is required."}
    task_status = str(status or "active").lower()
    if task_status not in TASK_STATUSES:
        return None, {"status": "error", "error": "invalid_status"}
    unit, interval, error = _validate_repeat(repeat_unit, repeat_interval)
    if error:
        return None, error
    parsed_date = _parse_date(due_date)
    parsed_time = _parse_time(due_time)
    if reminder_enabled and parsed_date is None:
        return None, {"status": "error", "error": "invalid_due_date", "message": "Use YYYY-MM-DD."}
    if reminder_enabled and parsed_time is None:
        return None, {"status": "error", "error": "invalid_due_time", "message": "Use HH:MM."}
    if due_date not in (None, "") and parsed_date is None:
        return None, {"status": "error", "error": "invalid_due_date", "message": "Use YYYY-MM-DD."}
    if due_time not in (None, "") and parsed_time is None:
        return None, {"status": "error", "error": "invalid_due_time", "message": "Use HH:MM."}
    return {
        "title": clean,
        "due_date": parsed_date.isoformat() if parsed_date else "",
        "due_time": parsed_time.strftime("%H:%M") if parsed_time else "",
        "status": task_status,
        "repeat_unit": unit,
        "repeat_interval": interval,
        "reminder_enabled": bool(reminder_enabled),
    }, None


def _log(conn, event_type, summary, list_id=None, task_id=None):
    conn.execute(
        "INSERT INTO todo_events(event_type,list_id,task_id,summary,created_at) VALUES(?,?,?,?,?)",
        (event_type, list_id, task_id, summary, now_iso()),
    )


def _reminder_for(conn, task_id):
    return conn.execute("SELECT * FROM todo_reminders WHERE task_id=? ORDER BY id DESC LIMIT 1", (int(task_id),)).fetchone()


def _list_for(conn, list_id):
    return conn.execute("SELECT * FROM todo_lists WHERE id=? AND is_deleted=0", (int(list_id or 0),)).fetchone()


def _sanitize_task(task, reminder=None, list_row=None):
    item = dict(task)
    item["is_deleted"] = bool(item.get("is_deleted", 0))
    item["is_completed"] = str(item.get("status", "")) == "completed"
    due_at = _task_due_at(item)
    item["due_at"] = due_at.isoformat() if due_at else ""
    item["overdue"] = bool(due_at and due_at < datetime.now().replace(microsecond=0) and item["status"] == "active")
    rem = dict(reminder) if reminder else {}
    item["reminder_enabled"] = bool(rem and int(rem.get("enabled", 0)) == 1)
    item["next_reminder_at"] = str(rem.get("next_reminder_at", "")) if rem else ""
    item["repeat_unit"] = str(rem.get("repeat_unit", "none")) if rem else "none"
    item["repeat_interval"] = int(rem.get("repeat_interval", 0)) if rem else 0
    item["snoozed_until"] = str(rem.get("snoozed_until") or "") if rem else ""
    if list_row:
        item["list_name"] = str(list_row["name"])
        item["list_emoji"] = str(list_row["emoji"])
    return item


def create_list(name, emoji="📥", path=None):
    def inner():
        clean, error = _validate_list(name)
        if error:
            return error
        stamp = now_iso()
        with _connect(path) as conn:
            sort_order = conn.execute("SELECT COALESCE(MAX(sort_order), 0) + 1 AS n FROM todo_lists").fetchone()["n"]
            cur = conn.execute(
                "INSERT INTO todo_lists(name,emoji,sort_order,created_at,updated_at,is_deleted) VALUES(?,?,?,?,?,0)",
                (clean, str(emoji or "📥")[:4], int(sort_order), stamp, stamp),
            )
            _log(conn, "list_created", "Created list " + clean, cur.lastrowid)
            return {"status": "ok", "list": _list_summary(conn, cur.lastrowid)}
    return _call(inner, path)


def update_list(list_id, name, emoji="📥", path=None):
    def inner():
        clean, error = _validate_list(name)
        if error:
            return error
        stamp = now_iso()
        with _connect(path) as conn:
            if not _list_for(conn, list_id):
                return {"status": "error", "error": "list_not_found"}
            conn.execute("UPDATE todo_lists SET name=?, emoji=?, updated_at=? WHERE id=?", (clean, str(emoji or "📥")[:4], stamp, int(list_id)))
            _log(conn, "list_updated", "Updated list " + clean, int(list_id))
            return {"status": "ok", "list": _list_summary(conn, list_id)}
    return _call(inner, path)


def delete_list(list_id, confirm_text="", path=None):
    def inner():
        if confirm_text != DELETE_LIST_CONFIRM:
            return {"status": "error", "error": "confirmation_required"}
        stamp = now_iso()
        with _connect(path) as conn:
            conn.execute("UPDATE todo_lists SET is_deleted=1, updated_at=? WHERE id=?", (stamp, int(list_id or 0)))
            conn.execute("UPDATE todo_tasks SET is_deleted=1, updated_at=? WHERE list_id=?", (stamp, int(list_id or 0)))
            _log(conn, "list_deleted", "Deleted list", int(list_id or 0))
            _ensure_inbox(conn)
            return {"status": "ok", "deleted": int(list_id or 0)}
    return _call(inner, path)


def _list_summary(conn, list_id):
    row = _list_for(conn, list_id)
    if not row:
        return {}
    today = date.today().isoformat()
    stats = conn.execute(
        """
        SELECT
            COUNT(*) AS total_tasks,
            SUM(CASE WHEN status='active' THEN 1 ELSE 0 END) AS active_tasks,
            SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) AS completed_tasks,
            SUM(CASE WHEN status='active' AND due_date=? THEN 1 ELSE 0 END) AS due_today,
            SUM(CASE WHEN status='active' AND due_date IS NOT NULL AND due_date!='' AND (due_date < ? OR (due_date=? AND due_time < ?)) THEN 1 ELSE 0 END) AS overdue
        FROM todo_tasks WHERE list_id=? AND is_deleted=0
        """,
        (today, today, today, datetime.now().strftime("%H:%M"), int(list_id)),
    ).fetchone()
    return {
        "id": int(row["id"]),
        "name": str(row["name"]),
        "emoji": str(row["emoji"]),
        "total_tasks": int(stats["total_tasks"] or 0),
        "active_tasks": int(stats["active_tasks"] or 0),
        "completed_tasks": int(stats["completed_tasks"] or 0),
        "due_today": int(stats["due_today"] or 0),
        "overdue": int(stats["overdue"] or 0),
    }


def lists(path=None):
    def inner():
        with _connect(path) as conn:
            rows = conn.execute("SELECT id FROM todo_lists WHERE is_deleted=0 ORDER BY sort_order ASC, id ASC").fetchall()
            return {"status": "ok", "lists": [_list_summary(conn, row["id"]) for row in rows]}
    return _call(inner, path)


def overview(path=None):
    def inner():
        with _connect(path) as conn:
            stats = settings_stats(path)
            return {"status": "ok", "lists": lists(path).get("lists", []), "stats": stats}
    return _call(inner, path)


def tasks(list_id=0, path=None):
    def inner():
        with _connect(path) as conn:
            row = _list_for(conn, list_id)
            if not row:
                row = conn.execute("SELECT * FROM todo_lists WHERE is_deleted=0 ORDER BY sort_order ASC, id ASC LIMIT 1").fetchone()
            if not row:
                _ensure_inbox(conn)
                row = conn.execute("SELECT * FROM todo_lists WHERE is_deleted=0 ORDER BY sort_order ASC, id ASC LIMIT 1").fetchone()
            raw_tasks = conn.execute(
                "SELECT * FROM todo_tasks WHERE list_id=? AND is_deleted=0 ORDER BY status ASC, due_date ASC, due_time ASC, id ASC",
                (int(row["id"]),),
            ).fetchall()
            active = []
            completed = []
            for task in raw_tasks:
                item = _sanitize_task(task, _reminder_for(conn, task["id"]), row)
                if item["status"] == "completed":
                    completed.append(item)
                else:
                    active.append(item)
            return {"status": "ok", "list": dict(row), "active": active, "completed": completed}
    return _call(inner, path)


def _write_reminder(conn, task_id, enabled, due_at, repeat_unit, repeat_interval, clear_snooze=True):
    stamp = now_iso()
    next_at = due_at.isoformat() if enabled and due_at else None
    existing = _reminder_for(conn, task_id)
    snooze_value = None if clear_snooze else (existing["snoozed_until"] if existing else None)
    if existing:
        conn.execute(
            "UPDATE todo_reminders SET enabled=?, next_reminder_at=?, repeat_unit=?, repeat_interval=?, snoozed_until=?, updated_at=? WHERE task_id=?",
            (1 if enabled else 0, next_at, repeat_unit, int(repeat_interval), snooze_value, stamp, int(task_id)),
        )
    else:
        conn.execute(
            "INSERT INTO todo_reminders(task_id,enabled,next_reminder_at,repeat_unit,repeat_interval,snoozed_until,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)",
            (int(task_id), 1 if enabled else 0, next_at, repeat_unit, int(repeat_interval), snooze_value, stamp, stamp),
        )


def create_task(list_id, title, notes="", due_date="", due_time="", reminder_enabled=False, repeat_unit="none", repeat_interval=0, path=None):
    def inner():
        validated, error = _validate_task(title, due_date, due_time, reminder_enabled, repeat_unit, repeat_interval)
        if error:
            return error
        stamp = now_iso()
        with _connect(path) as conn:
            if not _list_for(conn, list_id):
                return {"status": "error", "error": "list_not_found"}
            cur = conn.execute(
                "INSERT INTO todo_tasks(list_id,title,notes,status,due_date,due_time,created_at,updated_at,is_deleted) VALUES(?,?,?,?,?,?,?,?,0)",
                (int(list_id), validated["title"], str(notes or ""), "active", validated["due_date"], validated["due_time"], stamp, stamp),
            )
            _write_reminder(conn, cur.lastrowid, validated["reminder_enabled"], _task_due_at(validated), validated["repeat_unit"], validated["repeat_interval"])
            _log(conn, "task_created", "Created task " + validated["title"], int(list_id), cur.lastrowid)
            task = conn.execute("SELECT * FROM todo_tasks WHERE id=?", (cur.lastrowid,)).fetchone()
            return {"status": "ok", "task": _sanitize_task(task, _reminder_for(conn, cur.lastrowid), _list_for(conn, list_id))}
    return _call(inner, path)


def update_task(task_id, list_id, title, notes="", due_date="", due_time="", reminder_enabled=False, repeat_unit="none", repeat_interval=0, status="active", path=None):
    def inner():
        validated, error = _validate_task(title, due_date, due_time, reminder_enabled, repeat_unit, repeat_interval, status)
        if error:
            return error
        stamp = now_iso()
        with _connect(path) as conn:
            row = conn.execute("SELECT * FROM todo_tasks WHERE id=? AND is_deleted=0", (int(task_id or 0),)).fetchone()
            if not row:
                return {"status": "error", "error": "task_not_found"}
            if not _list_for(conn, list_id):
                return {"status": "error", "error": "list_not_found"}
            completed_at = stamp if validated["status"] == "completed" and row["status"] != "completed" else row["completed_at"]
            if validated["status"] == "active":
                completed_at = None
            conn.execute(
                "UPDATE todo_tasks SET list_id=?, title=?, notes=?, status=?, due_date=?, due_time=?, completed_at=?, updated_at=? WHERE id=?",
                (int(list_id), validated["title"], str(notes or ""), validated["status"], validated["due_date"], validated["due_time"], completed_at, stamp, int(task_id)),
            )
            enabled = validated["reminder_enabled"] and validated["status"] == "active"
            _write_reminder(conn, task_id, enabled, _task_due_at(validated), validated["repeat_unit"], validated["repeat_interval"])
            _log(conn, "task_updated", "Updated task " + validated["title"], int(list_id), int(task_id))
            task = conn.execute("SELECT * FROM todo_tasks WHERE id=?", (int(task_id),)).fetchone()
            return {"status": "ok", "task": _sanitize_task(task, _reminder_for(conn, task_id), _list_for(conn, list_id))}
    return _call(inner, path)


def delete_task(task_id, confirm_text="", path=None):
    def inner():
        if confirm_text != DELETE_TASK_CONFIRM:
            return {"status": "error", "error": "confirmation_required"}
        stamp = now_iso()
        with _connect(path) as conn:
            row = conn.execute("SELECT * FROM todo_tasks WHERE id=?", (int(task_id or 0),)).fetchone()
            conn.execute("UPDATE todo_tasks SET is_deleted=1, updated_at=? WHERE id=?", (stamp, int(task_id or 0)))
            if row:
                _log(conn, "task_deleted", "Deleted task", int(row["list_id"]), int(task_id or 0))
            return {"status": "ok", "deleted": int(task_id or 0)}
    return _call(inner, path)


def mark_done(task_id, path=None):
    def inner():
        stamp = now_iso()
        with _connect(path) as conn:
            row = conn.execute("SELECT * FROM todo_tasks WHERE id=? AND is_deleted=0", (int(task_id or 0),)).fetchone()
            if not row:
                return {"status": "error", "error": "task_not_found"}
            conn.execute("UPDATE todo_tasks SET status='completed', completed_at=?, updated_at=? WHERE id=?", (stamp, stamp, int(task_id)))
            conn.execute("UPDATE todo_reminders SET enabled=0, snoozed_until=NULL, updated_at=? WHERE task_id=?", (stamp, int(task_id)))
            _log(conn, "task_completed", "Completed task", int(row["list_id"]), int(task_id))
            task = conn.execute("SELECT * FROM todo_tasks WHERE id=?", (int(task_id),)).fetchone()
            return {"status": "ok", "task": _sanitize_task(task, _reminder_for(conn, task_id), _list_for(conn, row["list_id"]))}
    return _call(inner, path)


def mark_active(task_id, path=None):
    def inner():
        stamp = now_iso()
        with _connect(path) as conn:
            row = conn.execute("SELECT * FROM todo_tasks WHERE id=? AND is_deleted=0", (int(task_id or 0),)).fetchone()
            if not row:
                return {"status": "error", "error": "task_not_found"}
            conn.execute("UPDATE todo_tasks SET status='active', completed_at=NULL, updated_at=? WHERE id=?", (stamp, int(task_id)))
            rem = _reminder_for(conn, task_id)
            if rem and rem["next_reminder_at"]:
                conn.execute("UPDATE todo_reminders SET enabled=1, updated_at=? WHERE task_id=?", (stamp, int(task_id)))
            _log(conn, "task_active", "Marked task active", int(row["list_id"]), int(task_id))
            task = conn.execute("SELECT * FROM todo_tasks WHERE id=?", (int(task_id),)).fetchone()
            return {"status": "ok", "task": _sanitize_task(task, _reminder_for(conn, task_id), _list_for(conn, row["list_id"]))}
    return _call(inner, path)


def _add_months(base, months):
    month = base.month - 1 + months
    year = base.year + month // 12
    month = month % 12 + 1
    days = [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    return base.replace(year=year, month=month, day=min(base.day, days[month - 1]))


def calculate_next_reminder(task, reminder, now=None):
    current = now or datetime.now().replace(microsecond=0)
    unit = str(reminder.get("repeat_unit", "none"))
    interval = int(reminder.get("repeat_interval", 0) or 0)
    if unit == "hours":
        return current + timedelta(hours=max(1, interval))
    if unit == "days":
        return current + timedelta(days=max(1, interval))
    if unit == "weekly":
        return current + timedelta(days=7)
    if unit == "monthly":
        return _add_months(current, 1)
    if unit == "yearly":
        try:
            return current.replace(year=current.year + 1)
        except ValueError:
            return current.replace(year=current.year + 1, day=28)
    return None


def due(path=None):
    def inner():
        current = datetime.now().replace(microsecond=0)
        due_items = []
        stamp = current.isoformat()
        with _connect(path) as conn:
            rows = conn.execute(
                """
                SELECT t.*, l.name AS list_name, l.emoji AS list_emoji, r.enabled, r.next_reminder_at,
                       r.last_reminded_at, r.repeat_unit, r.repeat_interval, r.snoozed_until
                FROM todo_tasks t
                JOIN todo_lists l ON l.id=t.list_id AND l.is_deleted=0
                JOIN todo_reminders r ON r.task_id=t.id
                WHERE t.is_deleted=0 AND t.status='active' AND r.enabled=1
                ORDER BY COALESCE(r.next_reminder_at, t.due_date || 'T' || t.due_time || ':00') ASC, t.id ASC
                """
            ).fetchall()
            for row in rows:
                item = dict(row)
                snoozed_until = str(item.get("snoozed_until") or "")
                if snoozed_until and datetime.fromisoformat(snoozed_until) > current:
                    continue
                due_at_text = str(item.get("next_reminder_at") or "")
                if not due_at_text:
                    due_dt = _task_due_at(item)
                    due_at_text = due_dt.isoformat() if due_dt else ""
                if not due_at_text:
                    continue
                due_at = datetime.fromisoformat(due_at_text)
                if due_at > current:
                    continue
                notification_id = "todo:%d:%s" % (int(item["id"]), due_at.isoformat())
                last_reminded = str(item.get("last_reminded_at") or "")
                if last_reminded != due_at.isoformat():
                    conn.execute(
                        "INSERT INTO todo_notification_log(task_id,notification_id,shown_at,created_at) VALUES(?,?,?,?)",
                        (int(item["id"]), notification_id, stamp, stamp),
                    )
                    conn.execute("UPDATE todo_reminders SET last_reminded_at=?, updated_at=? WHERE task_id=?", (due_at.isoformat(), stamp, int(item["id"])))
                due_items.append({
                    "task_id": int(item["id"]),
                    "id": int(item["id"]),
                    "list_id": int(item["list_id"]),
                    "title": str(item["title"]),
                    "notes": str(item.get("notes") or ""),
                    "list_name": str(item["list_name"]),
                    "list_emoji": str(item["list_emoji"]),
                    "due_at": due_at.isoformat(),
                    "repeat_unit": str(item.get("repeat_unit", "none")),
                    "repeat_interval": int(item.get("repeat_interval", 0) or 0),
                    "notification_id": notification_id,
                })
            return {"status": "ok", "count": len(due_items), "due": due_items, "now": current.isoformat()}
    return _call(inner, path)


def dismiss(task_id, path=None):
    def inner():
        stamp = now_iso()
        with _connect(path) as conn:
            task = conn.execute("SELECT * FROM todo_tasks WHERE id=? AND is_deleted=0", (int(task_id or 0),)).fetchone()
            rem = _reminder_for(conn, task_id)
            if not task or not rem:
                return {"status": "error", "error": "task_not_found"}
            next_at = calculate_next_reminder(dict(task), dict(rem), datetime.now().replace(microsecond=0))
            if next_at:
                conn.execute("UPDATE todo_reminders SET next_reminder_at=?, snoozed_until=NULL, updated_at=? WHERE task_id=?", (next_at.isoformat(), stamp, int(task_id)))
            else:
                conn.execute("UPDATE todo_reminders SET enabled=0, snoozed_until=NULL, updated_at=? WHERE task_id=?", (stamp, int(task_id)))
            conn.execute("UPDATE todo_notification_log SET action_taken='dismissed' WHERE task_id=? AND action_taken IS NULL", (int(task_id),))
            return {"status": "ok", "task_id": int(task_id), "next_reminder_at": next_at.isoformat() if next_at else ""}
    return _call(inner, path)


def snooze(task_id, minutes=10, path=None):
    def inner():
        stamp = now_iso()
        raw_minutes = str(minutes)
        delta = timedelta(days=1) if raw_minutes == "tomorrow" else timedelta(minutes=int(minutes or 10))
        snoozed_until = (datetime.now().replace(microsecond=0) + delta).isoformat()
        with _connect(path) as conn:
            if not conn.execute("SELECT id FROM todo_tasks WHERE id=? AND is_deleted=0", (int(task_id or 0),)).fetchone():
                return {"status": "error", "error": "task_not_found"}
            conn.execute(
                "UPDATE todo_reminders SET snoozed_until=?, next_reminder_at=?, updated_at=? WHERE task_id=?",
                (snoozed_until, snoozed_until, stamp, int(task_id)),
            )
            conn.execute("UPDATE todo_notification_log SET action_taken='snoozed', snoozed_until=? WHERE task_id=? AND action_taken IS NULL", (snoozed_until, int(task_id)))
            return {"status": "ok", "task_id": int(task_id), "snoozed_until": snoozed_until}
    return _call(inner, path)


def settings_stats(path=None):
    def inner():
        target = Path(path) if path else db_path()
        today = date.today().isoformat()
        now_time = datetime.now().strftime("%H:%M")
        with _connect(path) as conn:
            return {
                "status": "ok",
                "schema_version": SCHEMA_VERSION,
                "lists_count": conn.execute("SELECT COUNT(*) AS c FROM todo_lists WHERE is_deleted=0").fetchone()["c"],
                "active_tasks": conn.execute("SELECT COUNT(*) AS c FROM todo_tasks WHERE is_deleted=0 AND status='active'").fetchone()["c"],
                "completed_tasks": conn.execute("SELECT COUNT(*) AS c FROM todo_tasks WHERE is_deleted=0 AND status='completed'").fetchone()["c"],
                "overdue_tasks": conn.execute(
                    "SELECT COUNT(*) AS c FROM todo_tasks WHERE is_deleted=0 AND status='active' AND due_date IS NOT NULL AND due_date!='' AND (due_date < ? OR (due_date=? AND due_time < ?))",
                    (today, today, now_time),
                ).fetchone()["c"],
                "due_today": conn.execute("SELECT COUNT(*) AS c FROM todo_tasks WHERE is_deleted=0 AND status='active' AND due_date=?", (today,)).fetchone()["c"],
                "database_path": str(target),
                "database_size_bytes": target.stat().st_size if target.exists() else 0,
            }
    return _call(inner, path)
