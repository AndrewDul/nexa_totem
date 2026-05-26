"""SQLite-backed local Study / NeXa Learn store."""

from __future__ import annotations

import difflib
import os
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_DB_PATH = Path("var/data/study/nexa_study.db")
SCHEMA_VERSION = 1
DELETE_ALL_CONFIRM = "DELETE_STUDY_DATA"


class ClosingConnection(sqlite3.Connection):
    def __exit__(self, exc_type, exc_value, traceback):
        result = super().__exit__(exc_type, exc_value, traceback)
        self.close()
        return result


def db_path():
    return Path(os.environ.get("NEXA_STUDY_DB_PATH", DEFAULT_DB_PATH))


def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalize_name(value):
    text = str(value or "").strip().lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _connect(path=None):
    target = Path(path) if path is not None else db_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(target, factory=ClosingConnection)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _row(row):
    return dict(row) if row is not None else None


def _rows(rows):
    return [dict(row) for row in rows]


def _safe_int(value, default=0, minimum=None, maximum=None):
    try:
        result = int(value)
    except (TypeError, ValueError):
        result = default
    if minimum is not None:
        result = max(minimum, result)
    if maximum is not None:
        result = min(maximum, result)
    return result


def initialize(path=None):
    with _connect(path) as conn:
        conn.executescript(
            """
            PRAGMA user_version = 1;
            CREATE TABLE IF NOT EXISTS study_topics (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                normalized_name TEXT NOT NULL UNIQUE,
                topic_type TEXT NOT NULL DEFAULT 'pomodoro',
                created_at TEXT NOT NULL,
                last_used_at TEXT
            );
            CREATE TABLE IF NOT EXISTS pomodoro_sessions (
                id INTEGER PRIMARY KEY,
                topic_id INTEGER NOT NULL,
                planned_minutes INTEGER NOT NULL,
                break_minutes INTEGER NOT NULL DEFAULT 0,
                actual_seconds INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'running',
                started_at TEXT NOT NULL,
                finished_at TEXT,
                FOREIGN KEY(topic_id) REFERENCES study_topics(id)
            );
            CREATE TABLE IF NOT EXISTS smart_study_sessions (
                id INTEGER PRIMARY KEY,
                topic TEXT NOT NULL,
                normalized_topic TEXT NOT NULL,
                goal TEXT,
                total_minutes INTEGER NOT NULL,
                break_count INTEGER NOT NULL,
                break_minutes INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'running',
                started_at TEXT NOT NULL,
                finished_at TEXT
            );
            CREATE TABLE IF NOT EXISTS smart_study_notes (
                id INTEGER PRIMARY KEY,
                session_id INTEGER NOT NULL,
                note_text TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS smart_study_segments (
                id INTEGER PRIMARY KEY,
                session_id INTEGER NOT NULL,
                position INTEGER NOT NULL,
                segment_type TEXT NOT NULL,
                planned_minutes INTEGER NOT NULL,
                actual_seconds INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'pending',
                started_at TEXT,
                finished_at TEXT,
                FOREIGN KEY(session_id) REFERENCES smart_study_sessions(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS flashcard_decks (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                normalized_name TEXT NOT NULL UNIQUE,
                description TEXT,
                created_at TEXT NOT NULL,
                last_reviewed_at TEXT
            );
            CREATE TABLE IF NOT EXISTS flashcards (
                id INTEGER PRIMARY KEY,
                deck_id INTEGER NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                normalized_question TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'new',
                correct_count INTEGER NOT NULL DEFAULT 0,
                wrong_count INTEGER NOT NULL DEFAULT 0,
                unsure_count INTEGER NOT NULL DEFAULT 0,
                repeat_count INTEGER NOT NULL DEFAULT 0,
                last_reviewed_at TEXT,
                UNIQUE(deck_id, normalized_question),
                FOREIGN KEY(deck_id) REFERENCES flashcard_decks(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS flashcard_reviews (
                id INTEGER PRIMARY KEY,
                deck_id INTEGER NOT NULL,
                card_id INTEGER NOT NULL,
                question_number INTEGER NOT NULL,
                typed_answer TEXT,
                was_correct INTEGER,
                confidence TEXT NOT NULL,
                revealed_answer INTEGER NOT NULL DEFAULT 0,
                reviewed_at TEXT NOT NULL,
                FOREIGN KEY(deck_id) REFERENCES flashcard_decks(id) ON DELETE CASCADE,
                FOREIGN KEY(card_id) REFERENCES flashcards(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS quiz_sets (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                normalized_name TEXT NOT NULL UNIQUE,
                description TEXT,
                created_at TEXT NOT NULL,
                last_attempt_at TEXT
            );
            CREATE TABLE IF NOT EXISTS quiz_questions (
                id INTEGER PRIMARY KEY,
                quiz_id INTEGER NOT NULL,
                question TEXT NOT NULL,
                normalized_question TEXT NOT NULL,
                answer_a TEXT NOT NULL,
                answer_b TEXT NOT NULL,
                answer_c TEXT NOT NULL,
                answer_d TEXT NOT NULL,
                correct_answer TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'new',
                correct_count INTEGER NOT NULL DEFAULT 0,
                wrong_count INTEGER NOT NULL DEFAULT 0,
                marked_for_review INTEGER NOT NULL DEFAULT 0,
                last_answered_at TEXT,
                UNIQUE(quiz_id, normalized_question),
                FOREIGN KEY(quiz_id) REFERENCES quiz_sets(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS quiz_attempts (
                id INTEGER PRIMARY KEY,
                quiz_id INTEGER NOT NULL,
                score INTEGER NOT NULL,
                total_questions INTEGER NOT NULL,
                started_at TEXT NOT NULL,
                finished_at TEXT NOT NULL,
                FOREIGN KEY(quiz_id) REFERENCES quiz_sets(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS language_lists (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                language TEXT NOT NULL,
                normalized_name TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL,
                last_reviewed_at TEXT
            );
            CREATE TABLE IF NOT EXISTS language_words (
                id INTEGER PRIMARY KEY,
                list_id INTEGER NOT NULL,
                word TEXT NOT NULL,
                normalized_word TEXT NOT NULL,
                pronunciation TEXT,
                meaning TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'new',
                correct_count INTEGER NOT NULL DEFAULT 0,
                wrong_count INTEGER NOT NULL DEFAULT 0,
                last_reviewed_at TEXT,
                UNIQUE(list_id, normalized_word),
                FOREIGN KEY(list_id) REFERENCES language_lists(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS study_notes (
                id INTEGER PRIMARY KEY,
                target_type TEXT NOT NULL,
                target_id INTEGER NOT NULL,
                note_text TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS study_events (
                id INTEGER PRIMARY KEY,
                event_type TEXT NOT NULL,
                target_type TEXT,
                target_id INTEGER,
                summary TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        return {"status": "ok", "schema_version": SCHEMA_VERSION, "db_path": str(Path(path) if path else db_path())}


def _event(conn, event_type, summary, target_type=None, target_id=None):
    conn.execute(
        "INSERT INTO study_events(event_type,target_type,target_id,summary,created_at) VALUES(?,?,?,?,?)",
        (event_type, target_type, target_id, summary, now_iso()),
    )


def _duplicate_or_similar(conn, table, normalized, label, parent_clause="", params=()):
    existing = conn.execute(
        f"SELECT * FROM {table} WHERE normalized_name = ? {parent_clause}", (normalized, *params)
    ).fetchone()
    if existing:
        return {"status": "duplicate", "message": f"You already have this {label}. Open it to continue or make it more specific.", "existing": _row(existing)}
    candidates = conn.execute(f"SELECT * FROM {table} WHERE 1=1 {parent_clause}", params).fetchall()
    similar = []
    for candidate in candidates:
        score = difflib.SequenceMatcher(None, normalized, candidate["normalized_name"]).ratio()
        if score >= 0.82:
            item = dict(candidate)
            item["similarity"] = round(score, 3)
            similar.append(item)
    if similar:
        return {"status": "similar", "message": "A similar item exists. Please make it more specific or continue existing item.", "similar": similar[:5]}
    return None


def _duplicate_question(conn, table, parent_key, parent_id, normalized, label):
    row = conn.execute(
        f"SELECT * FROM {table} WHERE {parent_key} = ? AND normalized_question = ?", (parent_id, normalized)
    ).fetchone()
    if row:
        return {"status": "duplicate", "message": f"You already have this {label}. Open it to continue or make it more specific.", "existing": _row(row)}
    rows = conn.execute(f"SELECT * FROM {table} WHERE {parent_key} = ?", (parent_id,)).fetchall()
    similar = []
    for candidate in rows:
        score = difflib.SequenceMatcher(None, normalized, candidate["normalized_question"]).ratio()
        if score >= 0.82:
            item = dict(candidate)
            item["similarity"] = round(score, 3)
            similar.append(item)
    if similar:
        return {"status": "similar", "message": "A similar item exists. Please make it more specific or continue existing item.", "similar": similar[:5]}
    return None


def _call(fn, *args, **kwargs):
    try:
        initialize(kwargs.pop("path", None))
        return fn(*args, **kwargs)
    except sqlite3.DatabaseError as exc:
        return {"status": "error", "error": "study_database_error", "message": str(exc)}
    except Exception as exc:  # pragma: no cover - API boundary
        return {"status": "error", "error": "study_error", "message": str(exc)}


def overview(path=None):
    return stats(path=path)


def stats(path=None):
    def inner():
        with _connect(path) as conn:
            pomodoro_seconds = conn.execute("SELECT COALESCE(SUM(actual_seconds),0) AS value FROM pomodoro_sessions WHERE status != 'running'").fetchone()["value"]
            running_seconds = 0
            running = conn.execute("SELECT started_at FROM pomodoro_sessions WHERE status='running' ORDER BY id DESC LIMIT 1").fetchone()
            if running:
                started = datetime.fromisoformat(running["started_at"])
                running_seconds = max(0, int((datetime.now(timezone.utc) - started).total_seconds()))
            total_minutes = int((pomodoro_seconds + running_seconds) / 60)
            per_topic = _rows(conn.execute(
                """
                SELECT t.name AS topic, COUNT(s.id) AS sessions,
                       CAST(COALESCE(SUM(CASE WHEN s.status='running' THEN 0 ELSE s.actual_seconds END),0) / 60 AS INTEGER) AS total_minutes,
                       MAX(COALESCE(s.finished_at, s.started_at)) AS last_studied_at
                FROM study_topics t LEFT JOIN pomodoro_sessions s ON s.topic_id = t.id
                GROUP BY t.id ORDER BY last_studied_at DESC
                """
            ))
            payload = {
                "status": "ok",
                "total_study_minutes": total_minutes,
                "total_pomodoro_sessions": conn.execute("SELECT COUNT(*) AS c FROM pomodoro_sessions").fetchone()["c"],
                "total_smart_study_sessions": conn.execute("SELECT COUNT(*) AS c FROM smart_study_sessions").fetchone()["c"],
                "total_flashcard_decks": conn.execute("SELECT COUNT(*) AS c FROM flashcard_decks").fetchone()["c"],
                "total_flashcards": conn.execute("SELECT COUNT(*) AS c FROM flashcards").fetchone()["c"],
                "known_mastered_flashcards": conn.execute("SELECT COUNT(*) AS c FROM flashcards WHERE status IN ('known','mastered')").fetchone()["c"],
                "repeat_unsure_flashcards": conn.execute("SELECT COUNT(*) AS c FROM flashcards WHERE status IN ('repeat','unsure')").fetchone()["c"],
                "total_quiz_sets": conn.execute("SELECT COUNT(*) AS c FROM quiz_sets").fetchone()["c"],
                "total_quiz_questions": conn.execute("SELECT COUNT(*) AS c FROM quiz_questions").fetchone()["c"],
                "wrong_marked_quiz_questions": conn.execute("SELECT COUNT(*) AS c FROM quiz_questions WHERE status='wrong' OR marked_for_review=1").fetchone()["c"],
                "total_language_lists": conn.execute("SELECT COUNT(*) AS c FROM language_lists").fetchone()["c"],
                "total_language_words": conn.execute("SELECT COUNT(*) AS c FROM language_words").fetchone()["c"],
                "mastered_language_words": conn.execute("SELECT COUNT(*) AS c FROM language_words WHERE status='mastered'").fetchone()["c"],
                "per_topic_stats": per_topic,
                "database_path": str(Path(path) if path else db_path()),
                "database_size_bytes": (Path(path) if path else db_path()).stat().st_size if (Path(path) if path else db_path()).exists() else 0,
            }
            return payload
    return _call(inner, path=path)


def history(limit=30, path=None):
    def inner():
        with _connect(path) as conn:
            return {"status": "ok", "events": _rows(conn.execute("SELECT * FROM study_events ORDER BY id DESC LIMIT ?", (_safe_int(limit, 30, 1, 100),)))}
    return _call(inner, path=path)


def timer_status(path=None):
    def inner():
        with _connect(path) as conn:
            row = conn.execute(
                """
                SELECT s.*, t.name AS topic FROM pomodoro_sessions s
                JOIN study_topics t ON t.id=s.topic_id
                WHERE s.status='running' ORDER BY s.id DESC LIMIT 1
                """
            ).fetchone()
            if not row:
                return {"status": "ok", "active": False}
            item = dict(row)
            started = datetime.fromisoformat(item["started_at"])
            elapsed = max(0, int((datetime.now(timezone.utc) - started).total_seconds()))
            planned = int(item["planned_minutes"]) * 60
            remaining = max(0, planned - elapsed)
            if remaining <= 0:
                conn.execute("UPDATE pomodoro_sessions SET status='finished', actual_seconds=?, finished_at=? WHERE id=?", (elapsed, now_iso(), item["id"]))
                _event(conn, "pomodoro_finished", f"Focus time finished: {item['topic']}", "pomodoro", item["id"])
                return {"status": "ok", "active": False, "finished": True, "message": "Focus time finished. Take a break."}
            return {"status": "ok", "active": True, "session": item, "elapsed_seconds": elapsed, "remaining_seconds": remaining, "planned_seconds": planned}
    return _call(inner, path=path)


def start_pomodoro(topic, planned_minutes=25, break_minutes=0, path=None):
    def inner():
        name = str(topic or "").strip()
        normalized = normalize_name(name)
        if not normalized:
            return {"status": "error", "error": "topic_required"}
        with _connect(path) as conn:
            warning = _duplicate_or_similar(conn, "study_topics", normalized, "topic")
            if warning:
                return warning
            stamp = now_iso()
            cur = conn.execute("INSERT INTO study_topics(name,normalized_name,topic_type,created_at,last_used_at) VALUES(?,?,?,?,?)", (name, normalized, "pomodoro", stamp, stamp))
            topic_id = cur.lastrowid
            conn.execute("UPDATE study_topics SET last_used_at=? WHERE id=?", (stamp, topic_id))
            cur = conn.execute(
                "INSERT INTO pomodoro_sessions(topic_id,planned_minutes,break_minutes,started_at) VALUES(?,?,?,?)",
                (topic_id, _safe_int(planned_minutes, 25, 1, 240), _safe_int(break_minutes, 0, 0, 60), stamp),
            )
            _event(conn, "pomodoro_started", f"Started focus: {name}", "pomodoro", cur.lastrowid)
            return {"status": "ok", "session_id": cur.lastrowid, "topic_id": topic_id, "topic": name}
    return _call(inner, path=path)


def stop_timer(path=None):
    def inner():
        with _connect(path) as conn:
            row = conn.execute("SELECT * FROM pomodoro_sessions WHERE status='running' ORDER BY id DESC LIMIT 1").fetchone()
            if not row:
                return {"status": "ok", "active": False}
            started = datetime.fromisoformat(row["started_at"])
            actual = max(0, int((datetime.now(timezone.utc) - started).total_seconds()))
            conn.execute("UPDATE pomodoro_sessions SET status='stopped', actual_seconds=?, finished_at=? WHERE id=?", (actual, now_iso(), row["id"]))
            _event(conn, "pomodoro_stopped", "Stopped focus timer", "pomodoro", row["id"])
            return {"status": "ok", "active": False, "actual_seconds": actual}
    return _call(inner, path=path)


def validate_smart_segments(topic, segments):
    if not normalize_name(topic):
        return {"status": "error", "error": "topic_required", "message": "Session title is required."}
    if not isinstance(segments, list) or not segments:
        return {"status": "error", "error": "segments_required", "message": "Add at least one focus segment."}
    has_focus = False
    previous_type = ""
    for index, raw in enumerate(segments):
        if not isinstance(raw, dict):
            return {"status": "error", "error": "invalid_segment", "message": "Invalid segment."}
        segment_type = str(raw.get("type", raw.get("segment_type", ""))).lower()
        minutes = _safe_int(raw.get("minutes", raw.get("planned_minutes", 0)))
        if segment_type not in {"focus", "break"}:
            return {"status": "error", "error": "invalid_segment_type", "message": "Segment must be focus or break."}
        if previous_type and previous_type == segment_type:
            return {"status": "error", "error": "adjacent_segments", "message": "Segments must alternate focus and break."}
        if segment_type == "focus":
            has_focus = True
            if minutes < 5:
                return {"status": "error", "error": "focus_too_short", "message": "Focus part cannot be shorter than 5 minutes."}
        if segment_type == "break":
            if minutes < 5:
                return {"status": "error", "error": "break_too_short", "message": "Break cannot be shorter than 5 minutes."}
            if index == 0 or index == len(segments) - 1 or previous_type != "focus":
                return {"status": "error", "error": "invalid_break_position", "message": "Break needs focus before and after it."}
            next_type = str(segments[index + 1].get("type", segments[index + 1].get("segment_type", ""))).lower()
            if next_type != "focus":
                return {"status": "error", "error": "invalid_break_position", "message": "Break needs focus before and after it."}
        previous_type = segment_type
    if not has_focus:
        return {"status": "error", "error": "focus_required", "message": "Add at least one focus segment."}
    return {"status": "ok"}


def default_smart_segments(total_minutes=45, break_count=0, break_minutes=5):
    total = _safe_int(total_minutes, 45, 5, 300)
    breaks = _safe_int(break_count, 0, 0, 12)
    break_len = _safe_int(break_minutes, 5, 5, 60)
    if breaks <= 0:
        return [{"type": "focus", "minutes": total}]
    focus_total = total - breaks * break_len
    focus_parts = breaks + 1
    if focus_total < focus_parts * 5:
        return []
    base = int(focus_total / focus_parts)
    remainder = focus_total - base * focus_parts
    result = []
    for index in range(focus_parts):
        result.append({"type": "focus", "minutes": base + (1 if index < remainder else 0)})
        if index < breaks:
            result.append({"type": "break", "minutes": break_len})
    return result


def smart_start(topic, goal="", total_minutes=45, break_count=0, break_minutes=5, segments=None, path=None):
    def inner():
        topic_text = str(topic or "").strip()
        planned_segments = segments if segments is not None else default_smart_segments(total_minutes, break_count, break_minutes)
        validation = validate_smart_segments(topic_text, planned_segments)
        if validation.get("status") != "ok":
            if validation.get("error") == "segments_required":
                validation["message"] = "Session too short for breaks. Minimum is 10 minutes for one 5-minute break between two 5-minute focus parts."
            return validation
        stamp = now_iso()
        with _connect(path) as conn:
            existing = conn.execute("SELECT * FROM smart_study_sessions WHERE normalized_topic=? ORDER BY id DESC LIMIT 1", (normalize_name(topic_text),)).fetchone()
            if existing:
                return {"status": "duplicate", "message": "You already have this topic. Open it to continue or make it more specific.", "existing": _row(existing)}
            cur = conn.execute(
                "INSERT INTO smart_study_sessions(topic,normalized_topic,goal,total_minutes,break_count,break_minutes,started_at) VALUES(?,?,?,?,?,?,?)",
                (topic_text, normalize_name(topic_text), str(goal or ""), sum(_safe_int(s.get("minutes", 0)) for s in planned_segments), sum(1 for s in planned_segments if str(s.get("type")) == "break"), _safe_int(break_minutes, 5, 5, 60), stamp),
            )
            session_id = cur.lastrowid
            for index, segment in enumerate(planned_segments):
                conn.execute(
                    "INSERT INTO smart_study_segments(session_id,position,segment_type,planned_minutes,status,started_at) VALUES(?,?,?,?,?,?)",
                    (session_id, index + 1, str(segment.get("type")), _safe_int(segment.get("minutes"), 5, 5, 300), "running" if index == 0 else "pending", stamp if index == 0 else None),
                )
            _event(conn, "smart_started", f"Started smart study: {topic_text}", "smart", cur.lastrowid)
            return {"status": "ok", "session_id": session_id, "segments": planned_segments}
    return _call(inner, path=path)


def smart_status(path=None):
    def inner():
        with _connect(path) as conn:
            session = conn.execute("SELECT * FROM smart_study_sessions WHERE status='running' ORDER BY id DESC LIMIT 1").fetchone()
            if not session:
                return timer_status(path=path)
            segments = _rows(conn.execute("SELECT * FROM smart_study_segments WHERE session_id=? ORDER BY position", (session["id"],)))
            elapsed = max(0, int((datetime.now(timezone.utc) - datetime.fromisoformat(session["started_at"])).total_seconds()))
            cursor = 0
            active = None
            for segment in segments:
                planned_seconds = int(segment["planned_minutes"]) * 60
                if elapsed < cursor + planned_seconds:
                    active = segment
                    remaining = cursor + planned_seconds - elapsed
                    break
                cursor += planned_seconds
            if active is None:
                conn.execute("UPDATE smart_study_sessions SET status='finished', finished_at=? WHERE id=?", (now_iso(), session["id"]))
                _event(conn, "smart_finished", "Finished smart study session", "smart", session["id"])
                return {"status": "ok", "active": False, "finished": True}
            active_index = int(active["position"]) - 1
            note_pending = active["segment_type"] == "focus" and remaining <= 2
            return {
                "status": "ok",
                "active": True,
                "kind": active["segment_type"],
                "current_segment_type": active["segment_type"],
                "current_segment_index": active_index,
                "note_prompt_pending": note_pending,
                "note_target_segment_id": active["id"] if note_pending else 0,
                "session": _row(session),
                "segment": active,
                "segments": segments,
                "remaining_seconds": remaining,
                "planned_seconds": int(active["planned_minutes"]) * 60,
                "message": "What did you learn?" if note_pending else ("Break time. Rest." if active["segment_type"] == "break" else "Focus time"),
            }
    return _call(inner, path=path)


def smart_note(session_id, note_text, path=None):
    def inner():
        text = str(note_text or "").strip()
        if not text:
            return {"status": "error", "error": "note_required"}
        with _connect(path) as conn:
            cur = conn.execute("INSERT INTO smart_study_notes(session_id,note_text,created_at) VALUES(?,?,?)", (_safe_int(session_id), text, now_iso()))
            _event(conn, "smart_note", text[:80], "smart_note", cur.lastrowid)
            return {"status": "ok", "note_id": cur.lastrowid}
    return _call(inner, path=path)


def smart_finish(session_id, path=None):
    def inner():
        with _connect(path) as conn:
            conn.execute("UPDATE smart_study_sessions SET status='finished', finished_at=? WHERE id=?", (now_iso(), _safe_int(session_id)))
            _event(conn, "smart_finished", "Finished smart study session", "smart", _safe_int(session_id))
            return {"status": "ok"}
    return _call(inner, path=path)


def smart_stop(session_id=0, path=None):
    def inner():
        with _connect(path) as conn:
            target_id = _safe_int(session_id)
            if target_id <= 0:
                row = conn.execute("SELECT id FROM smart_study_sessions WHERE status='running' ORDER BY id DESC LIMIT 1").fetchone()
                target_id = int(row["id"]) if row else 0
            if target_id <= 0:
                return {"status": "ok", "active": False}
            conn.execute("UPDATE smart_study_sessions SET status='stopped', finished_at=? WHERE id=?", (now_iso(), target_id))
            _event(conn, "smart_stopped", "Stopped smart study session", "smart", target_id)
            return {"status": "ok", "active": False}
    return _call(inner, path=path)


def smart_skip_note(session_id, path=None):
    def inner():
        with _connect(path) as conn:
            _event(conn, "smart_note_skipped", "Skipped focus note", "smart", _safe_int(session_id))
            return {"status": "ok", "skipped": True}
    return _call(inner, path=path)


def create_deck(name, description="", path=None):
    return _create_named("flashcard_decks", "deck", name, description, path)


def create_quiz(name, description="", path=None):
    return _create_named("quiz_sets", "quiz", name, description, path)


def create_language_list(name, language="English", path=None):
    def inner():
        normalized = normalize_name(name)
        if not normalized:
            return {"status": "error", "error": "name_required"}
        with _connect(path) as conn:
            warning = _duplicate_or_similar(conn, "language_lists", normalized, "language list")
            if warning:
                return warning
            cur = conn.execute("INSERT INTO language_lists(name,language,normalized_name,created_at) VALUES(?,?,?,?)", (str(name).strip(), str(language or "English"), normalized, now_iso()))
            _event(conn, "language_list_created", f"Created language list: {name}", "language_list", cur.lastrowid)
            return {"status": "ok", "list": _row(conn.execute("SELECT * FROM language_lists WHERE id=?", (cur.lastrowid,)).fetchone())}
    return _call(inner, path=path)


def _create_named(table, label, name, description="", path=None):
    def inner():
        normalized = normalize_name(name)
        if not normalized:
            return {"status": "error", "error": "name_required"}
        with _connect(path) as conn:
            warning = _duplicate_or_similar(conn, table, normalized, label)
            if warning:
                return warning
            cur = conn.execute(f"INSERT INTO {table}(name,normalized_name,description,created_at) VALUES(?,?,?,?)", (str(name).strip(), normalized, str(description or ""), now_iso()))
            _event(conn, f"{label}_created", f"Created {label}: {name}", label, cur.lastrowid)
            return {"status": "ok", label: _row(conn.execute(f"SELECT * FROM {table} WHERE id=?", (cur.lastrowid,)).fetchone())}
    return _call(inner, path=path)


def decks(path=None):
    def inner():
        with _connect(path) as conn:
            return {"status": "ok", "decks": _rows(conn.execute(
                """
                SELECT d.*, COUNT(c.id) AS card_count,
                       SUM(CASE WHEN c.status IN ('known','mastered') THEN 1 ELSE 0 END) AS known_count,
                       SUM(CASE WHEN c.status IN ('repeat','unsure') THEN 1 ELSE 0 END) AS repeat_count
                FROM flashcard_decks d LEFT JOIN flashcards c ON c.deck_id=d.id
                GROUP BY d.id ORDER BY d.last_reviewed_at DESC, d.id DESC
                """
            ))}
    return _call(inner, path=path)


def deck_detail(deck_id, path=None):
    def inner():
        with _connect(path) as conn:
            deck = conn.execute("SELECT * FROM flashcard_decks WHERE id=?", (_safe_int(deck_id),)).fetchone()
            cards = _rows(conn.execute("SELECT *, ROW_NUMBER() OVER (ORDER BY id) AS question_number FROM flashcards WHERE deck_id=? ORDER BY id", (_safe_int(deck_id),)))
            return {"status": "ok", "deck": _row(deck), "cards": cards}
    return _call(inner, path=path)


def quizzes(path=None):
    def inner():
        with _connect(path) as conn:
            return {"status": "ok", "quizzes": _rows(conn.execute(
                """
                SELECT q.*, COUNT(qq.id) AS question_count,
                       SUM(CASE WHEN qq.status='wrong' OR qq.marked_for_review=1 THEN 1 ELSE 0 END) AS wrong_marked_count
                FROM quiz_sets q LEFT JOIN quiz_questions qq ON qq.quiz_id=q.id
                GROUP BY q.id ORDER BY q.last_attempt_at DESC, q.id DESC
                """
            ))}
    return _call(inner, path=path)


def quiz_detail(quiz_id, path=None):
    def inner():
        with _connect(path) as conn:
            quiz = conn.execute("SELECT * FROM quiz_sets WHERE id=?", (_safe_int(quiz_id),)).fetchone()
            questions = _rows(conn.execute("SELECT *, ROW_NUMBER() OVER (ORDER BY id) AS question_number FROM quiz_questions WHERE quiz_id=? ORDER BY id", (_safe_int(quiz_id),)))
            return {"status": "ok", "quiz": _row(quiz), "questions": questions}
    return _call(inner, path=path)


def language_lists(path=None):
    def inner():
        with _connect(path) as conn:
            return {"status": "ok", "lists": _rows(conn.execute(
                """
                SELECT l.*, COUNT(w.id) AS word_count,
                       SUM(CASE WHEN w.status='mastered' THEN 1 ELSE 0 END) AS mastered_count
                FROM language_lists l LEFT JOIN language_words w ON w.list_id=l.id
                GROUP BY l.id ORDER BY l.last_reviewed_at DESC, l.id DESC
                """
            ))}
    return _call(inner, path=path)


def language_list_detail(list_id, path=None):
    def inner():
        with _connect(path) as conn:
            language_list = conn.execute("SELECT * FROM language_lists WHERE id=?", (_safe_int(list_id),)).fetchone()
            words = _rows(conn.execute("SELECT *, ROW_NUMBER() OVER (ORDER BY id) AS question_number FROM language_words WHERE list_id=? ORDER BY id", (_safe_int(list_id),)))
            return {"status": "ok", "list": _row(language_list), "words": words}
    return _call(inner, path=path)


def add_card(deck_id, question, answer, path=None):
    def inner():
        normalized = normalize_name(question)
        if not normalized or not str(answer or "").strip():
            return {"status": "error", "error": "question_answer_required"}
        with _connect(path) as conn:
            warning = _duplicate_question(conn, "flashcards", "deck_id", _safe_int(deck_id), normalized, "card")
            if warning:
                return warning
            cur = conn.execute("INSERT INTO flashcards(deck_id,question,answer,normalized_question) VALUES(?,?,?,?)", (_safe_int(deck_id), str(question).strip(), str(answer).strip(), normalized))
            _event(conn, "flashcard_created", f"Added flashcard: {question}", "flashcard", cur.lastrowid)
            return {"status": "ok", "card": _row(conn.execute("SELECT * FROM flashcards WHERE id=?", (cur.lastrowid,)).fetchone())}
    return _call(inner, path=path)


def update_card(card_id, question=None, answer=None, path=None):
    def inner():
        with _connect(path) as conn:
            row = conn.execute("SELECT * FROM flashcards WHERE id=?", (_safe_int(card_id),)).fetchone()
            if not row:
                return {"status": "error", "error": "card_not_found"}
            next_question = str(question if question is not None else row["question"]).strip()
            next_answer = str(answer if answer is not None else row["answer"]).strip()
            if not next_question or not next_answer:
                return {"status": "error", "error": "question_answer_required"}
            conn.execute("UPDATE flashcards SET question=?, answer=?, normalized_question=? WHERE id=?", (next_question, next_answer, normalize_name(next_question), row["id"]))
            _event(conn, "flashcard_updated", f"Updated flashcard: {next_question}", "flashcard", row["id"])
            return {"status": "ok", "card": _row(conn.execute("SELECT * FROM flashcards WHERE id=?", (row["id"],)).fetchone())}
    return _call(inner, path=path)


def delete_card(card_id, path=None):
    def inner():
        with _connect(path) as conn:
            conn.execute("DELETE FROM flashcards WHERE id=?", (_safe_int(card_id),))
            _event(conn, "flashcard_deleted", "Deleted flashcard", "flashcard", _safe_int(card_id))
            return {"status": "ok"}
    return _call(inner, path=path)


def start_flashcard_review(deck_id, mode="all", path=None):
    payload = next_card(deck_id, mode, path=path)
    if payload.get("status") == "ok":
        payload["session_id"] = _safe_int(deck_id)
    return payload


def next_card(deck_id, mode="all", path=None):
    def inner():
        where = "deck_id=?"
        params = [_safe_int(deck_id)]
        if mode in {"repeat", "unsure"}:
            where += " AND status=?"
            params.append(mode)
        with _connect(path) as conn:
            row = conn.execute(f"SELECT *, ROW_NUMBER() OVER (ORDER BY id) AS question_number FROM flashcards WHERE {where} ORDER BY CASE status WHEN 'repeat' THEN 0 WHEN 'unsure' THEN 1 WHEN 'new' THEN 2 WHEN 'known' THEN 3 ELSE 4 END, last_reviewed_at IS NOT NULL, last_reviewed_at, id LIMIT 1", params).fetchone()
            return {"status": "ok", "card": _row(row)}
    return _call(inner, path=path)


def review_card(card_id, result=None, typed_answer="", confidence=None, revealed_answer=False, path=None):
    def inner():
        confidence_value = str(confidence or result or "dont_know")
        if confidence_value == "know":
            review_result = "known"
        elif confidence_value == "unsure":
            review_result = "unsure"
        else:
            review_result = "repeat"
        stamp = now_iso()
        with _connect(path) as conn:
            row = conn.execute("SELECT * FROM flashcards WHERE id=?", (_safe_int(card_id),)).fetchone()
            if not row:
                return {"status": "error", "error": "card_not_found"}
            typed = str(typed_answer or "").strip()
            was_correct = None
            if typed:
                was_correct = normalize_name(typed) == normalize_name(row["answer"])
            if confidence_value == "know" and not typed and not revealed_answer:
                return {"status": "error", "error": "answer_or_reveal_required", "message": "Type your answer or reveal the card first."}
            correct = int(row["correct_count"]) + (1 if review_result == "known" else 0)
            status = "mastered" if correct >= 50 else review_result
            conn.execute(
                "UPDATE flashcards SET status=?, correct_count=?, wrong_count=wrong_count+?, unsure_count=unsure_count+?, repeat_count=repeat_count+?, last_reviewed_at=? WHERE id=?",
                (status, correct, 1 if review_result == "repeat" else 0, 1 if review_result == "unsure" else 0, 1 if review_result == "repeat" else 0, stamp, row["id"]),
            )
            question_number = conn.execute("SELECT COUNT(*) AS c FROM flashcards WHERE deck_id=? AND id<=?", (row["deck_id"], row["id"])).fetchone()["c"]
            conn.execute(
                "INSERT INTO flashcard_reviews(deck_id,card_id,question_number,typed_answer,was_correct,confidence,revealed_answer,reviewed_at) VALUES(?,?,?,?,?,?,?,?)",
                (row["deck_id"], row["id"], question_number, typed, None if was_correct is None else int(was_correct), confidence_value, int(bool(revealed_answer)), stamp),
            )
            conn.execute("UPDATE flashcard_decks SET last_reviewed_at=? WHERE id=?", (stamp, row["deck_id"]))
            _event(conn, "flashcard_reviewed", f"Flashcard reviewed: {status}", "flashcard", row["id"])
            return {"status": "ok", "was_correct": was_correct, "correct_answer": row["answer"], "card": _row(conn.execute("SELECT * FROM flashcards WHERE id=?", (row["id"],)).fetchone())}
    return _call(inner, path=path)


def add_quiz_question(quiz_id, question, a, b, c, d, correct_answer, path=None):
    def inner():
        normalized = normalize_name(question)
        correct = str(correct_answer or "").upper()
        if correct not in {"A", "B", "C", "D"} or not normalized:
            return {"status": "error", "error": "invalid_question"}
        with _connect(path) as conn:
            warning = _duplicate_question(conn, "quiz_questions", "quiz_id", _safe_int(quiz_id), normalized, "quiz question")
            if warning:
                return warning
            cur = conn.execute(
                "INSERT INTO quiz_questions(quiz_id,question,normalized_question,answer_a,answer_b,answer_c,answer_d,correct_answer) VALUES(?,?,?,?,?,?,?,?)",
                (_safe_int(quiz_id), str(question).strip(), normalized, str(a), str(b), str(c), str(d), correct),
            )
            _event(conn, "quiz_question_created", f"Added quiz question: {question}", "quiz_question", cur.lastrowid)
            return {"status": "ok", "question": _row(conn.execute("SELECT * FROM quiz_questions WHERE id=?", (cur.lastrowid,)).fetchone())}
    return _call(inner, path=path)


def update_quiz_question(question_id, question=None, a=None, b=None, c=None, d=None, correct_answer=None, path=None):
    def inner():
        with _connect(path) as conn:
            row = conn.execute("SELECT * FROM quiz_questions WHERE id=?", (_safe_int(question_id),)).fetchone()
            if not row:
                return {"status": "error", "error": "question_not_found"}
            next_question = str(question if question is not None else row["question"]).strip()
            next_a = str(a if a is not None else row["answer_a"]).strip()
            next_b = str(b if b is not None else row["answer_b"]).strip()
            next_c = str(c if c is not None else row["answer_c"]).strip()
            next_d = str(d if d is not None else row["answer_d"]).strip()
            next_correct = str(correct_answer if correct_answer is not None else row["correct_answer"]).upper()
            if not next_question or next_correct not in {"A", "B", "C", "D"}:
                return {"status": "error", "error": "invalid_question"}
            conn.execute(
                "UPDATE quiz_questions SET question=?, normalized_question=?, answer_a=?, answer_b=?, answer_c=?, answer_d=?, correct_answer=? WHERE id=?",
                (next_question, normalize_name(next_question), next_a, next_b, next_c, next_d, next_correct, row["id"]),
            )
            _event(conn, "quiz_question_updated", f"Updated quiz question: {next_question}", "quiz_question", row["id"])
            return {"status": "ok", "question": _row(conn.execute("SELECT * FROM quiz_questions WHERE id=?", (row["id"],)).fetchone())}
    return _call(inner, path=path)


def delete_quiz_question(question_id, path=None):
    def inner():
        with _connect(path) as conn:
            conn.execute("DELETE FROM quiz_questions WHERE id=?", (_safe_int(question_id),))
            _event(conn, "quiz_question_deleted", "Deleted quiz question", "quiz_question", _safe_int(question_id))
            return {"status": "ok"}
    return _call(inner, path=path)


def start_quiz_attempt(quiz_id, mode="all", path=None):
    payload = next_quiz_question(quiz_id, mode, path=path)
    if payload.get("status") == "ok":
        payload["attempt_id"] = _safe_int(quiz_id)
    return payload


def next_quiz_question(quiz_id, mode="all", path=None):
    def inner():
        where = "quiz_id=?"
        params = [_safe_int(quiz_id)]
        if mode == "wrong":
            where += " AND status='wrong'"
        elif mode == "marked":
            where += " AND marked_for_review=1"
        with _connect(path) as conn:
            row = conn.execute(f"SELECT * FROM quiz_questions WHERE {where} ORDER BY last_answered_at IS NOT NULL, last_answered_at, id LIMIT 1", params).fetchone()
            return {"status": "ok", "question": _row(row)}
    return _call(inner, path=path)


def answer_quiz_question(question_id, answer, marked=False, path=None):
    def inner():
        chosen = str(answer or "").upper()
        if chosen not in {"A", "B", "C", "D"}:
            return {"status": "error", "error": "invalid_answer"}
        stamp = now_iso()
        with _connect(path) as conn:
            row = conn.execute("SELECT * FROM quiz_questions WHERE id=?", (_safe_int(question_id),)).fetchone()
            if not row:
                return {"status": "error", "error": "question_not_found"}
            correct = chosen == row["correct_answer"]
            status = "correct" if correct else "wrong"
            conn.execute(
                "UPDATE quiz_questions SET status=?, correct_count=correct_count+?, wrong_count=wrong_count+?, marked_for_review=?, last_answered_at=? WHERE id=?",
                (status, 1 if correct else 0, 0 if correct else 1, 1 if marked else int(row["marked_for_review"]), stamp, row["id"]),
            )
            conn.execute("UPDATE quiz_sets SET last_attempt_at=? WHERE id=?", (stamp, row["quiz_id"]))
            conn.execute("INSERT INTO quiz_attempts(quiz_id,score,total_questions,started_at,finished_at) VALUES(?,?,?,?,?)", (row["quiz_id"], 1 if correct else 0, 1, stamp, stamp))
            _event(conn, "quiz_answered", f"Quiz answer: {status}", "quiz_question", row["id"])
            correct_key = "answer_" + str(row["correct_answer"]).lower()
            selected_key = "answer_" + chosen.lower()
            return {
                "status": "ok",
                "correct": correct,
                "correct_answer": row["correct_answer"],
                "correct_answer_text": row[correct_key],
                "selected_answer": chosen,
                "selected_answer_text": row[selected_key],
                "message": "Correct" if correct else f"Wrong. Correct answer: {row['correct_answer']}. {row[correct_key]}",
                "question": _row(conn.execute("SELECT * FROM quiz_questions WHERE id=?", (row["id"],)).fetchone()),
            }
    return _call(inner, path=path)


def mark_quiz_question(question_id, path=None):
    def inner():
        with _connect(path) as conn:
            row = conn.execute("SELECT * FROM quiz_questions WHERE id=?", (_safe_int(question_id),)).fetchone()
            if not row:
                return {"status": "error", "error": "question_not_found"}
            next_marked = 0 if int(row["marked_for_review"]) else 1
            conn.execute("UPDATE quiz_questions SET marked_for_review=? WHERE id=?", (next_marked, row["id"]))
            _event(conn, "quiz_marked", "Marked quiz question for review" if next_marked else "Unmarked quiz question", "quiz_question", row["id"])
            return {"status": "ok", "marked_for_review": bool(next_marked), "question": _row(conn.execute("SELECT * FROM quiz_questions WHERE id=?", (row["id"],)).fetchone())}
    return _call(inner, path=path)


def finish_quiz_attempt(quiz_id, score=0, total_questions=0, path=None):
    def inner():
        stamp = now_iso()
        with _connect(path) as conn:
            total = _safe_int(total_questions)
            if total <= 0:
                total = conn.execute("SELECT COUNT(*) AS c FROM quiz_questions WHERE quiz_id=?", (_safe_int(quiz_id),)).fetchone()["c"]
            cur = conn.execute(
                "INSERT INTO quiz_attempts(quiz_id,score,total_questions,started_at,finished_at) VALUES(?,?,?,?,?)",
                (_safe_int(quiz_id), _safe_int(score), total, stamp, stamp),
            )
            conn.execute("UPDATE quiz_sets SET last_attempt_at=? WHERE id=?", (stamp, _safe_int(quiz_id)))
            _event(conn, "quiz_finished", f"Finished quiz: {_safe_int(score)} / {total}", "quiz_attempt", cur.lastrowid)
            return {"status": "ok", "attempt_id": cur.lastrowid}
    return _call(inner, path=path)


def add_language_word(list_id, word, meaning, pronunciation="", path=None):
    def inner():
        normalized = normalize_name(word)
        if not normalized or not str(meaning or "").strip():
            return {"status": "error", "error": "word_meaning_required"}
        with _connect(path) as conn:
            existing = conn.execute("SELECT * FROM language_words WHERE list_id=? AND normalized_word=?", (_safe_int(list_id), normalized)).fetchone()
            if existing:
                return {"status": "duplicate", "message": "You already have this word. Open it to continue or make it more specific.", "existing": _row(existing)}
            cur = conn.execute("INSERT INTO language_words(list_id,word,normalized_word,pronunciation,meaning) VALUES(?,?,?,?,?)", (_safe_int(list_id), str(word).strip(), normalized, str(pronunciation or ""), str(meaning).strip()))
            _event(conn, "language_word_created", f"Added word: {word}", "language_word", cur.lastrowid)
            return {"status": "ok", "word": _row(conn.execute("SELECT * FROM language_words WHERE id=?", (cur.lastrowid,)).fetchone())}
    return _call(inner, path=path)


def delete_language_word(word_id, path=None):
    def inner():
        with _connect(path) as conn:
            conn.execute("DELETE FROM language_words WHERE id=?", (_safe_int(word_id),))
            _event(conn, "language_word_deleted", "Deleted language word", "language_word", _safe_int(word_id))
            return {"status": "ok"}
    return _call(inner, path=path)


def next_language_word(list_id, mode="all", path=None):
    def inner():
        where = "list_id=?"
        params = [_safe_int(list_id)]
        if mode in {"weak", "mastered"}:
            where += " AND status=?"
            params.append(mode)
        with _connect(path) as conn:
            row = conn.execute(f"SELECT * FROM language_words WHERE {where} ORDER BY CASE status WHEN 'mastered' THEN 1 ELSE 0 END, last_reviewed_at IS NOT NULL, last_reviewed_at, id LIMIT 1", params).fetchone()
            return {"status": "ok", "word": _row(row)}
    return _call(inner, path=path)


def review_language_word(word_id, result, path=None):
    def inner():
        correct = result == "correct"
        stamp = now_iso()
        with _connect(path) as conn:
            row = conn.execute("SELECT * FROM language_words WHERE id=?", (_safe_int(word_id),)).fetchone()
            if not row:
                return {"status": "error", "error": "word_not_found"}
            correct_count = int(row["correct_count"]) + (1 if correct else 0)
            wrong_count = int(row["wrong_count"]) + (0 if correct else 1)
            status = "mastered" if correct_count >= 50 else ("weak" if wrong_count > correct_count and wrong_count >= 3 else ("strong" if correct_count >= 10 else "learning"))
            conn.execute("UPDATE language_words SET status=?, correct_count=?, wrong_count=?, last_reviewed_at=? WHERE id=?", (status, correct_count, wrong_count, stamp, row["id"]))
            conn.execute("UPDATE language_lists SET last_reviewed_at=? WHERE id=?", (stamp, row["list_id"]))
            _event(conn, "language_reviewed", f"Language word reviewed: {status}", "language_word", row["id"])
            return {"status": "ok", "word": _row(conn.execute("SELECT * FROM language_words WHERE id=?", (row["id"],)).fetchone())}
    return _call(inner, path=path)


def create_note(target_type, target_id, note_text, path=None):
    def inner():
        text = str(note_text or "").strip()
        if not text:
            return {"status": "error", "error": "note_required"}
        with _connect(path) as conn:
            cur = conn.execute("INSERT INTO study_notes(target_type,target_id,note_text,created_at) VALUES(?,?,?,?)", (str(target_type or "study"), _safe_int(target_id), text, now_iso()))
            _event(conn, "note_created", text[:80], "study_note", cur.lastrowid)
            return {"status": "ok", "note_id": cur.lastrowid}
    return _call(inner, path=path)


def notes(path=None):
    def inner():
        with _connect(path) as conn:
            return {"status": "ok", "notes": _rows(conn.execute("SELECT * FROM study_notes ORDER BY id DESC LIMIT 100"))}
    return _call(inner, path=path)


def settings_stats(path=None):
    payload = stats(path=path)
    if payload.get("status") == "ok":
        payload["schema_version"] = SCHEMA_VERSION
    return payload


def delete_action(action, confirm_text="", target_id=None, path=None):
    def inner():
        with _connect(path) as conn:
            if action == "delete_all_study_data":
                if confirm_text != DELETE_ALL_CONFIRM:
                    return {"status": "error", "error": "confirmation_required"}
                for table in ["study_events", "study_notes", "smart_study_notes", "smart_study_segments", "smart_study_sessions", "pomodoro_sessions", "study_topics", "flashcard_reviews", "flashcards", "flashcard_decks", "quiz_attempts", "quiz_questions", "quiz_sets", "language_words", "language_lists"]:
                    conn.execute(f"DELETE FROM {table}")
                return {"status": "ok", "deleted": "all"}
            required = {
                "delete_deck": ("DELETE_DECK", "flashcard_decks"),
                "delete_quiz": ("DELETE_QUIZ", "quiz_sets"),
                "delete_language_list": ("DELETE_LANGUAGE_LIST", "language_lists"),
            }
            if action in required:
                expected, table = required[action]
                if confirm_text != expected:
                    return {"status": "error", "error": "confirmation_required"}
                conn.execute(f"DELETE FROM {table} WHERE id=?", (_safe_int(target_id),))
                return {"status": "ok", "deleted": action}
            if action == "delete_old_sessions":
                conn.execute("DELETE FROM pomodoro_sessions WHERE status != 'running'")
                return {"status": "ok", "deleted": action}
            return {"status": "error", "error": "unknown_delete_action"}
    return _call(inner, path=path)
