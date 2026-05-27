import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from system.services.diagnostics.live_api import DiagnosticsHandler
from system.services.todo import todo_store


class TodoApiRoutingTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.old_env = os.environ.get("NEXA_TODO_DB_PATH")
        os.environ["NEXA_TODO_DB_PATH"] = str(Path(self.temp_dir.name) / "todo.db")

    def tearDown(self):
        if self.old_env is None:
            os.environ.pop("NEXA_TODO_DB_PATH", None)
        else:
            os.environ["NEXA_TODO_DB_PATH"] = self.old_env
        self.temp_dir.cleanup()

    def test_store_functions_support_api_payloads(self):
        lists = todo_store.lists()
        list_id = lists["lists"][0]["id"]
        now = datetime.now().replace(microsecond=0)
        created = todo_store.create_task(list_id, "API task", due_date=now.date().isoformat(), due_time=now.strftime("%H:%M"), reminder_enabled=True)
        self.assertEqual(created["status"], "ok")
        self.assertTrue(todo_store.due()["due"])
        self.assertEqual(todo_store.mark_done(created["task"]["id"])["status"], "ok")
        self.assertEqual(todo_store.delete_task(created["task"]["id"], "DELETE_TODO_TASK")["status"], "ok")

    def test_live_api_contains_todo_routes(self):
        source = Path("system/services/diagnostics/live_api.py").read_text()
        self.assertIn("/api/todo/overview", source)
        self.assertIn("/api/todo/lists/create", source)
        self.assertIn("/api/todo/tasks/mark-done", source)
        self.assertIn("todo_store.initialize()", source)
        self.assertIsNotNone(DiagnosticsHandler)


if __name__ == "__main__":
    unittest.main()

