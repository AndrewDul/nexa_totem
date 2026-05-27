import subprocess
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
LAUNCHER = REPO_ROOT / "scripts/run/run_nexa_totem_esp_mode.sh"
NORMAL_LAUNCHER = REPO_ROOT / "scripts/run/run_godot_ui_with_api_dev.sh"


class EspModeLauncherStaticTests(unittest.TestCase):
    def read(self, path: Path) -> str:
        return path.read_text(encoding="utf-8")

    def test_launcher_contains_required_safety_and_pull_mode_steps(self):
        text = self.read(LAUNCHER)
        self.assertIn("CONFIRM_NEXA_ESP_WIFI_SWITCH", text)
        self.assertIn("ESP mode will disconnect Raspberry Pi from normal Wi-Fi/internet and connect to NeXa-ESP.", text)
        self.assertIn("connect_to_esp_network.py --apply --i-understand-this-will-disconnect-internet", text)
        self.assertIn("export NEXA_HARDWARE_MODE=pull_esp_server", text)
        self.assertIn("export NEXA_ESP_STATE_URL=http://192.168.4.1/api/state", text)
        self.assertIn("export NEXA_ESP_POLL_INTERVAL_SECONDS=0.2", text)
        self.assertIn("run_godot_ui_with_api_dev.sh", text)
        self.assertIn("trap cleanup EXIT INT TERM", text)
        self.assertIn("reconnect_home_wifi.py --apply --i-understand-this-changes-network", text)

    def test_normal_launcher_does_not_switch_wifi(self):
        text = self.read(NORMAL_LAUNCHER)
        self.assertNotIn("connect_to_esp_network.py", text)
        self.assertNotIn("reconnect_home_wifi.py", text)

    def test_launcher_without_confirmation_exits_before_connect(self):
        completed = subprocess.run(
            ["bash", str(LAUNCHER)],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        output = completed.stdout + completed.stderr
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("CONFIRM_NEXA_ESP_WIFI_SWITCH=RUN", output)
        self.assertIn("No Wi-Fi changes were made.", output)
        self.assertNotIn("Connecting Raspberry Pi Wi-Fi to NeXa-ESP", output)


if __name__ == "__main__":
    unittest.main()
