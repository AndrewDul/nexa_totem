#!/usr/bin/env python3
"""Run NeXa ToTem unit tests with structured output."""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system.services.diagnostics.reports import write_history_report, write_latest_report
from system.services.diagnostics.status import utc_now_iso


def run_unit_tests(command_runner=subprocess.run, report_root=REPO_ROOT / "var/reports/diagnostics"):
    """Run unit tests and return a structured report."""
    started_at = utc_now_iso()
    start = time.monotonic()
    command = [sys.executable, "-m", "unittest", "discover", "-s", "tests/unit"]
    result = command_runner(command, check=False, capture_output=True, text=True, cwd=str(REPO_ROOT))
    finished_at = utc_now_iso()
    status = "ok" if result.returncode == 0 else "error"
    return {
        "test_run": "unit_tests",
        "status": status,
        "message": "Unit tests passed." if status == "ok" else "Unit tests failed.",
        "command": command,
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_ms": int((time.monotonic() - start) * 1000),
        "report_paths": {"latest": {}, "history": {}},
        "source": "run_unit_tests",
    }


def save_unit_test_report(report, report_root, save_report=False, save_history=False, history_limit=50):
    """Save latest or history unit test reports."""
    paths = {"latest": {}, "history": {}}
    if save_report:
        paths["latest"]["unit_tests"] = str(write_latest_report("unit_tests", report, report_root=report_root))
    if save_history:
        paths["history"]["unit_tests"] = str(
            write_history_report("unit_tests", report, report_root=report_root, history_limit=history_limit)
        )
    return paths


def main():
    parser = argparse.ArgumentParser(description="Run NeXa ToTem unit tests.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    parser.add_argument("--save-report", action="store_true", help="Save latest JSON report.")
    parser.add_argument("--save-history", action="store_true", help="Save timestamped history report.")
    parser.add_argument("--history-limit", type=int, default=50, help="History reports to keep per report type.")
    args = parser.parse_args()

    report = run_unit_tests()
    report["report_paths"] = save_unit_test_report(
        report,
        report_root=REPO_ROOT / "var/reports/diagnostics",
        save_report=args.save_report,
        save_history=args.save_history,
        history_limit=args.history_limit,
    )

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Unit tests: {report['status']}")
        print(report["message"])

    raise SystemExit(0 if report["status"] == "ok" else 1)


if __name__ == "__main__":
    main()

