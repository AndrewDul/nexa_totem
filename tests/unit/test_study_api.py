import os
import tempfile
import unittest
from pathlib import Path

from system.services.diagnostics import live_api
from system.services.study import study_store


class StudyApiTests(unittest.TestCase):
    def test_live_api_exposes_study_endpoints(self):
        text = Path(live_api.__file__).read_text(encoding="utf-8")
        for endpoint in [
            "/api/study/overview",
            "/api/study/stats",
            "/api/study/history",
            "/api/study/smart/start",
            "/api/study/smart/status",
            "/api/study/smart/skip-note",
            "/api/study/flashcards/decks/create",
            "/api/study/flashcards/cards/update",
            "/api/study/flashcards/cards/delete",
            "/api/study/flashcards/review/start",
            "/api/study/quizzes/create",
            "/api/study/quizzes/questions/update",
            "/api/study/quizzes/questions/delete",
            "/api/study/quizzes/mark-review",
            "/api/study/languages/lists/create",
            "/api/study/settings/delete",
        ]:
            self.assertIn(endpoint, text)

    def test_env_database_initialization_uses_study_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            old_env = os.environ.get("NEXA_STUDY_DB_PATH")
            path = Path(temp_dir) / "study.db"
            os.environ["NEXA_STUDY_DB_PATH"] = str(path)
            try:
                payload = study_store.initialize()
                self.assertTrue(path.exists())
                self.assertEqual(payload["status"], "ok")
            finally:
                if old_env is None:
                    os.environ.pop("NEXA_STUDY_DB_PATH", None)
                else:
                    os.environ["NEXA_STUDY_DB_PATH"] = old_env


if __name__ == "__main__":
    unittest.main()
