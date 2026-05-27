import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
MAIN_GD = REPO_ROOT / "system/ui/godot/scripts/main.gd"


class JoystickPolicyStaticTests(unittest.TestCase):
    def test_repeat_select_and_center_release_policy_exists(self):
        text = MAIN_GD.read_text(encoding="utf-8")
        self.assertIn("joystick_repeat_delay_seconds := 0.28", text)
        self.assertIn("joystick_select_cooldown_seconds := 0.55", text)
        self.assertIn("joystick_requires_center_release_for_select := true", text)
        self.assertIn("joystick_select_armed", text)
        self.assertIn("hardware_joystick_candidate_count", text)
        self.assertIn("func _dispatch_nexa_input_action", text)
        self.assertIn('joystick == "CENTER"', text)


if __name__ == "__main__":
    unittest.main()
