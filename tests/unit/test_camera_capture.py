import tempfile
import unittest
from pathlib import Path

from system.devices.sensors.camera_csi.camera_status import validate_camera_capture


class CameraCaptureTests(unittest.TestCase):
    def test_capture_returns_missing_when_still_command_is_missing(self):
        status = validate_camera_capture(command_finder=lambda command: None)
        self.assertEqual(status["status"], "missing")
        self.assertFalse(status["details"]["capture_attempted"])

    def test_capture_returns_ok_when_fake_runner_creates_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "camera_test.jpg"

            def command_runner(command, timeout=6):
                output_path.write_bytes(b"fake image data")
                return {"ok": True, "stdout": "saved", "stderr": "", "missing": False, "returncode": 0}

            status = validate_camera_capture(
                output_path=output_path,
                command_runner=command_runner,
                command_finder=lambda command: command == "rpicam-still",
            )

        self.assertEqual(status["status"], "ok")
        self.assertTrue(status["details"]["capture_succeeded"])
        self.assertEqual(status["details"]["output_path"], str(output_path))

    def test_capture_returns_error_when_command_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "camera_test.jpg"

            def command_runner(command, timeout=6):
                return {"ok": False, "stdout": "", "stderr": "capture failed", "missing": False, "returncode": 1}

            status = validate_camera_capture(
                output_path=output_path,
                command_runner=command_runner,
                command_finder=lambda command: command == "libcamera-still",
            )

        self.assertEqual(status["status"], "error")
        self.assertFalse(status["details"]["capture_succeeded"])
        self.assertIn("capture failed", status["details"]["capture_command_stderr"])


if __name__ == "__main__":
    unittest.main()

