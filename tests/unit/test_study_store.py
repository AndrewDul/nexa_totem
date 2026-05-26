import os
import tempfile
import unittest
from pathlib import Path

from system.services.study import study_store


class StudyStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.path = Path(self.temp_dir.name) / "study.db"
        self.old_env = os.environ.get("NEXA_STUDY_DB_PATH")
        os.environ["NEXA_STUDY_DB_PATH"] = str(self.path)
        study_store.initialize()

    def tearDown(self):
        if self.old_env is None:
            os.environ.pop("NEXA_STUDY_DB_PATH", None)
        else:
            os.environ["NEXA_STUDY_DB_PATH"] = self.old_env
        self.temp_dir.cleanup()

    def test_db_creates_schema_and_normalizes_names(self):
        self.assertTrue(self.path.exists())
        self.assertEqual(study_store.normalize_name("  Java, OOP!!  "), "java oop")

    def test_duplicate_and_similar_topic_detection(self):
        first = study_store.start_pomodoro("Java OOP inheritance", 15)
        duplicate = study_store.start_pomodoro("java oop inheritance", 15)
        similar = study_store.start_pomodoro("Java OOP inheritence", 15)
        self.assertEqual(first["status"], "ok")
        self.assertEqual(duplicate["status"], "duplicate")
        self.assertIn(similar["status"], {"similar", "duplicate"})

    def test_pomodoro_start_stop_and_topic_stats(self):
        started = study_store.start_pomodoro("Math algebra", 15)
        stopped = study_store.stop_timer()
        stats = study_store.stats()
        self.assertEqual(started["status"], "ok")
        self.assertEqual(stopped["status"], "ok")
        self.assertEqual(stats["status"], "ok")
        self.assertTrue(stats["per_topic_stats"])
        self.assertEqual(stats["per_topic_stats"][0]["topic"], "Math algebra")

    def test_flashcard_deck_card_duplicate_and_review(self):
        deck = study_store.create_deck("Biology")
        duplicate = study_store.create_deck("biology")
        card = study_store.add_card(deck["deck"]["id"], "What is DNA?", "Code")
        card_duplicate = study_store.add_card(deck["deck"]["id"], "what is dna", "Code")
        reviewed = study_store.review_card(card["card"]["id"], typed_answer="Code", confidence="know", revealed_answer=False)
        self.assertEqual(deck["status"], "ok")
        self.assertEqual(duplicate["status"], "duplicate")
        self.assertEqual(card["status"], "ok")
        self.assertEqual(card_duplicate["status"], "duplicate")
        self.assertEqual(reviewed["card"]["status"], "known")
        self.assertEqual(reviewed["card"]["correct_count"], 1)
        self.assertTrue(reviewed["was_correct"])

    def test_smart_study_segments_validate_and_save_notes(self):
        adjacent = study_store.smart_start("Adjacent focus", segments=[{"type": "focus", "minutes": 5}, {"type": "focus", "minutes": 5}])
        self.assertEqual(adjacent["status"], "error")
        self.assertIn("alternate", adjacent["message"])
        invalid = study_store.smart_start("Too short", segments=[{"type": "focus", "minutes": 5}, {"type": "break", "minutes": 5}])
        self.assertEqual(invalid["status"], "error")
        self.assertIn("focus before and after", invalid["message"])
        started = study_store.smart_start(
            "Segmented study",
            "Review chapters",
            segments=[{"type": "focus", "minutes": 5}, {"type": "break", "minutes": 5}, {"type": "focus", "minutes": 5}],
        )
        note = study_store.smart_note(started["session_id"], "What did you learn?")
        status = study_store.smart_status()
        self.assertEqual(started["status"], "ok")
        self.assertEqual(note["status"], "ok")
        self.assertEqual(status["status"], "ok")
        self.assertTrue(status["active"])
        self.assertIn("note_prompt_pending", status)
        self.assertEqual(status["current_segment_type"], "focus")

    def test_flashcard_review_confidence_and_priority(self):
        deck = study_store.create_deck("Priority cards")
        repeat = study_store.add_card(deck["deck"]["id"], "Repeat me", "R")
        unsure = study_store.add_card(deck["deck"]["id"], "Unsure me", "U")
        known = study_store.add_card(deck["deck"]["id"], "Known me", "K")
        blocked = study_store.review_card(known["card"]["id"], confidence="know")
        unsure_result = study_store.review_card(unsure["card"]["id"], typed_answer="maybe", confidence="unsure", revealed_answer=True)
        repeat_result = study_store.review_card(repeat["card"]["id"], typed_answer="wrong", confidence="dont_know", revealed_answer=True)
        next_card = study_store.next_card(deck["deck"]["id"])
        self.assertEqual(blocked["error"], "answer_or_reveal_required")
        self.assertEqual(unsure_result["card"]["status"], "unsure")
        self.assertEqual(repeat_result["card"]["status"], "repeat")
        self.assertEqual(next_card["card"]["id"], repeat["card"]["id"])

    def test_flashcard_mastered_requires_50_correct(self):
        deck = study_store.create_deck("Mastery cards")
        card = study_store.add_card(deck["deck"]["id"], "Master?", "yes")
        result = None
        for _ in range(49):
            result = study_store.review_card(card["card"]["id"], typed_answer="yes", confidence="know", revealed_answer=False)
        self.assertEqual(result["card"]["status"], "known")
        result = study_store.review_card(card["card"]["id"], typed_answer="yes", confidence="know", revealed_answer=False)
        self.assertEqual(result["card"]["correct_count"], 50)
        self.assertEqual(result["card"]["status"], "mastered")

    def test_quiz_answer_returns_visible_answer_text(self):
        quiz = study_store.create_quiz("Answer text quiz")
        question = study_store.add_quiz_question(quiz["quiz"]["id"], "Pick two", "One", "Two", "Three", "Four", "B")
        result = study_store.answer_quiz_question(question["question"]["id"], "A")
        self.assertFalse(result["correct"])
        self.assertEqual(result["correct_answer"], "B")
        self.assertEqual(result["correct_answer_text"], "Two")
        self.assertEqual(result["selected_answer_text"], "One")

    def test_language_detail_delete_and_mastered_threshold(self):
        lang = study_store.create_language_list("Polish basics", "Polish")
        word = study_store.add_language_word(lang["list"]["id"], "dom", "house", "dohm")
        detail = study_store.language_list_detail(lang["list"]["id"])
        self.assertEqual(detail["words"][0]["word"], "dom")
        result = None
        for _ in range(50):
            result = study_store.review_language_word(word["word"]["id"], "correct")
        self.assertEqual(result["word"]["status"], "mastered")
        deleted = study_store.delete_language_word(word["word"]["id"])
        self.assertEqual(deleted["status"], "ok")

    def test_flashcard_card_update_and_delete(self):
        deck = study_store.create_deck("Editable cards")
        card = study_store.add_card(deck["deck"]["id"], "Old?", "Old")
        updated = study_store.update_card(card["card"]["id"], "New?", "New")
        deleted = study_store.delete_card(card["card"]["id"])
        detail = study_store.deck_detail(deck["deck"]["id"])
        self.assertEqual(updated["card"]["question"], "New?")
        self.assertEqual(deleted["status"], "ok")
        self.assertEqual(detail["cards"], [])

    def test_quiz_duplicate_question_answer_and_marked_status(self):
        quiz = study_store.create_quiz("Physics")
        duplicate = study_store.create_quiz("physics")
        question = study_store.add_quiz_question(quiz["quiz"]["id"], "Force unit?", "J", "N", "W", "Pa", "B")
        question_duplicate = study_store.add_quiz_question(quiz["quiz"]["id"], "force unit", "J", "N", "W", "Pa", "B")
        wrong = study_store.answer_quiz_question(question["question"]["id"], "A", marked=True)
        correct = study_store.answer_quiz_question(question["question"]["id"], "B")
        self.assertEqual(duplicate["status"], "duplicate")
        self.assertEqual(question["status"], "ok")
        self.assertEqual(question["question"]["correct_answer"], "B")
        self.assertEqual(question_duplicate["status"], "duplicate")
        self.assertFalse(wrong["correct"])
        self.assertTrue(correct["correct"])
        self.assertEqual(wrong["question"]["marked_for_review"], 1)

    def test_quiz_mark_update_and_delete_question(self):
        quiz = study_store.create_quiz("Editable quiz")
        question = study_store.add_quiz_question(quiz["quiz"]["id"], "Pick B", "A", "B", "C", "D", "B")
        marked = study_store.mark_quiz_question(question["question"]["id"])
        updated = study_store.update_quiz_question(question["question"]["id"], correct_answer="C")
        deleted = study_store.delete_quiz_question(question["question"]["id"])
        detail = study_store.quiz_detail(quiz["quiz"]["id"])
        self.assertTrue(marked["marked_for_review"])
        self.assertEqual(updated["question"]["correct_answer"], "C")
        self.assertEqual(deleted["status"], "ok")
        self.assertEqual(detail["questions"], [])

    def test_language_review_mastered_logic(self):
        lang = study_store.create_language_list("Polish words", "Polish")
        word = study_store.add_language_word(lang["list"]["id"], "dom", "house", "dom")
        wrong = study_store.review_language_word(word["word"]["id"], "wrong")
        result = None
        for _ in range(50):
            result = study_store.review_language_word(word["word"]["id"], "correct")
        self.assertEqual(wrong["word"]["wrong_count"], 1)
        self.assertEqual(result["word"]["status"], "mastered")
        self.assertEqual(result["word"]["correct_count"], 50)

    def test_history_returns_real_events(self):
        study_store.create_deck("History deck")
        history = study_store.history()
        self.assertEqual(history["status"], "ok")
        self.assertTrue(history["events"])
        self.assertEqual(history["events"][0]["event_type"], "deck_created")

    def test_delete_all_requires_confirmation_and_works(self):
        study_store.create_deck("Delete me")
        blocked = study_store.delete_action("delete_all_study_data", "")
        deleted = study_store.delete_action("delete_all_study_data", "DELETE_STUDY_DATA")
        stats = study_store.stats()
        self.assertEqual(blocked["status"], "error")
        self.assertEqual(deleted["status"], "ok")
        self.assertEqual(stats["total_flashcard_decks"], 0)


if __name__ == "__main__":
    unittest.main()
