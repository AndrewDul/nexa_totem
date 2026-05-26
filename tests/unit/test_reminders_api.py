import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class RemindersApiStructureTests(unittest.TestCase):
    def test_reminders_api_routes_are_registered(self):
        live_api = (ROOT / "system/services/diagnostics/live_api.py").read_text(encoding="utf-8")
        for endpoint in [
            "/api/reminders/overview",
            "/api/reminders/list",
            "/api/reminders/due",
            "/api/reminders/create",
            "/api/reminders/update",
            "/api/reminders/delete",
            "/api/reminders/dismiss",
            "/api/reminders/mark-triggered",
            "/api/reminders/settings/stats",
        ]:
            self.assertIn(endpoint, live_api)
        self.assertIn("reminders_store", live_api)


if __name__ == "__main__":
    unittest.main()
