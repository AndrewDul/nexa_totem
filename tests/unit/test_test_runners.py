import tempfile
import unittest

from scripts.test.run_all_checks import run_all_checks
from scripts.test.run_unit_tests import run_unit_tests, save_unit_test_report


class FakeCompletedProcess:
    returncode = 0
    stdout = "tests passed"
    stderr = ""


class TestRunnerTests(unittest.TestCase):
    def test_unit_test_runner_returns_structured_result(self):
        def command_runner(command, check=False, capture_output=True, text=True, cwd=None):
            return FakeCompletedProcess()

        report = run_unit_tests(command_runner=command_runner)
        self.assertEqual(report["test_run"], "unit_tests")
        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["stdout"], "tests passed")

    def test_unit_test_report_can_be_saved(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            report = {"test_run": "unit_tests", "status": "ok"}
            paths = save_unit_test_report(report, temp_dir, save_report=True, save_history=True)

        self.assertIn("unit_tests", paths["latest"])
        self.assertIn("unit_tests", paths["history"])

    def test_run_all_checks_combines_fake_results(self):
        def unit_test_runner(report_root):
            return {
                "test_run": "unit_tests",
                "status": "ok",
                "message": "Unit tests passed.",
                "report_paths": {"latest": {}, "history": {}},
            }

        def diagnostics_runner(**kwargs):
            return {
                "diagnostics": "nexa_totem",
                "status": "ok",
                "message": "Diagnostics passed.",
                "report_paths": {"latest": {}, "history": {}},
            }

        report = run_all_checks(unit_test_runner=unit_test_runner, diagnostics_runner=diagnostics_runner)
        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["unit_tests"]["status"], "ok")
        self.assertEqual(report["diagnostics"]["status"], "ok")


if __name__ == "__main__":
    unittest.main()

