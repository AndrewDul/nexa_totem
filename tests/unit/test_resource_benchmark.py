import unittest

from system.services.resources.benchmark import combine_benchmark_results, time_operation


class ResourceBenchmarkTests(unittest.TestCase):
    def test_benchmark_result_includes_duration(self):
        result = time_operation("quick_check", lambda: {"status": "ok", "message": "done"})
        self.assertEqual(result["benchmark"], "quick_check")
        self.assertEqual(result["status"], "ok")
        self.assertIsInstance(result["duration_ms"], int)

    def test_benchmark_handles_exceptions(self):
        def fail():
            raise RuntimeError("broken")

        result = time_operation("broken_check", fail)
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["details"]["error"], "broken")

    def test_combine_benchmark_results(self):
        report = combine_benchmark_results(
            [
                {"benchmark": "a", "status": "ok", "duration_ms": 10},
                {"benchmark": "b", "status": "ok", "duration_ms": 20},
            ]
        )
        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["summary"]["slowest_benchmark"], "b")
        self.assertEqual(report["summary"]["total_duration_ms"], 30)


if __name__ == "__main__":
    unittest.main()

