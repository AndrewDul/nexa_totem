#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
API_SCRIPT="$ROOT_DIR/scripts/run/run_diagnostics_api.py"
GODOT_SCRIPT="$ROOT_DIR/scripts/run/run_godot_ui_dev.sh"
NEXA_GODOT_RENDERING_DRIVER="${NEXA_GODOT_RENDERING_DRIVER:-opengl3}"
export NEXA_GODOT_RENDERING_DRIVER

API_PID=""

api_available() {
  python3 - <<'PY' >/dev/null 2>&1
import urllib.request
urllib.request.urlopen("http://127.0.0.1:8769/health", timeout=1)
PY
}

stop_preview() {
  python3 - <<'PY' >/dev/null 2>&1 || true
import urllib.request
urllib.request.urlopen("http://127.0.0.1:8769/api/camera/preview/stop", data=b"{}", timeout=1)
PY
}

cleanup() {
  stop_preview
  if [[ -n "$API_PID" ]] && kill -0 "$API_PID" 2>/dev/null; then
    kill "$API_PID" 2>/dev/null || true
    wait "$API_PID" 2>/dev/null || true
  fi
}

trap cleanup EXIT INT TERM

if api_available; then
  echo "Using existing NeXa diagnostics API on 127.0.0.1:8769."
else
  echo "Starting NeXa diagnostics API for Godot UI development."
  python3 "$API_SCRIPT" &
  API_PID="$!"

  for _ in 1 2 3 4 5; do
    if api_available; then
      break
    fi
    sleep 0.4
  done
fi

echo "Starting NeXa Godot LCD UI with diagnostics API in fixed 640x480 window."
echo "Using Godot Compatibility/OpenGL renderer for Raspberry Pi stability."
bash "$GODOT_SCRIPT"
