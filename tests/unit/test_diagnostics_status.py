import unittest

from system.services.diagnostics.status import combine_statuses, make_component_status


class DiagnosticsStatusTests(unittest.TestCase):
    def test_make_component_status_returns_expected_fields(self):
        status = make_component_status(
            component="usb_speaker",
            status="ok",
            message="USB speaker is connected.",
            details={"playback_devices_found": 1},
            checked_at="2026-05-25T14:10:00Z",
            source="speaker_status",
        )

        self.assertEqual(status["component"], "usb_speaker")
        self.assertEqual(status["status"], "ok")
        self.assertEqual(status["message"], "USB speaker is connected.")
        self.assertEqual(status["details"]["playback_devices_found"], 1)
        self.assertEqual(status["checked_at"], "2026-05-25T14:10:00Z")
        self.assertEqual(status["source"], "speaker_status")

    def test_combine_statuses_returns_ok_when_all_ok(self):
        statuses = [
            make_component_status("one", "ok"),
            make_component_status("two", "ok"),
        ]
        self.assertEqual(combine_statuses(statuses), "ok")

    def test_combine_statuses_returns_warning_when_component_missing(self):
        statuses = [
            make_component_status("one", "ok"),
            make_component_status("two", "missing"),
        ]
        self.assertEqual(combine_statuses(statuses), "warning")

    def test_combine_statuses_returns_error_when_component_error(self):
        statuses = [
            make_component_status("one", "warning"),
            make_component_status("two", "error"),
        ]
        self.assertEqual(combine_statuses(statuses), "error")


if __name__ == "__main__":
    unittest.main()
