import unittest

from system.services.resources.process_monitor import (
    collect_process_statuses,
    make_not_running_status,
    summarize_processes,
)


REGISTRY = [
    {
        "component": "nexa_backend",
        "display_name": "NeXa Backend",
        "match_keywords": ["nexa_backend"],
        "notes": "Backend.",
    },
    {
        "component": "nexa_godot_lcd_ui",
        "display_name": "Godot LCD UI",
        "match_keywords": ["godot"],
        "notes": "LCD UI.",
    },
]


class ProcessMonitorTests(unittest.TestCase):
    def test_not_running_process_status_shape(self):
        status = make_not_running_status(REGISTRY[0])
        self.assertEqual(status["component"], "nexa_backend")
        self.assertEqual(status["status"], "not_running")
        self.assertIsNone(status["pid"])
        self.assertEqual(status["cpu_percent"], 0.0)
        self.assertEqual(status["memory_rss_mb"], 0.0)

    def test_process_statuses_use_fake_process_data(self):
        snapshots = [
            {"pid": 10, "command": "python nexa_backend", "rss_kb": 102400, "cpu_ticks": 20},
            {"pid": 11, "command": "godot nexa_godot_lcd_ui", "rss_kb": 204800, "cpu_ticks": 30},
        ]
        statuses = collect_process_statuses(
            registry=REGISTRY,
            process_snapshots=snapshots,
            cpu_percent_by_pid={10: 4.5, 11: 12.0},
            total_memory_kb=1024000,
        )
        self.assertEqual(statuses[0]["status"], "running")
        self.assertEqual(statuses[0]["memory_rss_mb"], 100.0)
        self.assertEqual(statuses[1]["cpu_percent"], 12.0)

    def test_resource_summary_picks_top_cpu_and_memory(self):
        processes = [
            {"component": "nexa_backend", "status": "running", "cpu_percent": 4.5, "memory_rss_mb": 100.0},
            {"component": "nexa_godot_lcd_ui", "status": "running", "cpu_percent": 12.0, "memory_rss_mb": 200.0},
            {"component": "nexa_web_panel", "status": "not_running", "cpu_percent": 0.0, "memory_rss_mb": 0.0},
        ]
        summary = summarize_processes(processes)
        self.assertEqual(summary["running_count"], 2)
        self.assertEqual(summary["not_running_count"], 1)
        self.assertEqual(summary["top_cpu_component"], "nexa_godot_lcd_ui")
        self.assertEqual(summary["top_memory_component"], "nexa_godot_lcd_ui")
        self.assertEqual(summary["total_nexa_cpu_percent"], 16.5)
        self.assertEqual(summary["total_nexa_memory_mb"], 300.0)


if __name__ == "__main__":
    unittest.main()

