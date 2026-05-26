"""Shared live diagnostics state and TTL cache."""

from __future__ import annotations

import threading
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
VAR_DIR = REPO_ROOT / "var"
REPORT_DIR = VAR_DIR / "reports" / "diagnostics" / "latest"
LOG_DIR = VAR_DIR / "log"
CACHE_DIR = VAR_DIR / "cache"
PREVIEW_DIR = CACHE_DIR / "camera_preview"
PREVIEW_FRAME = PREVIEW_DIR / "latest.jpg"


class TTLCache:
    """Small thread-safe TTL cache for diagnostics payloads."""

    def __init__(self):
        self._lock = threading.Lock()
        self._items = {}

    def get(self, key, ttl_seconds):
        now = time.monotonic()
        with self._lock:
            item = self._items.get(key)
            if not item:
                return None
            if now - item["created_at"] > ttl_seconds:
                return None
            return item["value"]

    def set(self, key, value):
        with self._lock:
            self._items[key] = {"created_at": time.monotonic(), "value": value}
        return value


class LiveState:
    """Mutable API state for prototype controls and background jobs."""

    def __init__(self):
        self.cache = TTLCache()
        self.lock = threading.RLock()
        self.quiet_mode = False
        self.brightness_percent = 65
        self.brightness_auto = False
        self.sound_percent = None
        self.sound_muted = False
        self.remote_network_state = "planned"
        self.preview_enabled = False
        self.preview_started_at = None
        self.preview_last_frame_at = None
        self.preview_error = None
        self.preview_mode = "off"
        self.preview_fps = 5
        self.preview_frame_bytes = None
        self.preview_last_request_at = None
        self.preview_process = None
        self.preview_thread = None
        self.preview_stop_event = threading.Event()
        self.jobs = {
            "benchmarks": {"status": "idle", "result": None, "error": None},
            "reports": {"status": "idle", "result": None, "error": None},
            "camera_check": {"status": "idle", "result": None, "error": None},
            "audio_check": {"status": "idle", "result": None, "error": None},
        }

    def set_job(self, name, status, result=None, error=None):
        with self.lock:
            self.jobs[name] = {"status": status, "result": result, "error": error}

    def get_job(self, name):
        with self.lock:
            return dict(self.jobs.get(name, {"status": "idle", "result": None, "error": None}))


def ensure_runtime_dirs():
    for path in (REPORT_DIR, LOG_DIR, CACHE_DIR, PREVIEW_DIR):
        path.mkdir(parents=True, exist_ok=True)
