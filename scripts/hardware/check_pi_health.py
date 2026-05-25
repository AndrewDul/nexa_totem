#!/usr/bin/env python3
"""Print Raspberry Pi health diagnostics."""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system.services.system_health.pi_health import collect_pi_health


def main():
    parser = argparse.ArgumentParser(description="Check Raspberry Pi health.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    args = parser.parse_args()

    status = collect_pi_health()
    if args.json:
        print(json.dumps(status, indent=2, sort_keys=True))
        return

    print(f"Raspberry Pi: {status['status']}")
    print(status["message"])
    details = status["details"]
    if details.get("temperature_c") is not None:
        print(f"Temperature: {details['temperature_c']} C")
    if details.get("throttled_raw"):
        print(f"Throttled: {details['throttled_raw']}")


if __name__ == "__main__":
    main()
