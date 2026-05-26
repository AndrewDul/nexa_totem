#!/usr/bin/env python3
"""Check NeXa Learn Study API with a temporary SQLite database."""

import argparse
import json
import os
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from system.services.diagnostics.live_api import DiagnosticsHandler, HOST  # noqa: E402
from http.server import ThreadingHTTPServer  # noqa: E402


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
    parser = argparse.ArgumentParser(description="Check NeXa Learn Study API.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    with tempfile.TemporaryDirectory() as temp_dir:
        global API_URL
        old_env = os.environ.get("NEXA_STUDY_DB_PATH")
        os.environ["NEXA_STUDY_DB_PATH"] = str(Path(temp_dir) / "study.db")
        from system.services.study import study_store

        study_store.initialize()
        server = ThreadingHTTPServer((HOST, 0), DiagnosticsHandler)
        API_URL = "http://127.0.0.1:" + str(server.server_port)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            if not wait_for_api():
                raise RuntimeError("Diagnostics API did not start.")
            suffix = str(int(time.time() * 1000))
            results = {}
            results["overview"] = fetch("/api/study/overview")
            topic = "Check Topic " + suffix
            segments = [{"type": "focus", "minutes": 5}, {"type": "break", "minutes": 5}, {"type": "focus", "minutes": 5}]
            results["smart_start"] = post("/api/study/smart/start", {"topic": topic, "goal": "Check segments", "segments": segments})
            results["smart_duplicate"] = post("/api/study/smart/start", {"topic": topic, "goal": "Duplicate", "segments": segments})
            results["smart_invalid"] = post("/api/study/smart/start", {"topic": "Invalid " + suffix, "segments": [{"type": "focus", "minutes": 5}, {"type": "break", "minutes": 5}]})
            results["smart_status"] = fetch("/api/study/smart/status")
            results["smart_skip_note"] = post("/api/study/smart/skip-note", {"session_id": results["smart_start"].get("session_id", 0)})
            results["smart_stop"] = post("/api/study/smart/stop", {"session_id": results["smart_start"].get("session_id", 0)})

            deck = post("/api/study/flashcards/decks/create", {"name": "Deck " + suffix})
            deck_id = deck["deck"]["id"]
            card = post("/api/study/flashcards/cards/create", {"deck_id": deck_id, "question": "Question " + suffix, "answer": "Answer"})
            results["flashcard_deck"] = deck
            results["flashcard_card"] = card
            results["flashcard_review_start"] = fetch("/api/study/flashcards/review/start?" + urllib.parse.urlencode({"deck_id": deck_id, "mode": "all"}))
            results["flashcard_review"] = post("/api/study/flashcards/review", {"card_id": card["card"]["id"], "typed_answer": "Answer", "confidence": "know", "revealed_answer": False})
            card_unsure = post("/api/study/flashcards/cards/create", {"deck_id": deck_id, "question": "Unsure " + suffix, "answer": "Maybe"})
            card_repeat = post("/api/study/flashcards/cards/create", {"deck_id": deck_id, "question": "Repeat " + suffix, "answer": "Again"})
            results["flashcard_unsure"] = post("/api/study/flashcards/review", {"card_id": card_unsure["card"]["id"], "typed_answer": "Maybe", "confidence": "unsure", "revealed_answer": True})
            results["flashcard_dont_know"] = post("/api/study/flashcards/review", {"card_id": card_repeat["card"]["id"], "typed_answer": "Wrong", "confidence": "dont_know", "revealed_answer": True})
            results["flashcard_delete_blocked"] = post("/api/study/settings/delete", {"action": "delete_deck", "target_id": deck_id})

            quiz = post("/api/study/quizzes/create", {"name": "Quiz " + suffix})
            quiz_id = quiz["quiz"]["id"]
            question = post("/api/study/quizzes/questions/create", {
                "quiz_id": quiz_id,
                "question": "Quiz question " + suffix,
                "answer_a": "A1",
                "answer_b": "B1",
                "answer_c": "C1",
                "answer_d": "D1",
                "correct_answer": "B",
            })
            results["quiz"] = quiz
            results["quiz_question"] = question
            results["quiz_answer_correct"] = post("/api/study/quizzes/answer", {"question_id": question["question"]["id"], "answer": "B"})
            results["quiz_answer_wrong"] = post("/api/study/quizzes/answer", {"question_id": question["question"]["id"], "answer": "A"})
            results["quiz_mark"] = post("/api/study/quizzes/mark-review", {"question_id": question["question"]["id"]})
            results["quiz_delete_blocked"] = post("/api/study/settings/delete", {"action": "delete_quiz", "target_id": quiz_id})

            lang = post("/api/study/languages/lists/create", {"name": "Words " + suffix, "language": "Polish"})
            list_id = lang["list"]["id"]
            word = post("/api/study/languages/words/create", {"list_id": list_id, "word": "dom" + suffix, "pronunciation": "dom", "meaning": "house"})
            results["language_list"] = lang
            results["language_word"] = word
            results["language_review"] = post("/api/study/languages/review", {"word_id": word["word"]["id"], "result": "correct"})
            results["language_wrong"] = post("/api/study/languages/review", {"word_id": word["word"]["id"], "result": "wrong"})

            results["stats"] = fetch("/api/study/stats")
            results["history"] = fetch("/api/study/history")
            results["delete_blocked"] = post("/api/study/settings/delete", {"action": "delete_all_study_data"})
            expected_errors = {"smart_invalid", "delete_blocked", "flashcard_delete_blocked", "quiz_delete_blocked"}
            status = "ok" if all(key in expected_errors or value.get("status") in {"ok", "duplicate", "similar"} for key, value in results.items()) else "error"
            if any(results[key].get("error") != "confirmation_required" for key in ["delete_blocked", "flashcard_delete_blocked", "quiz_delete_blocked"]) or results["smart_invalid"].get("status") != "error":
                status = "error"
            output = {"status": status, "started_server": True, "port": server.server_port, "results": results}
            if args.json:
                print(json.dumps(output, indent=2, sort_keys=True))
            else:
                print("Study API check passed.")
                for key in results:
                    print(f"- OK: {key}")
            return 0 if status == "ok" else 1
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)
            if old_env is None:
                os.environ.pop("NEXA_STUDY_DB_PATH", None)
            else:
                os.environ["NEXA_STUDY_DB_PATH"] = old_env


if __name__ == "__main__":
    raise SystemExit(main())
