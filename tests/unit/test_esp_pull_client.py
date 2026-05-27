import json
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from system.services.hardware_gateway.esp_pull_client import EspPullClient
from system.services.hardware_gateway.hardware_state import HardwareStateStore


SAMPLE = {
    "device": "nexa_totem_esp8266",
    "presence": 1,
    "distance_cm": 10,
    "joystick": "CENTER",
    "joystick_x": 517,
    "joystick_y": 503,
    "temperature_c": 28.9,
    "humidity_percent": 41.9,
    "pressure_hpa": 1016.6,
    "gas_kohms": 21.4,
    "air_status": "VENTILATE",
}


class FakeEspHandler(BaseHTTPRequestHandler):
    response_body = json.dumps(SAMPLE).encode("utf-8")
    response_status = 200
    response_delay = 0.0

    def log_message(self, format, *args):  # noqa: A002
        return

    def do_GET(self):  # noqa: N802
        if self.response_delay:
            time.sleep(self.response_delay)
        if self.path != "/api/state":
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(self.response_status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(self.response_body)))
        self.end_headers()
        try:
            self.wfile.write(self.response_body)
        except BrokenPipeError:
            pass


class EspServer:
    def __init__(self, body, delay=0.0):
        self.body = body
        self.delay = delay
        self.server = None
        self.thread = None

    def __enter__(self):
        class Handler(FakeEspHandler):
            response_body = self.body
            response_delay = self.delay

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        host, port = self.server.server_address
        return f"http://{host}:{port}/api/state"

    def __exit__(self, exc_type, exc, tb):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)


class EspPullClientTests(unittest.TestCase):
    def test_fetch_valid_json_from_fake_server(self):
        with EspServer(json.dumps(SAMPLE).encode("utf-8")) as url:
            result = EspPullClient(url=url).fetch_once()
        self.assertEqual(result["status"], "ok")
        self.assertTrue(result["connected"])
        self.assertEqual(result["payload"]["temperature_c"], 28.9)

    def test_bad_json_returns_error(self):
        with EspServer(b"{bad") as url:
            result = EspPullClient(url=url).fetch_once()
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error"], "bad_json")

    def test_offline_url_returns_error(self):
        result = EspPullClient(url="http://127.0.0.1:9/api/state", timeout_seconds=0.1).fetch_once()
        self.assertEqual(result["status"], "error")
        self.assertIn(result["error"], {"network_error", "timeout"})

    def test_timeout_handled(self):
        with EspServer(json.dumps(SAMPLE).encode("utf-8"), delay=0.2) as url:
            result = EspPullClient(url=url, timeout_seconds=0.05).fetch_once()
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error"], "timeout")

    def test_state_normalized_into_store(self):
        with EspServer(json.dumps(SAMPLE).encode("utf-8")) as url:
            store = HardwareStateStore()
            result = EspPullClient(url=url).fetch_and_update(store)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["source"], "esp_pull")
        self.assertTrue(result["connected"])
        self.assertEqual(result["state"]["joystick"], "CENTER")
        self.assertEqual(result["state"]["advice"], "Open the window")


if __name__ == "__main__":
    unittest.main()
