import unittest

from system.services.resources.resource_report import build_resource_report, make_godot_telemetry_placeholder


class ResourceReportTests(unittest.TestCase):
    def test_resource_report_includes_godot_placeholder(self):
        snapshot = {
            "resource_report": "nexa_processes",
            "status": "not_checked",
            "message": "No known NeXa processes are running yet.",
            "processes": [
                {
                    "component": "nexa_godot_lcd_ui",
                    "display_name": "Godot LCD UI",
                    "status": "not_running",
                    "pid": None,
                    "cpu_percent": 0.0,
                    "memory_rss_mb": 0.0,
                    "memory_percent": 0.0,
                }
            ],
            "summary": {},
        }
        report = build_resource_report(process_snapshot=snapshot)
        telemetry = report["godot_telemetry"]
        self.assertEqual(telemetry["component"], "nexa_godot_lcd_ui")
        self.assertIsNone(telemetry["fps"])
        self.assertFalse(telemetry["gpu_usage_supported"])
        self.assertIsNone(telemetry["gpu_usage_percent"])

    def test_godot_placeholder_does_not_fake_gpu_usage(self):
        telemetry = make_godot_telemetry_placeholder({"status": "running"})
        self.assertEqual(telemetry["status"], "unknown")
        self.assertFalse(telemetry["gpu_usage_supported"])
        self.assertIsNone(telemetry["frame_time_ms"])


if __name__ == "__main__":
    unittest.main()

