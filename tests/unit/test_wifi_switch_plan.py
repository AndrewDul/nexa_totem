import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.network import connect_to_esp_network, reconnect_home_wifi
from system.network.wifi_switch.wifi_switch_plan import (
    NEXA_ESP_PASSWORD,
    NEXA_ESP_SSID,
    NEXA_ESP_STATE_URL,
    PREVIOUS_WIFI_CONNECTION_PATH,
    build_connect_commands,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


class WifiSwitchPlanTests(unittest.TestCase):
    def read(self, path):
        return Path(path).read_text(encoding="utf-8")

    def test_esp_values_represented(self):
        self.assertEqual(NEXA_ESP_SSID, "NeXa-ESP")
        self.assertEqual(NEXA_ESP_PASSWORD, "nexa12345")
        self.assertEqual(NEXA_ESP_STATE_URL, "http://192.168.4.1/api/state")
        self.assertEqual(PREVIOUS_WIFI_CONNECTION_PATH, "var/data/network/previous_wifi_connection.json")

    def test_connect_commands_target_esp(self):
        joined = "\n".join(build_connect_commands("wlan0"))
        self.assertIn("NeXa-ESP", joined)
        self.assertIn("wifi-sec.psk nexa12345", joined)
        self.assertIn("connection up NeXa-ESP", joined)

    def test_connect_defaults_to_dry_run(self):
        with patch.object(connect_to_esp_network, "collect_network_state", return_value={}):
            summary = connect_to_esp_network.dry_run_summary()
        self.assertTrue(summary["dry_run"])
        self.assertFalse(summary["changed_network"])

    def test_connect_requires_apply_warning_flag(self):
        source = self.read(REPO_ROOT / "scripts/network/connect_to_esp_network.py")
        self.assertIn("--apply", source)
        self.assertIn("--i-understand-this-will-disconnect-internet", source)
        self.assertIn("missing_warning_flag", source)

    def test_reconnect_defaults_to_dry_run(self):
        with patch.object(reconnect_home_wifi, "load_previous_wifi", return_value={"connection_name": "HomeWiFi", "exists": True}):
            summary = reconnect_home_wifi.dry_run_summary()
        self.assertTrue(summary["dry_run"])
        self.assertFalse(summary["changed_network"])
        self.assertIn("HomeWiFi", "\n".join(summary["reconnect_commands"]))

    def test_reconnect_requires_apply_warning_flag(self):
        source = self.read(REPO_ROOT / "scripts/network/reconnect_home_wifi.py")
        self.assertIn("--apply", source)
        self.assertIn("--i-understand-this-changes-network", source)
        self.assertIn("missing_warning_flag", source)

    def test_no_apply_happens_in_tests(self):
        with patch.object(connect_to_esp_network.subprocess, "run") as run:
            with patch.object(connect_to_esp_network, "collect_network_state", return_value={}):
                connect_to_esp_network.dry_run_summary()
        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
