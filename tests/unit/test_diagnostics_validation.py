import unittest

from system.services.diagnostics.validation import (
    make_validation_result,
    timed_validation,
    validation_status_from_component_status,
)


class DiagnosticsValidationTests(unittest.TestCase):
    def test_validation_result_shape(self):
        result = make_validation_result(
            "camera_capture",
            status="ok",
            message="Camera capture validation succeeded.",
            duration_ms=12,
            details={"output_path": "test.jpg"},
            source="camera_capture",
        )
        self.assertEqual(result["validation"], "camera_capture")
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["duration_ms"], 12)
        self.assertEqual(result["details"]["output_path"], "test.jpg")

    def test_timed_validation_includes_duration(self):
        result = timed_validation(
            "fake_validation",
            lambda: {"status": "ok", "message": "done", "details": {"value": 1}},
        )
        self.assertEqual(result["status"], "ok")
        self.assertIsInstance(result["duration_ms"], int)
        self.assertIn("started_at", result)
        self.assertIn("finished_at", result)

    def test_validation_status_from_component_status(self):
        self.assertEqual(validation_status_from_component_status({"status": "missing"}), "missing")
        self.assertEqual(validation_status_from_component_status({"status": "bad"}), "unknown")
        self.assertEqual(validation_status_from_component_status(None), "unknown")

    def test_timed_validation_handles_exception(self):
        def fail():
            raise RuntimeError("failed")

        result = timed_validation("broken", fail)
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["details"]["error"], "failed")


if __name__ == "__main__":
    unittest.main()

