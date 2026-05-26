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
        self.assertIn("run/max_fps=30", project)

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

    def test_premium_rounded_style_helpers_are_represented(self):
        text = self._all_godot_text()
        for term in [
            "draw_card",
            "draw_pill",
            "draw_tile",
            "rounded",
        ]:
            self.assertIn(term, text)

    def test_runtime_helpers_are_local_and_callable(self):
        main = self.read(GODOT_DIR / "scripts/main.gd")
        for helper in [
            "func _draw_card",
            "func _draw_tile",
            "func _draw_pill",
            "func _draw_soft_panel",
        ]:
            self.assertIn(helper, main)
        for bad_call in [
            "ThemeScript.draw_card",
            "ThemeScript.draw_tile",
            "ThemeScript.draw_pill",
            "ThemeScript.draw_soft_panel",
        ]:
            self.assertNotIn(bad_call, main)

    def test_no_rect2_translated_usage_remains(self):
        text = "\n".join(
            self.read(path)
            for path in (GODOT_DIR / "scripts").glob("*.gd")
        )
        self.assertNotIn(".translated(", text)

    def test_menu_tile_layout_and_short_subtitles_are_represented(self):
        main = self.read(GODOT_DIR / "scripts/main.gd")
        self.assertIn("284.0", main)
        self.assertIn("72.0", main)
        self.assertIn("index % 2", main)
        for subtitle in [
            "Clock",
            "Focus",
            "Alerts",
            "Events",
            "To-do",
            "Play",
            "System",
            "Setup",
        ]:
            self.assertIn(f'"subtitle": "{subtitle}"', main)

    def test_control_center_cards_are_represented(self):
        main = self.read(GODOT_DIR / "scripts/main.gd")
        self.assertIn("Control Center", main)
        self.assertIn("var controls: Array", main)
        self.assertIn("_draw_notification", main)

    def test_face_uses_vertical_eyes_without_strong_glow(self):
        face = self.read(GODOT_DIR / "scripts/face_renderer.gd")
        self.assertIn("_draw_vertical_capsule", face)
        self.assertIn("_draw_bean_eye", face)
        self.assertNotIn("width + 20.0", face)
        self.assertNotIn("height + 24.0", face)

    def test_face_idle_blink_logic_is_represented(self):
        face = self.read(GODOT_DIR / "scripts/face_renderer.gd")
        self.assertIn("BLINK_PERIOD", face)
        self.assertIn("BLINK_DURATION", face)
        self.assertIn("fmod", face)
        self.assertIn("_blink_amount", face)

    def test_scroll_support_is_represented(self):
        main = self.read(GODOT_DIR / "scripts/main.gd")
        for term in [
            "diagnostic_scroll_y",
            "control_center_scroll_y",
            "func _draw_scrollbar",
            "clampf(diagnostic_scroll_y",
            "clampf(control_center_scroll_y",
            "MOUSE_BUTTON_WHEEL_UP",
            "MOUSE_BUTTON_WHEEL_DOWN",
        ]:
            self.assertIn(term, main)

    def test_panel_font_sizes_are_reduced(self):
        main = self.read(GODOT_DIR / "scripts/main.gd")
        self.assertIn('_draw_text("Menu", Vector2(32, 52), 27', main)
        self.assertIn('Vector2(58, 30), 17', main)
        self.assertIn('Vector2(58, 52), 11', main)
        self.assertIn('_draw_text("Control Center", Vector2(44, 64), 26', main)
        self.assertIn('_draw_text("Diagnostics", Vector2(26, 40), 26', main)

    def test_menu_tile_cards_are_represented(self):
        main = self.read(GODOT_DIR / "scripts/main.gd")
        self.assertIn("MENU_TILES", main)
        self.assertIn("_draw_tile(rect", main)
        self.assertIn("Diagnostics", main)

    def test_face_home_label_is_not_drawn_on_home_screen(self):
        main = self.read(GODOT_DIR / "scripts/main.gd")
        self.assertNotIn('_draw_text("Face Home"', main)

    def test_transition_logic_is_represented(self):
        main = self.read(GODOT_DIR / "scripts/main.gd")
        for term in [
            "transition_progress",
            "transition_direction",
            "_draw_transition",
            "TRANSITION_SECONDS",
            "CLOSE_TRANSITION_SECONDS",
        ]:
            self.assertIn(term, main)
        self.assertIn("TRANSITION_SECONDS := 0.14", main)
        self.assertIn("CLOSE_TRANSITION_SECONDS := 0.10", main)
        self.assertIn("transition_overlay", main)
        self.assertIn("_draw_overlay_screen", main)

    def test_redraw_throttling_is_represented(self):
        main = self.read(GODOT_DIR / "scripts/main.gd")
        for term in [
            "TARGET_REDRAW_FPS",
            "REDRAW_INTERVAL",
            "redraw_accumulator",
            "redraw_requested",
            "_request_redraw",
        ]:
            self.assertIn(term, main)

    def test_navigation_close_behaviour_is_represented(self):
        main = self.read(GODOT_DIR / "scripts/main.gd")
        gesture = self.read(GODOT_DIR / "scripts/gesture_detector.gd")
        self.assertIn('nav.current_screen == "Menu" and action == "swipe_right"', main)
        self.assertIn('nav.current_screen == "Clock" and action == "swipe_left"', main)
        self.assertIn('nav.current_screen == "Notification Control Center" and action == "swipe_up"', main)
        self.assertIn('"swipe_up"', gesture)

    def test_premium_style_terms_are_represented(self):
        text = self._all_godot_text()
        for term in [
            "draw_card",
            "rounded",
            "transition",
            "Face Home",
            "Menu",
            "Clock",
            "Notification Control Center",
            "Diagnostics",
        ]:
            self.assertIn(term, text)

    def _all_godot_text(self):
        parts = []
        for path in GODOT_DIR.rglob("*"):
            if path.is_file() and path.suffix in {".gd", ".tscn", ".godot", ".md"}:
                parts.append(self.read(path))
        return "\n".join(parts)


if __name__ == "__main__":
    unittest.main()
