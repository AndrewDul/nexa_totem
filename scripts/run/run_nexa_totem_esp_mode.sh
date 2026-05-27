#!/usr/bin/env bash
set -u

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR" || exit 1

CONFIRM_VALUE="${CONFIRM_NEXA_ESP_WIFI_SWITCH:-}"
ESP_WIFI_STARTED=0

api_available() {
  python3 - <<'PY' >/dev/null 2>&1
import urllib.request
urllib.request.urlopen("http://127.0.0.1:8769/health", timeout=1)
PY
}

cleanup() {
  if [[ "$ESP_WIFI_STARTED" != "1" ]]; then
    return
  fi
  echo "Stopping NeXa ESP mode..."
  echo "Trying to reconnect previous Wi-Fi..."
  if ! python3 scripts/network/reconnect_home_wifi.py --apply --i-understand-this-changes-network; then
    echo "Reconnect failed. Use Raspberry Pi network menu or run reconnect manually."
    echo "Manual command:"
    echo "python3 scripts/network/reconnect_home_wifi.py --apply --i-understand-this-changes-network"
  fi
}

echo "ESP mode will disconnect Raspberry Pi from normal Wi-Fi/internet and connect to NeXa-ESP."

if [[ "$CONFIRM_VALUE" != "RUN" ]]; then
  echo "No Wi-Fi changes were made."
  echo "To start NeXa ESP mode, run:"
  echo "CONFIRM_NEXA_ESP_WIFI_SWITCH=RUN bash scripts/run/run_nexa_totem_esp_mode.sh"
  exit 1
fi

if api_available; then
  echo "A NeXa diagnostics API is already running on 127.0.0.1:8769."
  echo "Stop the existing API/UI first so ESP mode can start a fresh pull-mode API."
  echo "No Wi-Fi changes were made."
  exit 1
fi

trap cleanup EXIT INT TERM

echo "Connecting Raspberry Pi Wi-Fi to NeXa-ESP..."
if ! python3 scripts/network/connect_to_esp_network.py --apply --i-understand-this-will-disconnect-internet; then
  echo "Could not connect to NeXa-ESP. No NeXa UI was started."
  exit 1
fi
ESP_WIFI_STARTED=1

export NEXA_HARDWARE_MODE=pull_esp_server
export NEXA_ESP_STATE_URL=http://192.168.4.1/api/state
export NEXA_ESP_POLL_INTERVAL_SECONDS=0.2

echo "Starting NeXa in ESP pull mode."
echo "ESP state URL: $NEXA_ESP_STATE_URL"
bash scripts/run/run_godot_ui_with_api_dev.sh
RUN_STATUS=$?

exit "$RUN_STATUS"
