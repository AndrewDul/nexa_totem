#!/usr/bin/env python3
"""Print fast CSI camera diagnostics."""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system.devices.sensors.camera_csi.camera_status import collect_camera_status
from system.services.diagnostics.reports import write_latest_report
from system.services.logging.runtime_logger import setup_runtime_logger


def main():
    parser = argparse.ArgumentParser(description="Check CSI camera status.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    parser.add_argument("--save-report", action="store_true", help="Save the latest JSON report.")
    args = parser.parse_args()

    logger = setup_runtime_logger("camera_status", console=False)
    logger.info("Starting fast CSI camera status check.")
    status = collect_camera_status()
    logger.info("CSI camera status check finished with status %s.", status["status"])

    if args.save_report:
        report_path = write_latest_report("camera_status", status, report_root=REPO_ROOT / "var/reports/diagnostics")
        logger.info("Saved CSI camera status report to %s.", report_path)

    if args.json:
        print(json.dumps(status, indent=2, sort_keys=True))
        return

    details = status["details"]
    print(f"CSI camera: {status['status']}")
    print(status["message"])
    print(f"Camera command: {details.get('camera_command') or 'not available'}")
    print(f"Camera detected: {details.get('camera_detected', False)}")
    print(f"Cameras found: {details.get('camera_count', 0)}")
    if details.get("camera_names"):
        print("Camera names: " + ", ".join(details["camera_names"]))


if __name__ == "__main__":
    main()
