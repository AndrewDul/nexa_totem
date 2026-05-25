import tempfile
import unittest

from scripts.hardware.run_diagnostics import collect_diagnostics
from system.services.diagnostics.status import make_component_status


class RunDiagnosticsTests(unittest.TestCase):
    def test_run_diagnostics_combines_fake_components(self):
        report = collect_diagnostics(
            pi_collector=lambda: make_component_status("raspberry_pi", "ok"),
            speaker_collector=lambda: make_component_status("usb_speaker", "ok"),
            camera_collector=lambda: make_component_status("camera_csi", "ok"),
            report_root="unused",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["components"]["camera_csi"]["status"], "ok")
        self.assertEqual(report["validations"], {})

    def test_run_diagnostics_can_include_fake_camera_capture_validation(self):
        report = collect_diagnostics(
            pi_collector=lambda: make_component_status("raspberry_pi", "ok"),
            speaker_collector=lambda: make_component_status("usb_speaker", "ok"),
            camera_collector=lambda: make_component_status("camera_csi", "ok"),
            camera_capture_validator=lambda: make_component_status(
                "camera_csi",
                "ok",
                "Camera capture validation succeeded.",
                details={"output_path": "fake.jpg"},
                source="camera_capture",
            ),
            include_camera_capture=True,
            report_root="unused",
        )

        self.assertEqual(report["validations"]["camera_capture"]["status"], "ok")
        self.assertEqual(report["validations"]["camera_capture"]["details"]["output_path"], "fake.jpg")

    def test_run_diagnostics_saves_latest_and_history_when_requested(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            report = collect_diagnostics(
                pi_collector=lambda: make_component_status("raspberry_pi", "ok"),
                speaker_collector=lambda: make_component_status("usb_speaker", "ok"),
                camera_collector=lambda: make_component_status("camera_csi", "missing"),
                save_report=True,
                save_history=True,
                history_limit=5,
                report_root=temp_dir,
            )

        self.assertIn("system_status", report["report_paths"]["latest"])
        self.assertIn("camera_status", report["report_paths"]["history"])


if __name__ == "__main__":
    unittest.main()

