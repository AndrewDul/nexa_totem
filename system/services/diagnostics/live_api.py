"""Localhost-only live diagnostics API for NeXa ToTem."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from system.services.diagnostics.camera_preview import CameraPreviewWorker
from system.services.diagnostics.job_runner import (
    start_audio_check,
    start_benchmarks,
    start_camera_check,
    start_report,
)
from system.services.diagnostics.live_collectors import (
    audio_data,
    camera_data,
    control_center_data,
    logs_data,
    network_data,
    overview_data,
    process_data,
    reports_data,
    system_data,
)
from system.services.diagnostics.live_state import LiveState, ensure_runtime_dirs


HOST = "127.0.0.1"
PORT = 8769
STATE = LiveState()
PREVIEW = CameraPreviewWorker(STATE)

TTL_SECONDS = {
    "overview": 2,
    "system": 2,
    "processes": 1,
    "audio": 5,
    "camera": 5,
    "network": 8,
    "logs": 5,
    "reports": 10,
    "control-center": 2,
}


def cached(state, key, ttl, collector):
    value = state.cache.get(key, ttl)
    if value is not None:
        return value
    return state.cache.set(key, collector())


def _preview_for(state):
    return PREVIEW if state is STATE else CameraPreviewWorker(state)


def preview_status(state=STATE):
    return _preview_for(state).status()


def start_preview(state=STATE):
    return _preview_for(state).start()


def stop_preview(state=STATE):
    return _preview_for(state).stop()


class DiagnosticsHandler(BaseHTTPRequestHandler):
    server_version = "NeXaDiagnosticsAPI/0.1"

    def log_message(self, format, *args):  # noqa: A002
        return

    def _json(self, payload, status=200):
        body = json.dumps(payload, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _body_json(self):
        length = int(self.headers.get("Content-Length", "0") or "0")
        if not length:
            return {}
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {}

    def do_GET(self):  # noqa: N802
        path = urlparse(self.path).path
        try:
            if path == "/health":
                self._json({"status": "ok", "host": HOST, "port": PORT})
            elif path == "/api/overview":
                self._json(cached(STATE, "overview", TTL_SECONDS["overview"], lambda: overview_data(STATE)))
            elif path == "/api/system":
                self._json(cached(STATE, "system", TTL_SECONDS["system"], system_data))
            elif path == "/api/processes":
                self._json(cached(STATE, "processes", TTL_SECONDS["processes"], process_data))
            elif path == "/api/audio":
                self._json(cached(STATE, "audio", TTL_SECONDS["audio"], audio_data))
            elif path == "/api/camera":
                self._json(cached(STATE, "camera", TTL_SECONDS["camera"], lambda: camera_data(STATE)))
            elif path == "/api/network":
                self._json(cached(STATE, "network", TTL_SECONDS["network"], lambda: network_data(STATE)))
            elif path == "/api/logs":
                self._json(cached(STATE, "logs", TTL_SECONDS["logs"], logs_data))
            elif path == "/api/reports":
                self._json(cached(STATE, "reports", TTL_SECONDS["reports"], reports_data))
            elif path == "/api/control-center":
                self._json(cached(STATE, "control-center", TTL_SECONDS["control-center"], lambda: control_center_data(STATE)))
            elif path == "/api/benchmarks/status":
                self._json(STATE.get_job("benchmarks"))
            elif path == "/api/reports/status":
                self._json(STATE.get_job("reports"))
            elif path == "/api/camera/preview/status":
                self._json(preview_status(STATE))
            elif path == "/api/camera/preview/frame":
                self._frame()
            else:
                self._json({"status": "error", "error": "not_found"}, status=404)
        except Exception as exc:  # pragma: no cover - defensive API boundary
            self._json({"status": "error", "error": str(exc)}, status=500)

    def _frame(self):
        body = PREVIEW.latest_frame_bytes()
        if not body:
            self._json({"status": "pending", "message": "No frame available"}, status=404)
            return
        self.send_response(200)
        self.send_header("Content-Type", "image/jpeg")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):  # noqa: N802
        path = urlparse(self.path).path
        data = self._body_json()
        if path == "/api/benchmarks/run":
            self._json(start_benchmarks(STATE))
        elif path == "/api/reports/generate":
            self._json(start_report(STATE))
        elif path == "/api/camera/preview/start":
            self._json(start_preview(STATE))
        elif path == "/api/camera/preview/stop":
            self._json(stop_preview(STATE))
        elif path == "/api/control/quiet-mode":
            with STATE.lock:
                STATE.quiet_mode = bool(data.get("enabled", not STATE.quiet_mode))
            self._json({"status": "ok", "quiet_mode": STATE.quiet_mode})
        elif path == "/api/control/brightness":
            with STATE.lock:
                requested = data.get("brightness_percent", data.get("percent", STATE.brightness_percent))
                STATE.brightness_percent = max(0, min(100, int(requested)))
                STATE.brightness_auto = bool(data.get("auto_brightness", data.get("auto", STATE.brightness_auto)))
            self._json({"status": "planned", "dry_run": True, "brightness_percent": STATE.brightness_percent, "brightness_auto": STATE.brightness_auto})
        elif path == "/api/control/sound":
            with STATE.lock:
                requested = data.get("sound_percent", data.get("percent", STATE.sound_percent))
                if requested is not None:
                    STATE.sound_percent = max(0, min(100, int(requested)))
                STATE.sound_muted = bool(data.get("muted", STATE.sound_muted))
            self._json({"status": "planned", "dry_run": True, "sound_percent": STATE.sound_percent, "muted": STATE.sound_muted})
        elif path == "/api/control/remote-network":
            with STATE.lock:
                requested = data.get("state")
                STATE.remote_network_state = requested if requested in {"on", "off", "planned"} else "planned"
            self._json({"status": "planned", "dry_run": True, "remote_network_state": STATE.remote_network_state})
        elif path == "/api/camera/check/run":
            self._json(start_camera_check(STATE))
        elif path == "/api/audio/check/run":
            self._json(start_audio_check(STATE))
        else:
            self._json({"status": "error", "error": "not_found"}, status=404)


def make_server(host=HOST, port=PORT):
    ensure_runtime_dirs()
    return ThreadingHTTPServer((host, port), DiagnosticsHandler)


def serve_forever(host=HOST, port=PORT):
    server = make_server(host, port)
    try:
        server.serve_forever()
    finally:
        stop_preview(STATE)
        server.server_close()
