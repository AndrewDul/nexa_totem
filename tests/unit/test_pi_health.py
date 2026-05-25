import unittest

from system.services.system_health.pi_health import (
    collect_pi_health,
    parse_cpu_temperature,
    parse_throttled_output,
)


class PiHealthTests(unittest.TestCase):
    def test_parse_throttled_output_zero(self):
        parsed = parse_throttled_output("throttled=0x0")
        self.assertEqual(parsed["throttled_raw"], "0x0")
        self.assertFalse(parsed["undervoltage_detected"])
        self.assertFalse(parsed["throttling_detected"])

    def test_parse_throttled_output_under_voltage_and_throttling(self):
        parsed = parse_throttled_output("0x50005")
        self.assertTrue(parsed["undervoltage_detected"])
        self.assertTrue(parsed["throttling_detected"])
        self.assertTrue(parsed["flags"]["under_voltage_now"])
        self.assertTrue(parsed["flags"]["throttling_has_occurred"])

    def test_missing_vcgencmd_does_not_crash(self):
        def command_runner(command, timeout=3):
            return {"ok": False, "stdout": "", "stderr": "missing", "missing": True}

        def file_reader(path):
            values = {
                "/proc/uptime": "12.34 56.78",
                "/proc/meminfo": "MemTotal: 1000 kB\nMemAvailable: 400 kB\n",
                "/sys/class/thermal/thermal_zone0/temp": "45000",
                "/etc/os-release": 'PRETTY_NAME="Test OS"',
            }
            return values.get(path, "")

        status = collect_pi_health(command_runner=command_runner, file_reader=file_reader)
        self.assertIn(status["status"], {"ok", "warning", "unknown"})
        self.assertFalse(status["details"]["vcgencmd_available"])

    def test_temperature_parser_handles_valid_and_missing_values(self):
        self.assertEqual(parse_cpu_temperature("45123"), 45.1)
        self.assertEqual(parse_cpu_temperature("temp=48.2'C"), 48.2)
        self.assertIsNone(parse_cpu_temperature(""))
        self.assertIsNone(parse_cpu_temperature("not a temperature"))


if __name__ == "__main__":
    unittest.main()
