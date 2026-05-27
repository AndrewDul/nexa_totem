"""Localhost-only live diagnostics API for NeXa ToTem."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from system.services.diagnostics.camera_preview import CameraPreviewWorker
from system.services.diagnostics.job_runner import (
    start_audio_check,
    start_benchmarks,
    start_camera_check,
    start_report,
)
from system.services.diagnostics.live_collectors import (
    audio_data,
    camera_data,
    control_center_data,
    logs_data,
    network_data,
    overview_data,
    process_data,
    reports_data,
    system_data,
)
from system.services.diagnostics.live_state import LiveState, ensure_runtime_dirs
from system.services.settings import settings_store
from system.services.study import study_store
from system.services.reminders import reminders_store
from system.services.calendar import calendar_store
from system.services.todo import todo_store
from system.services.hardware_gateway import latest_hardware_state
from system.services.hardware_gateway.hardware_dashboard import render_dashboard


HOST = "127.0.0.1"
PORT = 8769
STATE = LiveState()
PREVIEW = CameraPreviewWorker(STATE)

TTL_SECONDS = {
    "overview": 2,
    "system": 2,
    "processes": 1,
    "audio": 5,
    "camera": 5,
    "network": 8,
    "logs": 5,
    "reports": 10,
    "control-center": 2,
}


def cached(state, key, ttl, collector):
    value = state.cache.get(key, ttl)
    if value is not None:
        return value
    return state.cache.set(key, collector())


def _preview_for(state):
    return PREVIEW if state is STATE else CameraPreviewWorker(state)


def preview_status(state=STATE):
    return _preview_for(state).status()


def start_preview(state=STATE):
    return _preview_for(state).start()


def stop_preview(state=STATE):
    return _preview_for(state).stop()


class DiagnosticsHandler(BaseHTTPRequestHandler):
    server_version = "NeXaDiagnosticsAPI/0.1"

    def log_message(self, format, *args):  # noqa: A002
        return

    def _json(self, payload, status=200):
        body = json.dumps(payload, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _html(self, body_text, status=200):
        body = body_text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _body_json(self):
        length = int(self.headers.get("Content-Length", "0") or "0")
        if not length:
            return {}
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {}

    def _body_json_checked(self):
        length = int(self.headers.get("Content-Length", "0") or "0")
        if not length:
            return {}, True
        try:
            data = json.loads(self.rfile.read(length).decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {}, False
        return (data if isinstance(data, dict) else {}), isinstance(data, dict)

    def do_GET(self):  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        try:
            if path == "/health":
                self._json({"status": "ok", "host": HOST, "port": PORT})
            elif path == "/hardware-dashboard":
                self._html(render_dashboard(latest_hardware_state.as_dict()))
            elif path == "/api/hardware/state":
                self._json({"status": "ok", "state": latest_hardware_state.as_dict()})
            elif path == "/api/study/overview":
                self._json(study_store.overview())
            elif path == "/api/study/stats":
                self._json(study_store.stats())
            elif path == "/api/study/history":
                self._json(study_store.history())
            elif path == "/api/study/timer/status":
                self._json(study_store.timer_status())
            elif path == "/api/study/smart/status":
                self._json(study_store.smart_status())
            elif path == "/api/study/flashcards/decks":
                self._json(study_store.decks())
            elif path == "/api/study/flashcards/deck":
                self._json(study_store.deck_detail(_query_int(query, "deck_id")))
            elif path == "/api/study/flashcards/review/start":
                self._json(study_store.start_flashcard_review(_query_int(query, "deck_id"), _query_str(query, "mode", "all")))
            elif path == "/api/study/flashcards/review/next":
                deck_id = _query_int(query, "deck_id") or _query_int(query, "session_id")
                self._json(study_store.next_card(deck_id, _query_str(query, "mode", "all")))
            elif path == "/api/study/quizzes":
                self._json(study_store.quizzes())
            elif path == "/api/study/quizzes/quiz":
                self._json(study_store.quiz_detail(_query_int(query, "quiz_id")))
            elif path == "/api/study/quizzes/question/next":
                self._json(study_store.next_quiz_question(_query_int(query, "quiz_id"), _query_str(query, "mode", "all")))
            elif path == "/api/study/languages/lists":
                self._json(study_store.language_lists())
            elif path == "/api/study/languages/list":
                self._json(study_store.language_list_detail(_query_int(query, "list_id")))
            elif path == "/api/study/languages/word/next":
                self._json(study_store.next_language_word(_query_int(query, "list_id"), _query_str(query, "mode", "all")))
            elif path == "/api/study/languages/practice/next":
                self._json(study_store.next_language_word(_query_int(query, "list_id"), _query_str(query, "mode", "all")))
            elif path == "/api/study/notes":
                self._json(study_store.notes())
            elif path == "/api/study/settings/stats":
                self._json(study_store.settings_stats())
            elif path == "/api/reminders/overview":
                self._json(reminders_store.overview())
            elif path == "/api/reminders/list":
                self._json(reminders_store.list_reminders())
            elif path == "/api/reminders/due":
                self._json(reminders_store.due())
            elif path == "/api/reminders/settings/stats":
                self._json(reminders_store.settings_stats())
            elif path == "/api/calendar/month":
                self._json(calendar_store.month(_query_int(query, "year"), _query_int(query, "month"), _query_str(query, "selected_date", "")))
            elif path == "/api/calendar/day":
                self._json(calendar_store.day(_query_str(query, "date", "")))
            elif path == "/api/calendar/due":
                self._json(calendar_store.due())
            elif path == "/api/calendar/settings/stats":
                self._json(calendar_store.settings_stats())
            elif path == "/api/todo/overview":
                self._json(todo_store.overview())
            elif path == "/api/todo/lists":
                self._json(todo_store.lists())
            elif path == "/api/todo/tasks":
                self._json(todo_store.tasks(_query_int(query, "list_id")))
            elif path == "/api/todo/due":
                self._json(todo_store.due())
            elif path == "/api/todo/settings/stats":
                self._json(todo_store.settings_stats())
            elif path == "/api/overview":
                self._json(cached(STATE, "overview", TTL_SECONDS["overview"], lambda: overview_data(STATE)))
            elif path == "/api/system":
                self._json(cached(STATE, "system", TTL_SECONDS["system"], system_data))
            elif path == "/api/processes":
                self._json(cached(STATE, "processes", TTL_SECONDS["processes"], process_data))
            elif path == "/api/audio":
                self._json(cached(STATE, "audio", TTL_SECONDS["audio"], audio_data))
            elif path == "/api/camera":
                self._json(cached(STATE, "camera", TTL_SECONDS["camera"], lambda: camera_data(STATE)))
            elif path == "/api/network":
                self._json(cached(STATE, "network", TTL_SECONDS["network"], lambda: network_data(STATE)))
            elif path == "/api/logs":
                self._json(cached(STATE, "logs", TTL_SECONDS["logs"], logs_data))
            elif path == "/api/reports":
                self._json(cached(STATE, "reports", TTL_SECONDS["reports"], reports_data))
            elif path == "/api/control-center":
                self._json(cached(STATE, "control-center", TTL_SECONDS["control-center"], lambda: control_center_data(STATE)))
            elif path == "/api/settings":
                self._json({"status": "ok", "settings": settings_store.get_settings()})
            elif path == "/api/privacy/status":
                self._json(settings_store.privacy_status())
            elif path == "/api/benchmarks/status":
                self._json(STATE.get_job("benchmarks"))
            elif path == "/api/reports/status":
                self._json(STATE.get_job("reports"))
            elif path == "/api/camera/preview/status":
                self._json(preview_status(STATE))
            elif path == "/api/camera/preview/frame":
                self._frame()
            else:
                self._json({"status": "error", "error": "not_found"}, status=404)
        except Exception as exc:  # pragma: no cover - defensive API boundary
            self._json({"status": "error", "error": str(exc)}, status=500)

    def _frame(self):
        body = PREVIEW.latest_frame_bytes()
        if not body:
            self._json({"status": "pending", "message": "No frame available"}, status=404)
            return
        self.send_response(200)
        self.send_header("Content-Type", "image/jpeg")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):  # noqa: N802
        path = urlparse(self.path).path
        if path == "/api/hardware":
            data, valid = self._body_json_checked()
            if not valid:
                self._json({"status": "error", "error": "invalid_json"}, status=400)
                return
            state = latest_hardware_state.update(data)
            self._json({"status": "ok", "connected": bool(state.get("connected", False)), "received": True})
            return
        data = self._body_json()
        if path == "/api/study/pomodoro/start":
            self._json(study_store.start_pomodoro(data.get("topic", ""), data.get("planned_minutes", 25), data.get("break_minutes", 0)))
        elif path == "/api/study/timer/stop":
            self._json(study_store.stop_timer())
        elif path == "/api/study/smart/start":
            self._json(study_store.smart_start(data.get("topic", ""), data.get("goal", ""), data.get("total_minutes", 45), data.get("break_count", 0), data.get("break_minutes", 5), data.get("segments")))
        elif path == "/api/study/smart/note":
            self._json(study_store.smart_note(data.get("session_id", 0), data.get("note_text", "")))
        elif path == "/api/study/smart/skip-note":
            self._json(study_store.smart_skip_note(data.get("session_id", 0)))
        elif path == "/api/study/smart/finish":
            self._json(study_store.smart_finish(data.get("session_id", 0)))
        elif path == "/api/study/smart/stop":
            self._json(study_store.smart_stop(data.get("session_id", 0)))
        elif path == "/api/study/flashcards/decks/create":
            self._json(study_store.create_deck(data.get("name", ""), data.get("description", "")))
        elif path == "/api/study/flashcards/cards/create":
            self._json(study_store.add_card(data.get("deck_id", 0), data.get("question", ""), data.get("answer", "")))
        elif path == "/api/study/flashcards/cards/update":
            self._json(study_store.update_card(data.get("card_id", 0), data.get("question"), data.get("answer")))
        elif path == "/api/study/flashcards/cards/delete":
            self._json(study_store.delete_card(data.get("card_id", 0)))
        elif path == "/api/study/flashcards/review":
            self._json(study_store.review_card(data.get("card_id", 0), data.get("result"), data.get("typed_answer", ""), data.get("confidence"), bool(data.get("revealed_answer", False))))
        elif path == "/api/study/quizzes/create":
            self._json(study_store.create_quiz(data.get("name", ""), data.get("description", "")))
        elif path == "/api/study/quizzes/questions/create":
            self._json(study_store.add_quiz_question(data.get("quiz_id", 0), data.get("question", ""), data.get("answer_a", ""), data.get("answer_b", ""), data.get("answer_c", ""), data.get("answer_d", ""), data.get("correct_answer", "")))
        elif path == "/api/study/quizzes/questions/update":
            self._json(study_store.update_quiz_question(data.get("question_id", 0), data.get("question"), data.get("answer_a"), data.get("answer_b"), data.get("answer_c"), data.get("answer_d"), data.get("correct_answer")))
        elif path == "/api/study/quizzes/questions/delete":
            self._json(study_store.delete_quiz_question(data.get("question_id", 0)))
        elif path == "/api/study/quizzes/attempt/start":
            self._json(study_store.start_quiz_attempt(data.get("quiz_id", 0), data.get("mode", "all")))
        elif path == "/api/study/quizzes/answer":
            self._json(study_store.answer_quiz_question(data.get("question_id", 0), data.get("answer", ""), bool(data.get("marked_for_review", False))))
        elif path == "/api/study/quizzes/mark-review":
            self._json(study_store.mark_quiz_question(data.get("question_id", 0)))
        elif path == "/api/study/quizzes/attempt/finish":
            self._json(study_store.finish_quiz_attempt(data.get("quiz_id", 0), data.get("score", 0), data.get("total_questions", 0)))
        elif path == "/api/study/languages/lists/create":
            self._json(study_store.create_language_list(data.get("name", ""), data.get("language", "English")))
        elif path == "/api/study/languages/words/create":
            self._json(study_store.add_language_word(data.get("list_id", 0), data.get("word", ""), data.get("meaning", ""), data.get("pronunciation", "")))
        elif path == "/api/study/languages/words/delete":
            self._json(study_store.delete_language_word(data.get("word_id", 0)))
        elif path == "/api/study/languages/review":
            self._json(study_store.review_language_word(data.get("word_id", 0), data.get("result", "wrong")))
        elif path == "/api/study/notes/create":
            self._json(study_store.create_note(data.get("target_type", "study"), data.get("target_id", 0), data.get("note_text", "")))
        elif path == "/api/study/settings/delete":
            self._json(study_store.delete_action(data.get("action", ""), data.get("confirm_text", ""), data.get("target_id", 0)))
        elif path == "/api/reminders/create":
            self._json(reminders_store.create(data.get("title", ""), data.get("notes", ""), data.get("due_at", ""), bool(data.get("is_private", False))))
        elif path == "/api/reminders/update":
            self._json(reminders_store.update(data.get("id", 0), data.get("title", ""), data.get("notes", ""), data.get("due_at", ""), bool(data.get("is_private", False))))
        elif path == "/api/reminders/delete":
            self._json(reminders_store.delete(data.get("id", 0), data.get("confirm_text", "")))
        elif path == "/api/reminders/dismiss":
            self._json(reminders_store.dismiss(data.get("id", 0)))
        elif path == "/api/reminders/mark-triggered":
            self._json(reminders_store.mark_triggered(data.get("id", 0)))
        elif path == "/api/reminders/snooze":
            self._json(reminders_store.snooze(data.get("id", 0), data.get("minutes", 5)))
        elif path == "/api/calendar/events/create":
            self._json(calendar_store.create(data.get("title", ""), data.get("description", ""), data.get("start_date", ""), data.get("start_time", ""), data.get("reminder_minutes_before", 0), data.get("repeat_type", "none"), data.get("snooze_minutes", 0)))
        elif path == "/api/calendar/events/update":
            self._json(calendar_store.update(data.get("id", 0), data.get("title", ""), data.get("description", ""), data.get("start_date", ""), data.get("start_time", ""), data.get("reminder_minutes_before", 0), data.get("repeat_type", "none")))
        elif path == "/api/calendar/events/delete":
            self._json(calendar_store.delete(data.get("id", 0), data.get("confirm_text", "")))
        elif path == "/api/calendar/dismiss":
            self._json(calendar_store.dismiss(data.get("event_id", data.get("id", 0)), data.get("occurrence_start", "")))
        elif path == "/api/calendar/snooze":
            self._json(calendar_store.snooze(data.get("event_id", data.get("id", 0)), data.get("minutes", 10)))
        elif path == "/api/todo/lists/create":
            self._json(todo_store.create_list(data.get("name", ""), data.get("emoji", "📥")))
        elif path == "/api/todo/lists/update":
            self._json(todo_store.update_list(data.get("id", 0), data.get("name", ""), data.get("emoji", "📥")))
        elif path == "/api/todo/lists/delete":
            self._json(todo_store.delete_list(data.get("id", 0), data.get("confirm_text", "")))
        elif path == "/api/todo/tasks/create":
            self._json(todo_store.create_task(data.get("list_id", 0), data.get("title", ""), data.get("notes", ""), data.get("due_date", ""), data.get("due_time", ""), bool(data.get("reminder_enabled", False)), data.get("repeat_unit", "none"), data.get("repeat_interval", 0)))
        elif path == "/api/todo/tasks/update":
            self._json(todo_store.update_task(data.get("id", 0), data.get("list_id", 0), data.get("title", ""), data.get("notes", ""), data.get("due_date", ""), data.get("due_time", ""), bool(data.get("reminder_enabled", False)), data.get("repeat_unit", "none"), data.get("repeat_interval", 0), data.get("status", "active")))
        elif path == "/api/todo/tasks/delete":
            self._json(todo_store.delete_task(data.get("id", 0), data.get("confirm_text", "")))
        elif path == "/api/todo/tasks/mark-done":
            self._json(todo_store.mark_done(data.get("id", data.get("task_id", 0))))
        elif path == "/api/todo/tasks/mark-active":
            self._json(todo_store.mark_active(data.get("id", data.get("task_id", 0))))
        elif path == "/api/todo/dismiss":
            self._json(todo_store.dismiss(data.get("task_id", data.get("id", 0))))
        elif path == "/api/todo/snooze":
            self._json(todo_store.snooze(data.get("task_id", data.get("id", 0)), data.get("minutes", 10)))
        elif path == "/api/benchmarks/run":
            self._json(start_benchmarks(STATE))
        elif path == "/api/reports/generate":
            self._json(start_report(STATE))
        elif path == "/api/camera/preview/start":
            self._json(start_preview(STATE))
        elif path == "/api/camera/preview/stop":
            self._json(stop_preview(STATE))
        elif path == "/api/control/quiet-mode":
            with STATE.lock:
                STATE.quiet_mode = bool(data.get("enabled", not STATE.quiet_mode))
            self._json({"status": "ok", "quiet_mode": STATE.quiet_mode})
        elif path == "/api/control/brightness":
            with STATE.lock:
                requested = data.get("brightness_percent", data.get("percent", STATE.brightness_percent))
                STATE.brightness_percent = max(0, min(100, int(requested)))
                STATE.brightness_auto = bool(data.get("auto_brightness", data.get("auto", STATE.brightness_auto)))
            self._json({"status": "planned", "dry_run": True, "brightness_percent": STATE.brightness_percent, "brightness_auto": STATE.brightness_auto})
        elif path == "/api/control/sound":
            with STATE.lock:
                requested = data.get("sound_percent", data.get("percent", STATE.sound_percent))
                if requested is not None:
                    STATE.sound_percent = max(0, min(100, int(requested)))
                STATE.sound_muted = bool(data.get("muted", STATE.sound_muted))
            self._json({"status": "planned", "dry_run": True, "sound_percent": STATE.sound_percent, "muted": STATE.sound_muted})
        elif path == "/api/control/remote-network":
            with STATE.lock:
                requested = data.get("state")
                STATE.remote_network_state = requested if requested in {"on", "off", "planned"} else "planned"
            self._json({"status": "planned", "dry_run": True, "remote_network_state": STATE.remote_network_state})
        elif path == "/api/settings/update":
            payload = settings_store.update_setting(str(data.get("section", "")), str(data.get("key", "")), data.get("value"))
            self._json(payload, 200 if payload.get("status") == "ok" else 400)
        elif path == "/api/settings/update-many":
            payload = settings_store.update_many(data.get("updates", []))
            self._json(payload, 200 if payload.get("status") == "ok" else 400)
        elif path == "/api/settings/reset-section":
            payload = settings_store.reset_section(str(data.get("section", "")))
            self._json(payload, 200 if payload.get("status") == "ok" else 400)
        elif path == "/api/privacy/pin/set":
            payload = settings_store.set_pin(str(data.get("pin", "")))
            self._json(payload, 200 if payload.get("status") == "ok" else 400)
        elif path == "/api/privacy/pin/verify":
            self._json(settings_store.verify_pin(str(data.get("pin", ""))))
        elif path == "/api/privacy/lock":
            self._json(settings_store.lock_private())
        elif path == "/api/camera/check/run":
            self._json(start_camera_check(STATE))
        elif path == "/api/audio/check/run":
            self._json(start_audio_check(STATE))
        else:
            self._json({"status": "error", "error": "not_found"}, status=404)


def make_server(host=HOST, port=PORT):
    ensure_runtime_dirs()
    study_store.initialize()
    reminders_store.initialize()
    calendar_store.initialize()
    todo_store.initialize()
    return ThreadingHTTPServer((host, port), DiagnosticsHandler)


def serve_forever(host=HOST, port=PORT):
    server = make_server(host, port)
    try:
        server.serve_forever()
    finally:
        stop_preview(STATE)
        server.server_close()


def _query_str(query, key, default=""):
    values = query.get(key)
    return str(values[0]) if values else default


def _query_int(query, key, default=0):
    try:
        return int(_query_str(query, key, str(default)))
    except ValueError:
        return default
