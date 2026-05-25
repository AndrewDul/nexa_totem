#!/usr/bin/env python3
"""Run unit tests and fast diagnostics."""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts.hardware.run_diagnostics import collect_diagnostics
from scripts.test.run_unit_tests import run_unit_tests, save_unit_test_report
from system.services.diagnostics.status import combine_statuses, utc_now_iso


def run_all_checks(
    include_camera_capture=False,
    save_report=False,
    save_history=False,
    history_limit=50,
    report_root=REPO_ROOT / "var/reports/diagnostics",
    unit_test_runner=run_unit_tests,
    diagnostics_runner=collect_diagnostics,
):
    """Run unit tests and fast diagnostics with optional report saving."""
    unit_tests = unit_test_runner(report_root=report_root)
    unit_tests["report_paths"] = save_unit_test_report(
        unit_tests,
        report_root=report_root,
        save_report=save_report,
        save_history=save_history,
        history_limit=history_limit,
    )
    diagnostics = diagnostics_runner(
        include_camera_capture=include_camera_capture,
        save_report=save_report,
        save_history=save_history,
        history_limit=history_limit,
        report_root=report_root,
    )
    status = combine_statuses([unit_tests, diagnostics])
    return {
        "check_run": "all_checks",
        "status": status,
        "message": "All checks passed." if status == "ok" else "One or more checks need attention.",
        "unit_tests": unit_tests,
        "diagnostics": diagnostics,
        "checked_at": utc_now_iso(),
        "source": "run_all_checks",
    }


def main():
    parser = argparse.ArgumentParser(description="Run unit tests and fast diagnostics.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    parser.add_argument("--save-report", action="store_true", help="Save latest JSON reports.")
    parser.add_argument("--save-history", action="store_true", help="Save timestamped history reports.")
    parser.add_argument("--include-camera-capture", action="store_true", help="Run optional camera capture validation.")
    parser.add_argument("--history-limit", type=int, default=50, help="History reports to keep per report type.")
    args = parser.parse_args()

    report = run_all_checks(
        include_camera_capture=args.include_camera_capture,
        save_report=args.save_report,
        save_history=args.save_history,
        history_limit=args.history_limit,
    )

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"NeXa ToTem checks: {report['status']}")
        print(report["message"])

    raise SystemExit(0 if report["unit_tests"]["status"] == "ok" else 1)


if __name__ == "__main__":
    main()

