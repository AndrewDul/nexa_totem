#!/usr/bin/env python3
"""Print combined NeXa ToTem system diagnostics."""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system.devices.output.usb_speaker.speaker_status import collect_speaker_status
from system.devices.sensors.camera_csi.camera_status import collect_camera_status
from system.services.diagnostics.collector import make_system_status
from system.services.diagnostics.reports import write_json_report
from system.services.logging.runtime_logger import setup_runtime_logger
from system.services.system_health.pi_health import collect_pi_health


def collect_system_status():
    components = {
        "raspberry_pi": collect_pi_health(),
        "usb_speaker": collect_speaker_status(),
        "camera_csi": collect_camera_status(),
    }
    return make_system_status(components)


def main():
    parser = argparse.ArgumentParser(description="Check combined NeXa ToTem system status.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    parser.add_argument("--save-report", action="store_true", help="Save the latest JSON report.")
    args = parser.parse_args()

    logger = setup_runtime_logger("system_status", console=False)
    logger.info("Starting combined system status check.")
    status = collect_system_status()
    logger.info("Combined system status check finished with status %s.", status["status"])
    if args.save_report:
        report_path = write_json_report(status, REPO_ROOT / "var/reports/diagnostics/system_status_latest.json")
        logger.info("Saved combined system status report to %s.", report_path)

    if args.json:
        print(json.dumps(status, indent=2, sort_keys=True))
        return

    print(f"NeXa ToTem: {status['status']}")
    print(status["message"])
    for name, component in status["components"].items():
        print(f"- {name}: {component['status']} - {component['message']}")


if __name__ == "__main__":
    main()
