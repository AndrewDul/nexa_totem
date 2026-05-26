import unittest

from system.services.diagnostics import live_api


class CalendarApiStructureTests(unittest.TestCase):
    def test_calendar_endpoints_are_registered(self):
        with open(live_api.__file__, "r", encoding="utf-8") as handle:
            text = handle.read()
        for endpoint in [
            "/api/calendar/month",
            "/api/calendar/day",
            "/api/calendar/events/create",
            "/api/calendar/events/update",
            "/api/calendar/events/delete",
            "/api/calendar/due",
            "/api/calendar/dismiss",
            "/api/calendar/snooze",
            "/api/calendar/settings/stats",
        ]:
            self.assertIn(endpoint, text)
        self.assertIn("calendar_store.initialize()", text)


if __name__ == "__main__":
    unittest.main()

