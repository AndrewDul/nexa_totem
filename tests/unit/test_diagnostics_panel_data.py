import tempfile
import unittest

from system.services.diagnostics.panel_data import build_diagnostic_panel_data
from system.services.diagnostics.reports import write_latest_report
from system.services.diagnostics.status import make_component_status


class DiagnosticsPanelDataTests(unittest.TestCase):
    def test_panel_data_returns_not_checked_when_no_reports_exist(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            data = build_diagnostic_panel_data(report_root=temp_dir)

        self.assertEqual(data["panel"], "diagnostics")
        self.assertEqual(data["status"], "warning")
        self.assertEqual(data["latest_reports"]["system_status"]["status"], "not_checked")
        self.assertEqual(data["components"]["raspberry_pi"]["status"], "not_checked")

    def test_panel_data_reads_latest_reports_when_they_exist(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            pi = make_component_status("raspberry_pi", "ok", "Pi ok.")
            speaker = make_component_status("usb_speaker", "ok", "Speaker ok.")
            camera = make_component_status("camera_csi", "missing", "Camera missing.")
            system_status = {
                "device": "nexa_totem",
                "status": "warning",
                "message": "System has warnings.",
                "components": {
                    "raspberry_pi": pi,
                    "usb_speaker": speaker,
                    "camera_csi": camera,
                },
            }
            write_latest_report("system_status", system_status, report_root=temp_dir)
            write_latest_report("pi_health", pi, report_root=temp_dir)

            data = build_diagnostic_panel_data(report_root=temp_dir)

        self.assertEqual(data["status"], "warning")
        self.assertEqual(data["latest_reports"]["pi_health"]["status"], "ok")
        self.assertEqual(data["components"]["camera_csi"]["status"], "missing")

    def test_panel_data_returns_not_checked_for_missing_resource_reports(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            data = build_diagnostic_panel_data(report_root=temp_dir)

        self.assertEqual(data["latest_reports"]["nexa_resources"]["status"], "not_checked")
        self.assertEqual(data["latest_reports"]["resource_benchmark"]["status"], "not_checked")

    def test_panel_data_reads_latest_resource_reports(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            resource_report = {
                "resource_report": "nexa_resource_overview",
                "status": "ok",
                "message": "Resources available.",
            }
            benchmark_report = {
                "benchmark_report": "resource_benchmark",
                "status": "ok",
                "message": "Benchmarks available.",
            }
            write_latest_report("nexa_resources", resource_report, report_root=temp_dir)
            write_latest_report("resource_benchmark", benchmark_report, report_root=temp_dir)
            data = build_diagnostic_panel_data(report_root=temp_dir)

        self.assertEqual(data["latest_reports"]["nexa_resources"]["status"], "ok")
        self.assertEqual(data["latest_reports"]["resource_benchmark"]["status"], "ok")


if __name__ == "__main__":
    unittest.main()
