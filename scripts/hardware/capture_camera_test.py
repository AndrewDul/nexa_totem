#!/usr/bin/env python3
"""Run optional CSI camera capture validation."""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system.devices.sensors.camera_csi.camera_status import DEFAULT_CAPTURE_PATH, validate_camera_capture
from system.services.diagnostics.reports import write_json_report
from system.services.logging.runtime_logger import setup_runtime_logger


def main():
    parser = argparse.ArgumentParser(description="Run optional CSI camera capture validation.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    parser.add_argument("--save-report", action="store_true", help="Save the latest JSON report.")
    args = parser.parse_args()

    output_path = REPO_ROOT / DEFAULT_CAPTURE_PATH
    logger = setup_runtime_logger("camera_capture", console=False)
    logger.info("Starting CSI camera capture validation.")
    status = validate_camera_capture(output_path=output_path)
    logger.info("CSI camera capture validation finished with status %s.", status["status"])

    if args.save_report:
        report_path = write_json_report(status, REPO_ROOT / "var/reports/diagnostics/camera_capture_latest.json")
        logger.info("Saved CSI camera capture report to %s.", report_path)

    if args.json:
        print(json.dumps(status, indent=2, sort_keys=True))
        return

    details = status["details"]
    print(f"CSI camera capture: {status['status']}")
    print(status["message"])
    print(f"Capture command: {details.get('capture_command') or 'not available'}")
    print(f"Capture attempted: {details.get('capture_attempted', False)}")
    print(f"Capture succeeded: {details.get('capture_succeeded', False)}")
    if details.get("output_path"):
        print(f"Output path: {details['output_path']}")


if __name__ == "__main__":
    main()

