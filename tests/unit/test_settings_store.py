import json
import tempfile
import time
import unittest
from pathlib import Path

from system.services.settings import settings_store


class SettingsStoreTests(unittest.TestCase):
    def test_default_settings_load(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "nexa_settings.json"
            data = settings_store.load_settings(path)
        self.assertIn("appearance", data)
        self.assertIn("private_notifications_enabled", data["notifications"])
        self.assertIn("private_reminders_enabled", data["notifications"])
        for key in [
            "time_color",
            "hour_color",
            "minute_color",
            "second_color",
            "date_color",
            "day_color",
            "month_color",
            "year_color",
        ]:
            self.assertIn(key, data["appearance"])

    def test_broken_settings_file_falls_back(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "nexa_settings.json"
            path.write_text("{broken", encoding="utf-8")
            data = settings_store.load_settings(path)
        self.assertEqual(data["modes"]["current_mode"], "Normal")

    def test_settings_update_validates_section_and_key(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "nexa_settings.json"
            ok = settings_store.update_setting("display", "text_size", "Large", path)
            bad = settings_store.update_setting("display", "missing", True, path)
        self.assertEqual(ok["status"], "ok")
        self.assertEqual(bad["status"], "error")

    def test_appearance_values_are_validated(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "nexa_settings.json"
            ok = settings_store.update_setting("appearance", "background_color", "Graphite", path)
            clock_ok = settings_store.update_setting("appearance", "second_color", "Gold", path)
            bad_color = settings_store.update_setting("appearance", "background_color", "Invisible", path)
            bad_clock_color = settings_store.update_setting("appearance", "hour_color", "Invisible", path)
            bad_preset = settings_store.update_setting("appearance", "preset", "Missing", path)
        self.assertEqual(ok["status"], "ok")
        self.assertEqual(clock_ok["status"], "ok")
        self.assertEqual(bad_color["status"], "error")
        self.assertEqual(bad_clock_color["status"], "error")
        self.assertEqual(bad_preset["status"], "error")

    def test_update_many_saves_preset_values(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "nexa_settings.json"
            payload = settings_store.update_many([
                {"section": "appearance", "key": "preset", "value": "Night Red"},
                {"section": "appearance", "key": "eye_color", "value": "Red"},
                {"section": "appearance", "key": "mouth_color", "value": "Red"},
            ], path)
            data = settings_store.load_settings(path)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(data["appearance"]["preset"], "Night Red")
        self.assertEqual(data["appearance"]["eye_color"], "Red")

    def test_update_many_can_update_time_group_colors(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "nexa_settings.json"
            payload = settings_store.update_many([
                {"section": "appearance", "key": "time_color", "value": "Cyan"},
                {"section": "appearance", "key": "hour_color", "value": "Cyan"},
                {"section": "appearance", "key": "minute_color", "value": "Cyan"},
                {"section": "appearance", "key": "second_color", "value": "Cyan"},
            ], path)
            data = settings_store.load_settings(path)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(data["appearance"]["time_color"], "Cyan")
        self.assertEqual(data["appearance"]["hour_color"], "Cyan")
        self.assertEqual(data["appearance"]["minute_color"], "Cyan")
        self.assertEqual(data["appearance"]["second_color"], "Cyan")

    def test_update_many_rejects_invalid_clock_color(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "nexa_settings.json"
            payload = settings_store.update_many([
                {"section": "appearance", "key": "day_color", "value": "Invisible"},
            ], path)
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["error"], "invalid_color")

    def test_reset_section_restores_defaults(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "nexa_settings.json"
            settings_store.update_setting("display", "text_size", "Large", path)
            reset = settings_store.reset_section("display", path)
            data = settings_store.load_settings(path)
        self.assertEqual(reset["status"], "ok")
        self.assertEqual(data["display"]["text_size"], settings_store.DEFAULT_SETTINGS["display"]["text_size"])

    def test_pin_set_stores_hash_not_raw_pin(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "nexa_settings.json"
            settings_store.set_pin("1234", path)
            raw = json.loads(path.read_text(encoding="utf-8"))
            safe = settings_store.get_settings(path)
        self.assertNotEqual(raw["privacy"]["pin_hash"], "1234")
        self.assertTrue(raw["privacy"]["pin_salt"])
        self.assertNotIn("pin_hash", safe["privacy"])
        self.assertNotIn("pin_salt", safe["privacy"])

    def test_pin_verify_wrong_and_correct(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "nexa_settings.json"
            settings_store.set_pin("1234", path)
            wrong = settings_store.verify_pin("0000", path, now=100)
            correct = settings_store.verify_pin("1234", path, now=100)
        self.assertFalse(wrong["unlocked"])
        self.assertTrue(correct["unlocked"])

    def test_private_gates_until_unlock_and_lock(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "nexa_settings.json"
            settings_store.set_pin("1234", path)
            settings_store.update_setting("notifications", "private_notifications_enabled", True, path)
            settings_store.update_setting("notifications", "private_reminders_enabled", True, path)
            locked = settings_store.load_settings(path)
            settings_store.verify_pin("1234", path, now=time.time())
            unlocked = settings_store.load_settings(path)
            settings_store.lock_private(path)
            relocked = settings_store.load_settings(path)
        self.assertTrue(settings_store.should_hide_private_notifications(locked))
        self.assertTrue(settings_store.should_hide_private_reminders(locked))
        self.assertFalse(settings_store.should_hide_private_notifications(unlocked))
        self.assertFalse(settings_store.should_hide_private_reminders(unlocked))
        self.assertTrue(settings_store.should_hide_private_notifications(relocked))

    def test_pin_requires_four_digits(self):
        self.assertTrue(settings_store.valid_pin("1234"))
        self.assertFalse(settings_store.valid_pin("12345"))
        self.assertFalse(settings_store.valid_pin("12a4"))

    def test_default_quick_shelf_list_exists(self):
        defaults = settings_store.default_settings()
        self.assertIn("Brightness", defaults["quick_shelf"]["enabled_tiles"])
        self.assertIn("Settings", defaults["quick_shelf"]["enabled_tiles"])


if __name__ == "__main__":
    unittest.main()
