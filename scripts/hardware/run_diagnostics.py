#!/usr/bin/env python3
"""Run fast NeXa ToTem diagnostics."""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts.hardware.check_audio_output import play_test_sound
from system.devices.output.usb_speaker.speaker_status import collect_speaker_status
from system.devices.sensors.camera_csi.camera_status import validate_camera_capture
from system.services.diagnostics.collector import make_system_status
from system.services.diagnostics.reports import write_history_report, write_latest_report
from system.services.diagnostics.validation import timed_validation
from system.services.system_health.pi_health import collect_pi_health
from system.devices.sensors.camera_csi.camera_status import collect_camera_status


def run_audio_validation(play_sound=play_test_sound):
    """Run the optional audio validation sound."""
    def callback():
        played, message = play_sound()
        return {
            "status": "ok" if played else "warning",
            "message": message,
            "details": {"test_sound_played": played},
        }

    return timed_validation("audio_test", callback, source="audio_output")


def save_diagnostic_reports(report, report_root, save_latest=False, save_history=False, history_limit=50):
    """Save selected latest and history reports."""
    paths = {"latest": {}, "history": {}}
    if not save_latest and not save_history:
        return paths

    report_items = {"system_status": report["system_status"]}
    report_items.update(
        {
            "pi_health": report["components"]["raspberry_pi"],
            "audio_output": report["components"]["usb_speaker"],
            "camera_status": report["components"]["camera_csi"],
        }
    )
    if "camera_capture" in report["validations"]:
        report_items["camera_capture"] = report["validations"]["camera_capture"]
    if "audio_test" in report["validations"]:
        report_items["audio_test"] = report["validations"]["audio_test"]

    for report_type, item in report_items.items():
        if save_latest:
            paths["latest"][report_type] = str(write_latest_report(report_type, item, report_root=report_root))
        if save_history:
            paths["history"][report_type] = str(
                write_history_report(report_type, item, report_root=report_root, history_limit=history_limit)
            )
    return paths


def collect_diagnostics(
    pi_collector=collect_pi_health,
    speaker_collector=collect_speaker_status,
    camera_collector=collect_camera_status,
    camera_capture_validator=validate_camera_capture,
    audio_validator=run_audio_validation,
    include_camera_capture=False,
    include_audio_test=False,
    save_report=False,
    save_history=False,
    history_limit=50,
    report_root=REPO_ROOT / "var/reports/diagnostics",
):
    """Collect fast diagnostics and optional validations."""
    components = {
        "raspberry_pi": pi_collector(),
        "usb_speaker": speaker_collector(),
        "camera_csi": camera_collector(),
    }
    system_status = make_system_status(components)
    validations = {}

    if include_camera_capture:
        validations["camera_capture"] = timed_validation(
            "camera_capture",
            camera_capture_validator,
            source="camera_capture",
        )

    if include_audio_test:
        validations["audio_test"] = audio_validator()

    report = {
        "diagnostics": "nexa_totem",
        "status": system_status["status"],
        "message": system_status["message"],
        "system_status": system_status,
        "components": components,
        "validations": validations,
        "report_paths": {"latest": {}, "history": {}},
        "checked_at": system_status["checked_at"],
        "source": "run_diagnostics",
    }
    report["report_paths"] = save_diagnostic_reports(
        report,
        report_root=report_root,
        save_latest=save_report,
        save_history=save_history,
        history_limit=history_limit,
    )
    return report


def main():
    parser = argparse.ArgumentParser(description="Run fast NeXa ToTem diagnostics.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    parser.add_argument("--save-report", action="store_true", help="Save latest JSON reports.")
    parser.add_argument("--save-history", action="store_true", help="Save timestamped history reports.")
    parser.add_argument("--include-camera-capture", action="store_true", help="Run optional camera capture validation.")
    parser.add_argument("--include-audio-test", action="store_true", help="Run optional audio test sound.")
    parser.add_argument("--history-limit", type=int, default=50, help="History reports to keep per report type.")
    args = parser.parse_args()

    report = collect_diagnostics(
        include_camera_capture=args.include_camera_capture,
        include_audio_test=args.include_audio_test,
        save_report=args.save_report,
        save_history=args.save_history,
        history_limit=args.history_limit,
    )

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return

    print(f"NeXa ToTem diagnostics: {report['status']}")
    print(report["message"])
    for name, component in report["components"].items():
        print(f"- {name}: {component['status']} - {component['message']}")
    for name, validation in report["validations"].items():
        print(f"- {name}: {validation['status']} - {validation['message']}")


if __name__ == "__main__":
    main()
