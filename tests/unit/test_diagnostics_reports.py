import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from system.services.diagnostics.reports import (
    list_history_reports,
    make_timestamped_report_name,
    prune_history_reports,
    read_latest_report,
    write_history_report,
    write_latest_report,
)


class DiagnosticsReportsTests(unittest.TestCase):
    def test_latest_report_write_and_read(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            report = {"status": "ok", "message": "test"}
            path = write_latest_report("system_status", report, report_root=temp_dir)
            read_back = read_latest_report("system_status", report_root=temp_dir)

        self.assertTrue(str(path).endswith("latest/system_status_latest.json"))
        self.assertEqual(read_back, report)

    def test_history_report_filename_creation(self):
        now = datetime(2026, 5, 25, 18, 45, 20, tzinfo=timezone.utc)
        name = make_timestamped_report_name("system status", now=now)
        self.assertEqual(name, "2026-05-25_18-45-20_system_status.json")

    def test_history_report_pruning(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            history_dir = Path(temp_dir) / "history"
            history_dir.mkdir(parents=True)
            for index in range(5):
                (history_dir / f"2026-05-25_18-45-2{index}_system_status.json").write_text("{}", encoding="utf-8")

            kept = prune_history_reports("system_status", report_root=temp_dir, keep=2)
            remaining = list_history_reports("system_status", report_root=temp_dir)

        self.assertEqual(len(kept), 2)
        self.assertEqual(len(remaining), 2)

    def test_write_history_report_uses_retention(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            history_dir = Path(temp_dir) / "history"
            history_dir.mkdir(parents=True)
            for index in range(3):
                (history_dir / f"2026-05-25_18-45-2{index}_unit_tests.json").write_text("{}", encoding="utf-8")
            write_history_report("unit_tests", {"status": "ok"}, report_root=temp_dir, history_limit=2)
            remaining = list_history_reports("unit_tests", report_root=temp_dir)

        self.assertEqual(len(remaining), 2)


if __name__ == "__main__":
    unittest.main()

