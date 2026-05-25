import unittest

from system.devices.output.usb_speaker.speaker_status import (
    collect_speaker_status,
    looks_like_usb_speaker,
    parse_aplay_devices,
)


APLAY_OUTPUT = """
**** List of PLAYBACK Hardware Devices ****
card 1: UACDemoV10 [UACDemoV1.0], device 0: USB Audio [USB Audio]
  Subdevices: 1/1
  Subdevice #0: subdevice #0
"""


class SpeakerStatusTests(unittest.TestCase):
    def test_parse_aplay_devices(self):
        devices = parse_aplay_devices(APLAY_OUTPUT)
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0]["card"], 1)
        self.assertEqual(devices[0]["card_name"], "UACDemoV1.0")
        self.assertEqual(devices[0]["device_name"], "USB Audio")

    def test_detecting_usb_speaker_like_names(self):
        self.assertTrue(looks_like_usb_speaker("UACDemoV1.0 USB Audio"))
        self.assertTrue(looks_like_usb_speaker("Desk Speaker"))
        self.assertFalse(looks_like_usb_speaker("Built-in Output"))

    def test_missing_speaker_returns_missing_or_warning_status(self):
        def command_runner(command, timeout=3):
            if command[:2] == ["aplay", "-l"]:
                return {"ok": True, "stdout": "", "stderr": "", "missing": False}
            return {"ok": False, "stdout": "", "stderr": "not running", "missing": False}

        status = collect_speaker_status(command_runner=command_runner)
        self.assertIn(status["status"], {"missing", "warning"})

    def test_missing_audio_commands_do_not_crash(self):
        def command_runner(command, timeout=3):
            return {"ok": False, "stdout": "", "stderr": "missing", "missing": True}

        status = collect_speaker_status(command_runner=command_runner)
        self.assertEqual(status["status"], "unknown")
        self.assertFalse(any(status["details"]["commands_available"].values()))


if __name__ == "__main__":
    unittest.main()
