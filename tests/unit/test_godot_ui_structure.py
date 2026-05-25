import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
GODOT_DIR = REPO_ROOT / "system/ui/godot"


class GodotUiStructureTests(unittest.TestCase):
    def read(self, path):
        return Path(path).read_text(encoding="utf-8")

    def test_godot_project_files_exist(self):
        self.assertTrue(GODOT_DIR.exists())
        self.assertTrue((GODOT_DIR / "project.godot").exists())
        self.assertTrue((GODOT_DIR / "scenes/Main.tscn").exists())

    def test_required_scripts_exist(self):
        for script_name in [
            "main.gd",
            "theme.gd",
            "gesture_detector.gd",
            "navigation_controller.gd",
            "face_renderer.gd",
            "diagnostics_data.gd",
        ]:
            self.assertTrue((GODOT_DIR / "scripts" / script_name).exists(), script_name)

    def test_target_resolution_is_configured(self):
        project = self.read(GODOT_DIR / "project.godot")
        self.assertIn("viewport_width=640", project)
        self.assertIn("viewport_height=480", project)
        self.assertIn("resizable=false", project)

    def test_fullscreen_is_not_default_for_this_sprint(self):
        project = self.read(GODOT_DIR / "project.godot").lower()
        self.assertNotIn("fullscreen=true", project)

    def test_dev_launcher_is_windowed_fixed_size(self):
        launcher = self.read(REPO_ROOT / "scripts/run/run_godot_ui_dev.sh")
        self.assertIn("--windowed", launcher)
        self.assertIn("--resolution 640x480", launcher)
        self.assertNotIn("--fullscreen", launcher)
        self.assertIn("nexa_godot_lcd_ui", launcher)

    def test_lcd_launcher_exists_as_placeholder(self):
        launcher = self.read(REPO_ROOT / "scripts/run/run_godot_ui_lcd.sh")
        self.assertIn("planned for a later sprint", launcher)
        self.assertIn("run_godot_ui_dev.sh", launcher)

    def test_required_screen_names_are_represented(self):
        text = self._all_godot_text()
        for screen_name in [
            "Face Home",
            "Menu",
            "Clock",
            "Notification Control Center",
            "Diagnostics",
        ]:
            self.assertIn(screen_name, text)

    def test_diagnostics_tab_names_are_represented(self):
        text = self._all_godot_text()
        for tab_name in [
            "Overview",
            "System",
            "Processes",
            "Benchmarks",
            "Camera",
            "Audio",
            "Reports",
            "Logs",
            "Network",
        ]:
            self.assertIn(tab_name, text)

    def _all_godot_text(self):
        parts = []
        for path in GODOT_DIR.rglob("*"):
            if path.is_file() and path.suffix in {".gd", ".tscn", ".godot", ".md"}:
                parts.append(self.read(path))
        return "\n".join(parts)


if __name__ == "__main__":
    unittest.main()

