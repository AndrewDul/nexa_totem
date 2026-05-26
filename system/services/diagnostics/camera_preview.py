"""Low-FPS live camera preview worker for the diagnostics API."""

from __future__ import annotations

import importlib
import io
import shutil
import subprocess
import threading
import time

from system.services.diagnostics.live_state import PREVIEW_FRAME


STALE_TIMEOUT_SECONDS = 5
PREVIEW_FPS = 10
JPEG_SOI = b"\xff\xd8"
JPEG_EOI = b"\xff\xd9"


class CameraPreviewWorker:
    """Owns one live camera session while preview is enabled."""

    def __init__(self, state):
        self.state = state

    def start(self):
        with self.state.lock:
            self.state.preview_enabled = True
            self.state.preview_started_at = time.time()
            self.state.preview_last_request_at = time.time()
            self.state.preview_last_frame_at = None
            self.state.preview_frame_bytes = None
            self.state.preview_error = None
            self.state.preview_mode = "starting"
            self.state.preview_fps = PREVIEW_FPS
            self.state.preview_stop_event.clear()
            if self.state.preview_thread and self.state.preview_thread.is_alive():
                return self.status()
            self.state.preview_thread = threading.Thread(target=self._run_preview_session, daemon=True)
            self.state.preview_thread.start()
        return self.status()

    def stop(self):
        with self.state.lock:
            self.state.preview_enabled = False
            self.state.preview_stop_event.set()
            self.state.preview_last_frame_at = None
            self.state.preview_frame_bytes = None
            self.state.preview_mode = "off"
            process = getattr(self.state, "preview_process", None)
        self._terminate_process(process)
        return self.status(touch=False)

    def status(self, touch=True):
        now = time.time()
        with self.state.lock:
            if touch:
                self.state.preview_last_request_at = now
            enabled = self.state.preview_enabled
            age = round(now - self.state.preview_last_frame_at, 1) if enabled and self.state.preview_last_frame_at else None
            return {
                "status": "ok",
                "enabled": enabled,
                "mode": self.state.preview_mode if enabled else "off",
                "fps": self.state.preview_fps if enabled else 0,
                "frame_available": bool(enabled and self.state.preview_frame_bytes),
                "last_frame_age_seconds": age,
                "error": self.state.preview_error,
                "stale_timeout_seconds": STALE_TIMEOUT_SECONDS,
            }

    def latest_frame_bytes(self):
        with self.state.lock:
            self.state.preview_last_request_at = time.time()
            if not self.state.preview_enabled or not self.state.preview_frame_bytes:
                return None
            return bytes(self.state.preview_frame_bytes)

    @staticmethod
    def extract_jpeg_frames(buffer):
        frames = []
        remaining = buffer
        while True:
            start = remaining.find(JPEG_SOI)
            if start < 0:
                return frames, b""
            end = remaining.find(JPEG_EOI, start + 2)
            if end < 0:
                return frames, remaining[start:]
            frame = remaining[start:end + 2]
            frames.append(frame)
            remaining = remaining[end + 2:]

    def _run_preview_session(self):
        if shutil.which("rpicam-vid"):
            self._run_rpicam_vid_mjpeg()
        else:
            self._run_picamera2()

    def _run_rpicam_vid_mjpeg(self):
        command = [
            "rpicam-vid",
            "-t",
            "0",
            "--codec",
            "mjpeg",
            "--width",
            "320",
            "--height",
            "240",
            "--framerate",
            str(PREVIEW_FPS),
            "--nopreview",
            "-o",
            "-",
        ]
        process = None
        try:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            with self.state.lock:
                self.state.preview_process = process
                self.state.preview_mode = "rpicam_vid_mjpeg"
                self.state.preview_error = None
                self.state.preview_fps = PREVIEW_FPS
            pending = b""
            while not self.state.preview_stop_event.is_set():
                if self._stale_or_disabled():
                    break
                chunk = process.stdout.read(4096) if process.stdout else b""
                if not chunk:
                    if process.poll() is not None:
                        raise RuntimeError("rpicam-vid exited")
                    time.sleep(0.02)
                    continue
                pending += chunk
                frames, pending = self.extract_jpeg_frames(pending)
                for frame in frames:
                    self._store_frame(frame)
        except Exception as exc:
            with self.state.lock:
                self.state.preview_error = f"live_preview_unavailable: {exc}"
                self.state.preview_mode = "unavailable"
                self.state.preview_enabled = False
        finally:
            self._terminate_process(process)
            with self.state.lock:
                self.state.preview_process = None
                if self.state.preview_stop_event.is_set() or self.state.preview_mode == "unavailable":
                    self.state.preview_enabled = False
                    if self.state.preview_mode != "unavailable":
                        self.state.preview_mode = "off"

    def _run_picamera2(self):
        picamera = None
        try:
            module = importlib.import_module("picamera2")
            picamera_class = getattr(module, "Picamera2")
        except Exception as exc:
            with self.state.lock:
                self.state.preview_enabled = False
                self.state.preview_mode = "unavailable"
                self.state.preview_error = "live_preview_unavailable: Picamera2 not available"
                self.state.preview_stop_event.set()
            return

        try:
            picamera = picamera_class()
            config = picamera.create_preview_configuration(main={"size": (320, 240), "format": "RGB888"})
            picamera.configure(config)
            picamera.start()
            with self.state.lock:
                self.state.preview_mode = "picamera2"
                self.state.preview_error = None

            frame_interval = 1.0 / float(PREVIEW_FPS)
            while not self.state.preview_stop_event.wait(frame_interval):
                if self._stale_or_disabled():
                    break
                buffer = io.BytesIO()
                picamera.capture_file(buffer, format="jpeg")
                frame = buffer.getvalue()
                if not frame:
                    continue
                self._store_frame(frame)
        except Exception as exc:
            with self.state.lock:
                self.state.preview_error = f"live_preview_unavailable: {exc}"
                self.state.preview_mode = "unavailable"
                self.state.preview_enabled = False
        finally:
            if picamera is not None:
                try:
                    picamera.stop()
                except Exception:
                    pass
                try:
                    picamera.close()
                except Exception:
                    pass
            with self.state.lock:
                if self.state.preview_stop_event.is_set() or self.state.preview_mode == "unavailable":
                    self.state.preview_enabled = False
                    if self.state.preview_mode != "unavailable":
                        self.state.preview_mode = "off"

    def _stale_or_disabled(self):
        now = time.time()
        with self.state.lock:
            if not self.state.preview_enabled:
                return True
            last_request = self.state.preview_last_request_at or self.state.preview_started_at or now
            if now - last_request > STALE_TIMEOUT_SECONDS:
                self.state.preview_error = "Preview stopped after stale timeout"
                self.state.preview_enabled = False
                self.state.preview_stop_event.set()
                return True
        return False

    def _store_frame(self, frame):
        PREVIEW_FRAME.parent.mkdir(parents=True, exist_ok=True)
        try:
            PREVIEW_FRAME.write_bytes(frame)
        except OSError:
            pass
        with self.state.lock:
            self.state.preview_frame_bytes = frame
            self.state.preview_last_frame_at = time.time()
            self.state.preview_error = None

    @staticmethod
    def _terminate_process(process):
        if process is None:
            return
        if process.poll() is not None:
            return
        try:
            process.terminate()
            process.wait(timeout=1)
        except Exception:
            try:
                process.kill()
            except Exception:
                pass
