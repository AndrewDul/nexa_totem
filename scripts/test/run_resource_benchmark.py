#!/usr/bin/env python3
"""Run quick resource benchmarks for NeXa diagnostics checks."""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts.hardware.check_system_status import collect_system_status
from system.devices.output.usb_speaker.speaker_status import collect_speaker_status
from system.devices.sensors.camera_csi.camera_status import collect_camera_status
from system.services.diagnostics.panel_data import build_diagnostic_panel_data
from system.services.diagnostics.reports import write_history_report, write_latest_report
from system.services.resources.benchmark import combine_benchmark_results, time_operation
from system.services.system_health.pi_health import collect_pi_health


def run_resource_benchmarks(
    pi_check=collect_pi_health,
    speaker_check=collect_speaker_status,
    camera_check=collect_camera_status,
    system_check=collect_system_status,
    panel_data_builder=build_diagnostic_panel_data,
):
    """Run quick benchmarks for existing diagnostics."""
    results = [
        time_operation("pi_health_check", pi_check, source="pi_health"),
        time_operation("speaker_status_check", speaker_check, source="speaker_status"),
        time_operation("camera_status_check", camera_check, source="camera_status"),
        time_operation("system_status_check", system_check, source="system_status"),
        time_operation("diagnostic_panel_data_build", panel_data_builder, source="diagnostic_panel_data"),
    ]
    return combine_benchmark_results(results)


def save_benchmark_report(report, report_root, save_report=False, save_history=False, history_limit=50):
    """Save benchmark reports when requested."""
    paths = {"latest": {}, "history": {}}
    if save_report:
        paths["latest"]["resource_benchmark"] = str(
            write_latest_report("resource_benchmark", report, report_root=report_root)
        )
    if save_history:
        paths["history"]["resource_benchmark"] = str(
            write_history_report("resource_benchmark", report, report_root=report_root, history_limit=history_limit)
        )
    return paths


def main():
    parser = argparse.ArgumentParser(description="Run quick NeXa resource benchmarks.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    parser.add_argument("--save-report", action="store_true", help="Save latest JSON report.")
    parser.add_argument("--save-history", action="store_true", help="Save timestamped history report.")
    parser.add_argument("--history-limit", type=int, default=50, help="History reports to keep per report type.")
    args = parser.parse_args()

    report = run_resource_benchmarks()
    report["report_paths"] = save_benchmark_report(
        report,
        report_root=REPO_ROOT / "var/reports/diagnostics",
        save_report=args.save_report,
        save_history=args.save_history,
        history_limit=args.history_limit,
    )

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return

    print(f"Resource benchmarks: {report['status']}")
    for result in report["benchmarks"]:
        print(f"- {result['benchmark']}: {result['status']} - {result['duration_ms']} ms")


if __name__ == "__main__":
    main()

