import unittest

from system.services.resources.process_registry import get_process_registry


class ProcessRegistryTests(unittest.TestCase):
    def test_registry_contains_expected_components(self):
        components = {item["component"] for item in get_process_registry()}
        expected = {
            "nexa_backend",
            "nexa_godot_lcd_ui",
            "nexa_web_panel",
            "nexa_camera_service",
            "nexa_sensor_service",
            "nexa_remote_link",
            "nexa_diagnostics_runner",
            "nexa_test_runner",
        }
        self.assertTrue(expected.issubset(components))

    def test_registry_entries_include_required_fields(self):
        for item in get_process_registry():
            self.assertIn("display_name", item)
            self.assertIn("process_type", item)
            self.assertIn("expected", item)
            self.assertIsInstance(item["match_keywords"], list)
            self.assertIn("notes", item)


if __name__ == "__main__":
    unittest.main()

