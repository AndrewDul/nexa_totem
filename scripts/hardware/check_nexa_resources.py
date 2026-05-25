#!/usr/bin/env python3
"""Check resource usage for known NeXa processes."""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system.services.diagnostics.reports import write_history_report, write_latest_report
from system.services.resources.resource_report import build_resource_report


def save_resource_report(report, report_root, save_report=False, save_history=False, history_limit=50):
    """Save resource reports when requested."""
    paths = {"latest": {}, "history": {}}
    if save_report:
        paths["latest"]["nexa_resources"] = str(write_latest_report("nexa_resources", report, report_root=report_root))
    if save_history:
        paths["history"]["nexa_resources"] = str(
            write_history_report("nexa_resources", report, report_root=report_root, history_limit=history_limit)
        )
    return paths


def main():
    parser = argparse.ArgumentParser(description="Check NeXa process resource usage.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    parser.add_argument("--save-report", action="store_true", help="Save latest JSON report.")
    parser.add_argument("--save-history", action="store_true", help="Save timestamped history report.")
    parser.add_argument("--history-limit", type=int, default=50, help="History reports to keep per report type.")
    args = parser.parse_args()

    report = build_resource_report()
    report["report_paths"] = save_resource_report(
        report,
        report_root=REPO_ROOT / "var/reports/diagnostics",
        save_report=args.save_report,
        save_history=args.save_history,
        history_limit=args.history_limit,
    )

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return

    snapshot = report["process_snapshot"]
    print(f"NeXa resources: {report['status']}")
    print(snapshot["message"])
    print("Component                  Status        CPU %   RAM MB")
    for process in snapshot["processes"]:
        print(
            f"{process['component']:<26} {process['status']:<12} "
            f"{process['cpu_percent']:>5.1f} {process['memory_rss_mb']:>8.1f}"
        )


if __name__ == "__main__":
    main()

