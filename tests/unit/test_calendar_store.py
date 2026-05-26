import os
import tempfile
import unittest
from datetime import date, datetime, timedelta
from pathlib import Path

from system.services.calendar import calendar_store


class CalendarStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "calendar.db"
        self.old_db = os.environ.get("NEXA_CALENDAR_DB_PATH")
        os.environ["NEXA_CALENDAR_DB_PATH"] = str(self.db_path)
        calendar_store.initialize()

    def tearDown(self):
        if self.old_db is None:
            os.environ.pop("NEXA_CALENDAR_DB_PATH", None)
        else:
            os.environ["NEXA_CALENDAR_DB_PATH"] = self.old_db
        self.temp_dir.cleanup()

    def today(self):
        return date.today().isoformat()

    def now_time(self):
        return datetime.now().strftime("%H:%M")

    def test_schema_and_env_path(self):
        result = calendar_store.initialize()
        self.assertEqual(result["schema_version"], 1)
        self.assertEqual(result["db_path"], str(self.db_path))
        self.assertTrue(self.db_path.exists())

    def test_month_grid_shape_labels_and_today(self):
        today = date.today()
        result = calendar_store.month(today.year, today.month)
        cells = [cell for week in result["weeks"] for cell in week["cells"]]
        self.assertEqual(result["month_name"], today.strftime("%B"))
        self.assertEqual(len(cells), 42)
        self.assertEqual(cells[0]["full_date"], (date(today.year, today.month, 1) - timedelta(days=date(today.year, today.month, 1).weekday())).isoformat())
        self.assertTrue(any(cell["is_sunday"] for cell in cells))
        self.assertTrue(any(cell["is_today"] and cell["full_date"] == today.isoformat() for cell in cells))

    def test_create_update_delete_and_day(self):
        created = calendar_store.create("Study Java", "OOP", self.today(), "18:00", 15, "weekly")
        self.assertEqual(created["status"], "ok")
        event_id = created["event"]["id"]
        day = calendar_store.day(self.today())
        self.assertEqual(len(day["events"]), 1)
        updated = calendar_store.update(event_id, "Study Python", "SQLite", self.today(), "19:00", 5, "none")
        self.assertEqual(updated["event"]["title"], "Study Python")
        blocked = calendar_store.delete(event_id)
        self.assertEqual(blocked["error"], "confirmation_required")
        deleted = calendar_store.delete(event_id, "DELETE_CALENDAR_EVENT")
        self.assertEqual(deleted["status"], "ok")
        self.assertEqual(calendar_store.day(self.today())["events"], [])

    def test_recurring_events_appear_in_visible_month(self):
        target = date.today().replace(day=15)
        for repeat in ["daily", "weekly", "monthly", "yearly"]:
            created = calendar_store.create(f"{repeat} event", "", target.isoformat(), "09:00", 0, repeat)
            self.assertEqual(created["status"], "ok")
        result = calendar_store.month(target.year, target.month)
        events = [event for rows in result["events_by_date"].values() for event in rows]
        titles = {event["title"] for event in events}
        self.assertIn("daily event", titles)
        self.assertIn("weekly event", titles)
        self.assertIn("monthly event", titles)
        self.assertIn("yearly event", titles)

    def test_due_dismiss_snooze_and_no_delete(self):
        created = calendar_store.create("Due event", "", self.today(), self.now_time(), 0, "none")
        due = calendar_store.due()
        self.assertGreaterEqual(due["count"], 1)
        item = next(row for row in due["due"] if row["id"] == created["event"]["id"])
        dismissed = calendar_store.dismiss(item["id"], item["occurrence_start"])
        self.assertEqual(dismissed["status"], "ok")
        self.assertFalse(any(row["id"] == item["id"] for row in calendar_store.due()["due"]))
        self.assertTrue(any(row["id"] == item["id"] for row in calendar_store.day(self.today())["events"]))

        snooze_target = calendar_store.create("Snooze event", "", self.today(), self.now_time(), 0, "none")
        snoozed = calendar_store.snooze(snooze_target["event"]["id"], 10)
        self.assertEqual(snoozed["status"], "ok")
        self.assertFalse(any(row["id"] == snooze_target["event"]["id"] for row in calendar_store.due()["due"]))

    def test_deleted_event_does_not_appear(self):
        created = calendar_store.create("Delete me", "", self.today(), "10:00", 0, "none")
        calendar_store.delete(created["event"]["id"], "DELETE_CALENDAR_EVENT")
        result = calendar_store.month(date.today().year, date.today().month)
        events = [event for rows in result["events_by_date"].values() for event in rows]
        self.assertFalse(any(event["id"] == created["event"]["id"] for event in events))


if __name__ == "__main__":
    unittest.main()

