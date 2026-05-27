import unittest

from system.network.access_point.ap_profile import (
    NEXA_AP_IP,
    NEXA_AP_PASSWORD,
    NEXA_AP_PREFIX,
    NEXA_AP_SSID,
    NEXA_HARDWARE_POST_URL,
    NEXA_HARDWARE_SERVER_PORT,
    build_nmcli_commands,
    build_server_command,
)


class AccessPointProfileTests(unittest.TestCase):
    def test_constants_match_plan(self):
        self.assertEqual(NEXA_AP_SSID, "NeXa-ToTem")
        self.assertEqual(NEXA_AP_PASSWORD, "nexa12345")
        self.assertEqual(NEXA_AP_IP, "10.42.0.1")
        self.assertEqual(NEXA_AP_PREFIX, 24)
        self.assertEqual(NEXA_HARDWARE_SERVER_PORT, 8080)
        self.assertEqual(NEXA_HARDWARE_POST_URL, "http://10.42.0.1:8080/api/hardware")

    def test_nmcli_commands_are_generated_strings(self):
        commands = build_nmcli_commands("wlan0")
        self.assertTrue(commands)
        self.assertTrue(all(isinstance(command, str) for command in commands))
        joined = "\n".join(commands)
        self.assertIn("802-11-wireless.mode ap", joined)
        self.assertIn("ipv4.method shared", joined)
        self.assertIn("10.42.0.1/24", joined)
        self.assertIn("wifi-sec.key-mgmt wpa-psk", joined)
        self.assertIn("wifi-sec.psk nexa12345", joined)

    def test_server_command_uses_lan_host_and_port(self):
        command = build_server_command()
        self.assertIn("python3 scripts/run/run_hardware_gateway_dev.py", command)
        self.assertIn("--host 0.0.0.0", command)
        self.assertIn("--port 8080", command)


if __name__ == "__main__":
    unittest.main()
