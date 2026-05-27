#!/usr/bin/env python3
"""Run a safe ESP hardware pull client test."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from system.services.hardware_gateway.esp_pull_client import DEFAULT_ESP_STATE_URL, EspPullClient
from system.services.hardware_gateway.hardware_state import HardwareStateStore


def run_once(url: str, timeout: float) -> dict:
    store = HardwareStateStore()
    client = EspPullClient(url=url, timeout_seconds=timeout)
    return client.fetch_and_update(store)


def main() -> int:
    parser = argparse.ArgumentParser(description="Poll ESP8266 hardware state without changing Wi-Fi.")
    parser.add_argument("--url", default=DEFAULT_ESP_STATE_URL)
    parser.add_argument("--interval", type=float, default=1.0)
    parser.add_argument("--timeout", type=float, default=1.0)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    store = HardwareStateStore()
    client = EspPullClient(url=args.url, timeout_seconds=args.timeout)
    while True:
        result = client.fetch_and_update(store)
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        elif result.get("status") == "ok":
            state = result.get("state", {})
            print("ESP pull ok: connected=" + str(result.get("connected", False)) + " air=" + str(state.get("air_status", "UNKNOWN")))
        else:
            print("ESP pull error: " + str(result.get("error", "unknown")))
        if args.once:
            return 0 if result.get("status") == "ok" else 1
        time.sleep(max(0.1, args.interval))


if __name__ == "__main__":
    raise SystemExit(main())
