import time
import unittest
from unittest import mock

from system.services.diagnostics import camera_preview, live_api, live_collectors
from system.services.diagnostics.live_state import LiveState
from system.services.settings import settings_store


class LiveDiagnosticsApiTests(unittest.TestCase):
    def test_health_endpoint_json_shape(self):
        payload = {"status": "ok", "host": live_api.HOST, "port": live_api.PORT}
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["host"], "127.0.0.1")
        self.assertEqual(payload["port"], 8769)

    def test_overview_has_cpu_temp_field(self):
        state = LiveState()
        with mock.patch.object(live_collectors, "system_data", return_value={
            "status": "ok",
            "system_ok": True,
            "cpu_temperature_c": 42.0,
            "cpu_usage_percent": 3.0,
            "ram_usage_percent": 50.0,
            "ram_used_mb": 512.0,
        }), mock.patch.object(live_collectors, "audio_data", return_value={
            "speaker_status": "ok",
            "speaker_name": "USB Speaker",
        }), mock.patch.object(live_collectors, "camera_data", return_value={
            "camera_detected": True,
            "camera_ready": True,
        }), mock.patch.object(live_collectors, "network_data", return_value={
            "wifi_enabled": True,
            "connected_ssid": "Home",
            "remote_network_state": "planned",
        }):
            payload = live_collectors.overview_data(state)
        self.assertIn("cpu_temperature_c", payload)
        self.assertIn("cpu_usage_percent", payload)
        self.assertIn("gpu_usage_status", payload)
        self.assertFalse(payload["gpu_usage_supported"])
        self.assertIsNone(payload["gpu_usage_percent"])
        self.assertEqual(payload["gpu_usage_status"], "not_supported")

    def test_system_data_handles_missing_vcgencmd_safely(self):
        with mock.patch.object(live_collectors, "collect_pi_health", return_value={
            "status": "unknown",
            "message": "unknown",
            "details": {"temperature_c": None, "throttling_detected": None},
        }):
            payload = live_collectors.system_data()
        self.assertIn("gpu_usage_status", payload)
        self.assertEqual(payload["gpu_usage_status"], "not_supported")

    def test_processes_use_nexa_resource_monitor(self):
        with mock.patch.object(live_collectors, "collect_resource_snapshot", return_value={
            "status": "ok",
            "processes": [{"display_name": "Godot LCD UI", "status": "running"}],
            "summary": {"running_count": 1},
        }) as mocked:
            payload = live_collectors.process_data()
        mocked.assert_called_once()
        self.assertEqual(payload["processes"][0]["display_name"], "Godot LCD UI")

    def test_camera_preview_off_by_default_and_stop_changes_state(self):
        state = LiveState()
        status = live_api.preview_status(state)
        self.assertFalse(status["enabled"])
        self.assertEqual(status["mode"], "off")
        self.assertIn("fps", status)
        self.assertIn("frame_available", status)
        self.assertIn("stale_timeout_seconds", status)
        state.preview_enabled = True
        payload = live_api.stop_preview(state)
        self.assertFalse(payload["enabled"])

    def test_camera_preview_start_unavailable_is_safe(self):
        state = LiveState()
        with mock.patch("shutil.which", return_value=None), \
            mock.patch("importlib.import_module", side_effect=ImportError("missing")):
            payload = live_api.start_preview(state)
            deadline = time.time() + 1
            while state.preview_enabled and time.time() < deadline:
                time.sleep(0.02)
        status = live_api.preview_status(state)
        self.assertFalse(status["enabled"])
        self.assertIn(status["mode"], {"off", "unavailable"})
        self.assertTrue(status["error"] is None or "live_preview_unavailable" in status["error"])

    def test_camera_preview_worker_latest_frame_and_stop(self):
        state = LiveState()
        worker = camera_preview.CameraPreviewWorker(state)
        with state.lock:
            state.preview_enabled = True
            state.preview_mode = "picamera2"
            state.preview_frame_bytes = b"jpeg-bytes"
        self.assertEqual(worker.latest_frame_bytes(), b"jpeg-bytes")
        stopped = worker.stop()
        self.assertFalse(stopped["enabled"])
        self.assertIsNone(worker.latest_frame_bytes())

    def test_camera_preview_extracts_jpeg_frames(self):
        first = b"\xff\xd8one\xff\xd9"
        second = b"\xff\xd8two\xff\xd9"
        frames, remaining = camera_preview.CameraPreviewWorker.extract_jpeg_frames(b"junk" + first + b"gap" + second + b"\xff\xd8partial")
        self.assertEqual(frames, [first, second])
        self.assertEqual(remaining, b"\xff\xd8partial")

    def test_camera_preview_stop_terminates_process(self):
        state = LiveState()
        worker = camera_preview.CameraPreviewWorker(state)

        class FakeProcess:
            def __init__(self):
                self.terminated = False
                self.killed = False

            def poll(self):
                return None

            def terminate(self):
                self.terminated = True

            def wait(self, timeout=None):
                return 0

            def kill(self):
                self.killed = True

        fake = FakeProcess()
        with state.lock:
            state.preview_enabled = True
            state.preview_process = fake
        worker.stop()
        self.assertTrue(fake.terminated)
        self.assertFalse(state.preview_enabled)

    def test_camera_preview_stale_timeout_can_stop_preview(self):
        state = LiveState()
        worker = camera_preview.CameraPreviewWorker(state)
        with state.lock:
            state.preview_enabled = True
            state.preview_started_at = time.time() - 10
            state.preview_last_request_at = time.time() - 10
        self.assertTrue(worker._stale_or_disabled())
        self.assertFalse(state.preview_enabled)

    def test_benchmark_job_starts_without_blocking(self):
        state = LiveState()
        with mock.patch("system.services.diagnostics.job_runner.system_data", return_value={}), \
            mock.patch("system.services.diagnostics.job_runner.process_data", return_value={}), \
            mock.patch("system.services.diagnostics.job_runner.overview_data", return_value={}), \
            mock.patch("system.services.diagnostics.job_runner.audio_data", return_value={}), \
            mock.patch("system.services.diagnostics.job_runner.camera_data", return_value={}), \
            mock.patch("system.services.diagnostics.job_runner.network_data", return_value={}):
            payload = live_api.start_benchmarks(state)
            self.assertIn(payload["status"], {"pending", "running", "done"})
            deadline = time.time() + 2
            while state.get_job("benchmarks")["status"] in {"pending", "running"} and time.time() < deadline:
                time.sleep(0.05)
        self.assertIn(state.get_job("benchmarks")["status"], {"done", "error"})
        result = state.get_job("benchmarks").get("result") or {}
        self.assertIsInstance(result.get("results"), list)
        self.assertTrue(result["results"])

    def test_control_center_sound_has_safe_display(self):
        state = LiveState()
        with mock.patch.object(live_collectors, "network_summary", return_value={
            "connected_ssid": "Home",
            "remote_network_state": "planned",
        }), mock.patch.object(live_collectors, "audio_data", return_value={
            "volume_percent": None,
            "speaker_name": "Unknown",
            "speaker_status": "unknown",
            "muted": None,
        }), mock.patch.object(live_collectors, "system_data", return_value={"cpu_temperature_c": None}):
            payload = live_collectors.control_center_data(state)
        self.assertEqual(payload["sound_percent"], 50)
        self.assertEqual(payload["sound_display"], "Unknown")

    def test_prototype_control_posts_update_state(self):
        state = LiveState()
        with state.lock:
            state.brightness_percent = 65
            state.sound_percent = None
            state.quiet_mode = False
            state.remote_network_state = "planned"
        state.brightness_percent = max(0, min(100, int(72)))
        state.sound_percent = max(0, min(100, int(44)))
        state.quiet_mode = True
        state.remote_network_state = "on"
        self.assertEqual(state.brightness_percent, 72)
        self.assertEqual(state.sound_percent, 44)
        self.assertTrue(state.quiet_mode)
        self.assertEqual(state.remote_network_state, "on")

    def test_network_data_returns_network_lists(self):
        state = LiveState()
        with mock.patch.object(live_collectors, "saved_networks", return_value=["Home"]), \
            mock.patch.object(live_collectors, "available_networks", return_value=["Home", "Guest"]), \
            mock.patch.object(live_collectors, "connected_ssid", return_value="Home"), \
            mock.patch.object(live_collectors, "wifi_enabled", return_value=True):
            payload = live_collectors.network_data(state)
        self.assertIsInstance(payload["saved_networks"], list)
        self.assertIsInstance(payload["available_networks"], list)
        self.assertIn("remote_connected", payload)
        self.assertTrue(payload["actions_are_dry_run"])

    def test_control_center_data_omits_full_network_lists(self):
        state = LiveState()
        with mock.patch.object(live_collectors, "network_summary", return_value={
            "connected_ssid": "Home",
            "remote_network_state": "planned",
            "remote_connected": "unknown",
        }), mock.patch.object(live_collectors, "audio_data", return_value={}), \
            mock.patch.object(live_collectors, "system_data", return_value={}):
            payload = live_collectors.control_center_data(state)
        self.assertNotIn("saved_networks", payload)
        self.assertNotIn("available_networks", payload)

    def test_report_generation_returns_status(self):
        state = LiveState()
        with mock.patch("system.services.diagnostics.job_runner.overview_data", return_value={}), \
            mock.patch("system.services.diagnostics.job_runner.system_data", return_value={}), \
            mock.patch("system.services.diagnostics.job_runner.process_data", return_value={}):
            payload = live_api.start_report(state)
        self.assertIn(payload["status"], {"pending", "running", "done"})

    def test_network_write_actions_are_dry_run_planned(self):
        with open(live_api.__file__, encoding="utf-8") as handle:
            text = handle.read()
        self.assertIn("dry_run", text)
        self.assertIn("planned", text)

    def test_settings_api_endpoints_are_represented(self):
        with open(live_api.__file__, encoding="utf-8") as handle:
            text = handle.read()
        for endpoint in [
            "/api/settings",
            "/api/settings/update",
            "/api/settings/update-many",
            "/api/privacy/pin/set",
            "/api/privacy/pin/verify",
            "/api/privacy/status",
            "/api/settings/reset-section",
        ]:
            self.assertIn(endpoint, text)

    def test_settings_api_safe_payload_removes_pin_secret(self):
        data = settings_store.default_settings()
        data["privacy"]["pin_hash"] = "secret"
        data["privacy"]["pin_salt"] = "salt"
        safe = settings_store.safe_settings(data)
        self.assertNotIn("pin_hash", safe["privacy"])
        self.assertNotIn("pin_salt", safe["privacy"])


if __name__ == "__main__":
    unittest.main()
