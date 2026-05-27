"""Pull hardware state from an ESP8266 HTTP server."""

from __future__ import annotations

import json
import socket
import urllib.error
import urllib.request
from typing import Any

from system.services.hardware_gateway.hardware_state import HardwareStateStore


DEFAULT_ESP_STATE_URL = "http://192.168.4.1/api/state"


class EspPullClient:
    def __init__(self, url: str = DEFAULT_ESP_STATE_URL, timeout_seconds: float = 1.0):
        self.url = url
        self.timeout_seconds = float(timeout_seconds)

    def fetch_once(self) -> dict[str, Any]:
        try:
            with urllib.request.urlopen(self.url, timeout=self.timeout_seconds) as response:
                body = response.read().decode("utf-8")
        except TimeoutError:
            return self._error("timeout")
        except socket.timeout:
            return self._error("timeout")
        except urllib.error.URLError as exc:
            reason = getattr(exc, "reason", None)
            if isinstance(reason, TimeoutError) or isinstance(reason, socket.timeout):
                return self._error("timeout")
            return self._error("network_error")
        except OSError:
            return self._error("network_error")
        try:
            payload = json.loads(body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return self._error("bad_json")
        if not isinstance(payload, dict):
            return self._error("bad_json")
        return {
            "status": "ok",
            "source": "esp_pull",
            "connected": True,
            "payload": payload,
        }

    def fetch_and_update(self, store: HardwareStateStore) -> dict[str, Any]:
        result = self.fetch_once()
        if result.get("status") != "ok":
            return result
        state = store.update(result.get("payload", {}))
        return {
            "status": "ok",
            "source": "esp_pull",
            "connected": bool(state.get("connected", False)),
            "state": state,
        }

    def _error(self, error: str) -> dict[str, Any]:
        return {
            "status": "error",
            "source": "esp_pull",
            "connected": False,
            "error": error,
        }
