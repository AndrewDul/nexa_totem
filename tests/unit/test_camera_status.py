import unittest

from system.devices.sensors.camera_csi.camera_status import (
    collect_camera_status,
    parse_list_cameras_output,
    select_camera_command,
)


ONE_CAMERA_OUTPUT = """
Available cameras
-----------------
0 : imx708_wide [4608x2592 10-bit RGGB] (/base/axi/pcie@120000/rp1/i2c@88000/imx708@1a)
    Modes: 'SRGGB10_CSI2P' : 1536x864 [120.13 fps]
"""

NO_CAMERA_OUTPUT = """
Available cameras
-----------------
No cameras available!
"""


class CameraStatusTests(unittest.TestCase):
    def test_command_selection_prefers_rpicam_hello(self):
        def command_finder(command):
            return command in {"rpicam-hello", "libcamera-hello"}

        self.assertEqual(select_camera_command(command_finder=command_finder), "rpicam-hello")

    def test_command_selection_falls_back_to_libcamera_hello(self):
        def command_finder(command):
            return command == "libcamera-hello"

        self.assertEqual(select_camera_command(command_finder=command_finder), "libcamera-hello")

    def test_command_selection_returns_none_when_missing(self):
        self.assertIsNone(select_camera_command(command_finder=lambda command: None))

    def test_parse_one_detected_camera(self):
        parsed = parse_list_cameras_output(ONE_CAMERA_OUTPUT)
        self.assertTrue(parsed["camera_detected"])
        self.assertEqual(parsed["camera_count"], 1)
        self.assertEqual(parsed["camera_names"], ["imx708_wide"])

    def test_parse_no_cameras(self):
        parsed = parse_list_cameras_output(NO_CAMERA_OUTPUT)
        self.assertFalse(parsed["camera_detected"])
        self.assertEqual(parsed["camera_count"], 0)

    def test_parse_unexpected_output(self):
        parsed = parse_list_cameras_output("unexpected output")
        self.assertFalse(parsed["camera_detected"])
        self.assertEqual(parsed["camera_names"], [])

    def test_collect_status_returns_ok_when_camera_is_listed(self):
        def command_runner(command, timeout=2):
            self.assertEqual(command, ["rpicam-hello", "--list-cameras"])
            return {"ok": True, "stdout": ONE_CAMERA_OUTPUT, "stderr": "", "missing": False, "returncode": 0}

        status = collect_camera_status(
            command_runner=command_runner,
            command_finder=lambda command: command == "rpicam-hello",
        )
        self.assertEqual(status["status"], "ok")
        self.assertTrue(status["details"]["camera_detected"])

    def test_collect_status_returns_missing_when_no_camera_is_listed(self):
        def command_runner(command, timeout=2):
            return {"ok": True, "stdout": NO_CAMERA_OUTPUT, "stderr": "", "missing": False, "returncode": 0}

        status = collect_camera_status(
            command_runner=command_runner,
            command_finder=lambda command: command == "libcamera-hello",
        )
        self.assertEqual(status["status"], "missing")
        self.assertFalse(status["details"]["camera_detected"])

    def test_collect_status_returns_error_when_command_fails(self):
        def command_runner(command, timeout=2):
            return {"ok": False, "stdout": "", "stderr": "camera service failed", "missing": False, "returncode": 1}

        status = collect_camera_status(
            command_runner=command_runner,
            command_finder=lambda command: command == "rpicam-hello",
        )
        self.assertEqual(status["status"], "error")
        self.assertIn("camera service failed", status["details"]["list_command_stderr"])

    def test_collect_status_does_not_crash_when_command_is_missing(self):
        status = collect_camera_status(command_finder=lambda command: None)
        self.assertEqual(status["status"], "unknown")
        self.assertIsNone(status["details"]["camera_command"])

    def test_normal_status_check_does_not_run_capture_command(self):
        commands = []

        def command_runner(command, timeout=2):
            commands.append(command)
            return {"ok": True, "stdout": ONE_CAMERA_OUTPUT, "stderr": "", "missing": False, "returncode": 0}

        collect_camera_status(
            command_runner=command_runner,
            command_finder=lambda command: command in {"rpicam-hello", "rpicam-still"},
        )
        self.assertEqual(commands, [["rpicam-hello", "--list-cameras"]])


if __name__ == "__main__":
    unittest.main()

