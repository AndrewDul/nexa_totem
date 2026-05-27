import os
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from system.services.todo import todo_store


class TodoStoreTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "todo.db"
        self.old_env = os.environ.get("NEXA_TODO_DB_PATH")
        os.environ["NEXA_TODO_DB_PATH"] = str(self.db_path)

    def tearDown(self):
        if self.old_env is None:
            os.environ.pop("NEXA_TODO_DB_PATH", None)
        else:
            os.environ["NEXA_TODO_DB_PATH"] = self.old_env
        self.temp_dir.cleanup()

    def inbox_id(self):
        return todo_store.lists()["lists"][0]["id"]

    def test_schema_and_default_inbox(self):
        payload = todo_store.initialize()
        self.assertEqual(payload["status"], "ok")
        self.assertTrue(self.db_path.exists())
        lists = todo_store.lists()["lists"]
        self.assertEqual(lists[0]["name"], "Inbox")
        self.assertEqual(lists[0]["emoji"], "📥")

    def test_create_list_and_reject_empty_name(self):
        self.assertEqual(todo_store.create_list("", "📚")["error"], "name_required")
        created = todo_store.create_list("Study", "📚")
        self.assertEqual(created["status"], "ok")
        self.assertEqual(created["list"]["name"], "Study")

    def test_task_lifecycle_keeps_completed_visible(self):
        list_id = self.inbox_id()
        self.assertEqual(todo_store.create_task(list_id, "", path=self.db_path)["error"], "title_required")
        created = todo_store.create_task(list_id, "Finish Java notes", due_date="2026-05-26", due_time="18:00", reminder_enabled=True)
        task_id = created["task"]["id"]
        tasks = todo_store.tasks(list_id)
        self.assertEqual(len(tasks["active"]), 1)
        done = todo_store.mark_done(task_id)
        self.assertEqual(done["task"]["status"], "completed")
        tasks = todo_store.tasks(list_id)
        self.assertEqual(len(tasks["completed"]), 1)
        self.assertEqual(todo_store.due()["count"], 0)
        active = todo_store.mark_active(task_id)
        self.assertEqual(active["task"]["status"], "active")

    def test_delete_task_and_list_require_confirmation(self):
        created_list = todo_store.create_list("Errands", "🛒")["list"]
        task = todo_store.create_task(created_list["id"], "Buy milk")["task"]
        self.assertEqual(todo_store.delete_task(task["id"])["error"], "confirmation_required")
        self.assertEqual(todo_store.delete_task(task["id"], "DELETE_TODO_TASK")["status"], "ok")
        self.assertFalse(todo_store.tasks(created_list["id"])["active"])
        self.assertEqual(todo_store.delete_list(created_list["id"])["error"], "confirmation_required")
        self.assertEqual(todo_store.delete_list(created_list["id"], "DELETE_TODO_LIST")["status"], "ok")

    def test_due_snooze_and_dismiss_repeat(self):
        list_id = self.inbox_id()
        now = datetime.now().replace(microsecond=0)
        task = todo_store.create_task(
            list_id,
            "Due task",
            due_date=now.date().isoformat(),
            due_time=now.strftime("%H:%M"),
            reminder_enabled=True,
            repeat_unit="hours",
            repeat_interval=6,
        )["task"]
        due = todo_store.due()
        self.assertTrue(any(row["task_id"] == task["id"] for row in due["due"]))
        snoozed = todo_store.snooze(task["id"], 10)
        self.assertEqual(snoozed["status"], "ok")
        self.assertFalse(any(row["task_id"] == task["id"] for row in todo_store.due()["due"]))
        dismissed = todo_store.dismiss(task["id"])
        self.assertEqual(dismissed["status"], "ok")
        self.assertIn("T", dismissed["next_reminder_at"])

    def test_repeat_calculation_units(self):
        now = datetime(2026, 5, 26, 10, 0, 0)
        task = {"due_date": "2026-05-26", "due_time": "10:00"}
        self.assertEqual(todo_store.calculate_next_reminder(task, {"repeat_unit": "hours", "repeat_interval": 6}, now), now + timedelta(hours=6))
        self.assertEqual(todo_store.calculate_next_reminder(task, {"repeat_unit": "days", "repeat_interval": 2}, now), now + timedelta(days=2))
        self.assertEqual(todo_store.calculate_next_reminder(task, {"repeat_unit": "weekly", "repeat_interval": 0}, now), now + timedelta(days=7))
        self.assertEqual(todo_store.calculate_next_reminder(task, {"repeat_unit": "monthly", "repeat_interval": 0}, now).month, 6)
        self.assertEqual(todo_store.calculate_next_reminder(task, {"repeat_unit": "yearly", "repeat_interval": 0}, now).year, 2027)

    def test_notification_log_does_not_spam_for_same_occurrence(self):
        list_id = self.inbox_id()
        now = datetime.now().replace(microsecond=0)
        task = todo_store.create_task(list_id, "Logged task", due_date=now.date().isoformat(), due_time=now.strftime("%H:%M"), reminder_enabled=True)["task"]
        self.assertTrue(any(row["task_id"] == task["id"] for row in todo_store.due()["due"]))
        self.assertTrue(any(row["task_id"] == task["id"] for row in todo_store.due()["due"]))
        with todo_store._connect(self.db_path) as conn:
            count = conn.execute("SELECT COUNT(*) AS c FROM todo_notification_log WHERE task_id=?", (task["id"],)).fetchone()["c"]
        self.assertEqual(count, 1)


if __name__ == "__main__":
    unittest.main()

