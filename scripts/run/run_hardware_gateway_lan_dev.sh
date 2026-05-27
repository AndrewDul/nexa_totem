#!/usr/bin/env bash
set -euo pipefail

# Use this only when you want ESP8266 on the local network to reach the Pi.
# This does not change Wi-Fi or network configuration.
python3 scripts/run/run_hardware_gateway_dev.py --host 0.0.0.0 --port 8080
