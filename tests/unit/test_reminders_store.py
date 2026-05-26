import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from system.services.reminders import reminders_store
from system.services.settings import settings_store


class RemindersStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "reminders.db"
        self.settings_path = Path(self.temp_dir.name) / "settings.json"
        self.old_db = os.environ.get("NEXA_REMINDERS_DB_PATH")
        self.old_settings = os.environ.get("NEXA_SETTINGS_PATH")
        os.environ["NEXA_REMINDERS_DB_PATH"] = str(self.db_path)
        os.environ["NEXA_SETTINGS_PATH"] = str(self.settings_path)
        reminders_store.initialize()

    def tearDown(self):
        if self.old_db is None:
            os.environ.pop("NEXA_REMINDERS_DB_PATH", None)
        else:
            os.environ["NEXA_REMINDERS_DB_PATH"] = self.old_db
        if self.old_settings is None:
            os.environ.pop("NEXA_SETTINGS_PATH", None)
        else:
            os.environ["NEXA_SETTINGS_PATH"] = self.old_settings
        self.temp_dir.cleanup()

    def future(self, minutes=10):
        return (datetime.now(timezone.utc).replace(microsecond=0) + timedelta(minutes=minutes)).isoformat()

    def past(self, minutes=10):
        return (datetime.now(timezone.utc).replace(microsecond=0) - timedelta(minutes=minutes)).isoformat()

    def test_schema_and_env_path_create(self):
        result = reminders_store.initialize()
        self.assertEqual(result["schema_version"], 1)
        self.assertEqual(result["db_path"], str(self.db_path))
        self.assertTrue(self.db_path.exists())

    def test_create_validation_and_list_split(self):
        self.assertEqual(reminders_store.create("", due_at=self.future())["error"], "title_required")
        self.assertEqual(reminders_store.create("Bad date", due_at="not-a-date")["error"], "invalid_due_at")
        upcoming = reminders_store.create("Future", due_at=self.future())
        past = reminders_store.create("Past", due_at=self.past())
        listed = reminders_store.list_reminders()
        self.assertEqual(upcoming["status"], "ok")
        self.assertEqual(past["status"], "ok")
        self.assertEqual(len(listed["upcoming"]), 1)
        self.assertEqual(len(listed["past"]), 1)

    def test_past_remains_and_update_future_moves_upcoming(self):
        old = reminders_store.create("Old", due_at=self.past())
        listed = reminders_store.list_reminders()
        self.assertEqual(len(listed["past"]), 1)
        moved = reminders_store.update(old["reminder"]["id"], "Old reused", due_at=self.future())
        listed = reminders_store.list_reminders()
        self.assertEqual(moved["reminder"]["status"], "active")
        self.assertIsNone(moved["reminder"]["dismissed_at"])
        self.assertIsNone(moved["reminder"]["triggered_at"])
        self.assertEqual(len(listed["upcoming"]), 1)
        self.assertEqual(len(listed["past"]), 0)

    def test_dismissed_past_update_future_moves_upcoming(self):
        old = reminders_store.create("Dismissed old", due_at=self.past())
        reminders_store.dismiss(old["reminder"]["id"])
        dismissed_list = reminders_store.list_reminders()
        self.assertTrue(any(row["id"] == old["reminder"]["id"] for row in dismissed_list["past"]))
        moved = reminders_store.update(old["reminder"]["id"], "Dismissed reused", due_at=self.future(20))
        listed = reminders_store.list_reminders()
        self.assertEqual(moved["reminder"]["status"], "active")
        self.assertIsNone(moved["reminder"]["dismissed_at"])
        self.assertIsNone(moved["reminder"]["triggered_at"])
        self.assertTrue(any(row["id"] == old["reminder"]["id"] for row in listed["upcoming"]))
        self.assertFalse(any(row["id"] == old["reminder"]["id"] for row in listed["past"]))

    def test_triggered_past_update_future_moves_upcoming(self):
        old = reminders_store.create("Triggered old", due_at=self.past())
        reminders_store.mark_triggered(old["reminder"]["id"])
        moved = reminders_store.update(old["reminder"]["id"], "Triggered reused", due_at=self.future(25))
        listed = reminders_store.list_reminders()
        self.assertEqual(moved["reminder"]["status"], "active")
        self.assertIsNone(moved["reminder"]["triggered_at"])
        self.assertTrue(any(row["id"] == old["reminder"]["id"] for row in listed["upcoming"]))
        self.assertFalse(any(row["id"] == old["reminder"]["id"] for row in reminders_store.due()["due"]))

    def test_delete_requires_confirmation(self):
        item = reminders_store.create("Delete me", due_at=self.future())
        blocked = reminders_store.delete(item["reminder"]["id"])
        deleted = reminders_store.delete(item["reminder"]["id"], "DELETE_REMINDER")
        self.assertEqual(blocked["error"], "confirmation_required")
        self.assertEqual(deleted["status"], "ok")

    def test_due_trigger_dismiss_and_snooze(self):
        item = reminders_store.create("Due now", due_at=self.past())
        due = reminders_store.due()
        listed_due = reminders_store.list_reminders()
        self.assertEqual(due["count"], 1)
        self.assertTrue(any(row["id"] == item["reminder"]["id"] for row in listed_due["past"]))
        triggered = reminders_store.mark_triggered(item["reminder"]["id"])
        due_after_triggered = reminders_store.due()
        self.assertEqual(triggered["reminder"]["status"], "due")
        self.assertTrue(triggered["reminder"]["triggered_at"])
        self.assertEqual(due_after_triggered["count"], 1)
        snoozed = reminders_store.snooze(item["reminder"]["id"], 5)
        self.assertEqual(snoozed["reminder"]["status"], "active")
        self.assertTrue(any(row["id"] == item["reminder"]["id"] for row in reminders_store.list_reminders()["upcoming"]))
        dismissed = reminders_store.dismiss(item["reminder"]["id"])
        self.assertEqual(dismissed["status"], "ok")
        self.assertFalse(any(row["id"] == item["reminder"]["id"] for row in reminders_store.due()["due"]))

    def test_notification_dismiss_keeps_reminder_in_past_table(self):
        item = reminders_store.create("Dismiss from notification", due_at=self.past())
        dismissed = reminders_store.dismiss(item["reminder"]["id"])
        listed = reminders_store.list_reminders()
        self.assertEqual(dismissed["status"], "ok")
        self.assertFalse(any(row["id"] == item["reminder"]["id"] for row in reminders_store.due()["due"]))
        self.assertTrue(any(row["id"] == item["reminder"]["id"] for row in listed["past"]))

    def test_ui_datetime_format_without_timezone_is_accepted(self):
        due_text = (datetime.now().replace(microsecond=0) - timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:%S")
        item = reminders_store.create("UI local due", due_at=due_text)
        self.assertEqual(item["status"], "ok")
        self.assertGreaterEqual(reminders_store.due()["count"], 1)

    def test_private_reminders_hide_and_show(self):
        settings_store.set_pin("1234", self.settings_path)
        settings_store.update_setting("notifications", "private_reminders_enabled", True, self.settings_path)
        settings_store.lock_private(self.settings_path)
        item = reminders_store.create("Private title", due_at=self.past(), is_private=True)
        self.assertEqual(item["reminder"]["title"], "Private reminder locked")
        self.assertTrue(item["reminder"]["requires_pin"])
        settings_store.verify_pin("1234", self.settings_path)
        due = reminders_store.due()
        self.assertEqual(due["due"][0]["title"], "Private title")
        self.assertFalse(due["due"][0]["requires_pin"])


if __name__ == "__main__":
    unittest.main()
