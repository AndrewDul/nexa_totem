import unittest

from system.services.diagnostics.collector import make_system_status
from system.services.diagnostics.status import make_component_status


class SystemStatusTests(unittest.TestCase):
    def test_combined_system_status_returns_warning_if_speaker_missing(self):
        components = {
            "raspberry_pi": make_component_status("raspberry_pi", "ok"),
            "usb_speaker": make_component_status("usb_speaker", "missing"),
        }
        status = make_system_status(components)
        self.assertEqual(status["status"], "warning")

    def test_combined_system_status_returns_ok_if_all_components_ok(self):
        components = {
            "raspberry_pi": make_component_status("raspberry_pi", "ok"),
            "usb_speaker": make_component_status("usb_speaker", "ok"),
        }
        status = make_system_status(components)
        self.assertEqual(status["status"], "ok")


if __name__ == "__main__":
    unittest.main()
