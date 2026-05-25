import unittest
from unittest.mock import patch

from scripts.hardware.check_system_status import collect_system_status
from system.services.diagnostics.collector import make_system_status
from system.services.diagnostics.status import make_component_status


class SystemStatusTests(unittest.TestCase):
    def test_combined_system_status_returns_warning_if_speaker_missing(self):
        components = {
            "raspberry_pi": make_component_status("raspberry_pi", "ok"),
            "usb_speaker": make_component_status("usb_speaker", "missing"),
            "camera_csi": make_component_status("camera_csi", "ok"),
        }
        status = make_system_status(components)
        self.assertEqual(status["status"], "warning")

    def test_combined_system_status_returns_warning_if_camera_missing(self):
        components = {
            "raspberry_pi": make_component_status("raspberry_pi", "ok"),
            "usb_speaker": make_component_status("usb_speaker", "ok"),
            "camera_csi": make_component_status("camera_csi", "missing"),
        }
        status = make_system_status(components)
        self.assertEqual(status["status"], "warning")

    def test_combined_system_status_returns_ok_if_all_components_ok(self):
        components = {
            "raspberry_pi": make_component_status("raspberry_pi", "ok"),
            "usb_speaker": make_component_status("usb_speaker", "ok"),
            "camera_csi": make_component_status("camera_csi", "ok"),
        }
        status = make_system_status(components)
        self.assertEqual(status["status"], "ok")

    def test_collect_system_status_includes_camera_component(self):
        with patch("scripts.hardware.check_system_status.collect_pi_health") as pi_health:
            with patch("scripts.hardware.check_system_status.collect_speaker_status") as speaker_status:
                with patch("scripts.hardware.check_system_status.collect_camera_status") as camera_status:
                    pi_health.return_value = make_component_status("raspberry_pi", "ok")
                    speaker_status.return_value = make_component_status("usb_speaker", "ok")
                    camera_status.return_value = make_component_status("camera_csi", "ok")
                    status = collect_system_status()

        self.assertEqual(status["status"], "ok")
        self.assertIn("camera_csi", status["components"])


if __name__ == "__main__":
    unittest.main()
