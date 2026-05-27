import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
MAIN_GD = REPO_ROOT / "system/ui/godot/scripts/main.gd"


class SettingsExitStaticTests(unittest.TestCase):
    def test_exit_nexa_closes_ui_only(self):
        text = MAIN_GD.read_text(encoding="utf-8")
        self.assertIn("Exit NeXa", text)
        self.assertIn("This closes NeXa ToTem only. Raspberry Pi will stay on.", text)
        self.assertIn("get_tree().quit()", text)
        for forbidden in ["shutdown", "poweroff", "reboot", "halt"]:
            self.assertNotIn(forbidden, text.lower())


if __name__ == "__main__":
    unittest.main()
