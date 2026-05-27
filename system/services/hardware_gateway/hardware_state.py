"""In-memory state for the local hardware gateway."""

from __future__ import annotations

from datetime import datetime, timezone
from threading import Lock
from time import monotonic
from typing import Any

from system.services.hardware_gateway.hardware_models import (
    advice_for_air_status,
    normalize_air_status,
    normalize_distance,
    normalize_float,
    normalize_int,
    normalize_joystick,
    normalize_presence,
)


def state_with_age(state: dict[str, Any], last_seen_monotonic: float | None, stale_after_seconds: float) -> dict[str, Any]:
    if last_seen_monotonic is None:
        return state
    age_seconds = max(0.0, monotonic() - last_seen_monotonic)
    stale = age_seconds > stale_after_seconds
    current = dict(state)
    current["age_seconds"] = round(age_seconds, 3)
    current["connected"] = not stale
    current["stale"] = stale
    if stale:
        current["advice"] = "Waiting for live data"
    return current


def parse_arduino_raw_line(line: str) -> dict[str, Any]:
    parsed: dict[str, Any] = {}
    for chunk in str(line or "").split("|"):
        if "=" not in chunk:
            continue
        key, value = chunk.split("=", 1)
        parsed[key.strip()] = value.strip()
    return {
        "presence": normalize_presence(parsed.get("presence")),
        "distance_cm": normalize_distance(parsed.get("distance_cm")),
        "joystick": normalize_joystick(parsed.get("joystick")),
        "joystick_x": normalize_int(parsed.get("x")),
        "joystick_y": normalize_int(parsed.get("y")),
    }


def _presence_fields(payload: dict[str, Any], distance_cm: float | None, presence: bool) -> dict[str, Any]:
    has_distance = "distance_cm" in payload
    if distance_cm is not None:
        return {
            "distance_valid": distance_cm > 0,
            "presence_detected": distance_cm > 0,
            "presence_source": "distance",
        }
    if has_distance:
        return {
            "distance_valid": False,
            "presence_detected": False,
            "presence_source": "distance",
        }
    has_presence = "presence" in payload
    return {
        "distance_valid": False,
        "presence_detected": bool(presence),
        "presence_source": "presence_flag" if has_presence else "none",
    }


class HardwareStateStore:
    def __init__(self, stale_after_seconds: float = 5.0):
        self.stale_after_seconds = float(stale_after_seconds)
        self._lock = Lock()
        self._state: dict[str, Any] | None = None
        self._last_seen_monotonic: float | None = None

    def update(self, payload: dict[str, Any] | None) -> dict[str, Any]:
        if not isinstance(payload, dict):
            payload = {}
        now_iso = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        normalized = {
            "device": str(payload.get("device", "") or ""),
            "presence": normalize_presence(payload.get("presence")),
            "distance_cm": normalize_distance(payload.get("distance_cm")),
            "joystick": normalize_joystick(payload.get("joystick")),
            "joystick_x": normalize_int(payload.get("joystick_x", payload.get("x"))),
            "joystick_y": normalize_int(payload.get("joystick_y", payload.get("y"))),
            "temperature_c": normalize_float(payload.get("temperature_c")),
            "humidity_percent": normalize_float(payload.get("humidity_percent")),
            "pressure_hpa": normalize_float(payload.get("pressure_hpa")),
            "gas_kohms": normalize_float(payload.get("gas_kohms")),
            "air_status": normalize_air_status(payload.get("air_status")),
            "wifi_rssi": normalize_int(payload.get("wifi_rssi")),
            "last_arduino_raw": str(payload.get("last_arduino_raw", "") or ""),
            "last_seen_at": now_iso,
        }
        normalized.update(_presence_fields(payload, normalized["distance_cm"], normalized["presence"]))
        normalized["advice"] = advice_for_air_status(str(normalized["air_status"]), True)
        with self._lock:
            self._state = normalized
            self._last_seen_monotonic = monotonic()
            return state_with_age(self._state, self._last_seen_monotonic, self.stale_after_seconds)

    def as_dict(self) -> dict[str, Any]:
        with self._lock:
            if self._state is None or self._last_seen_monotonic is None:
                return self._empty_state()
            return state_with_age(self._state, self._last_seen_monotonic, self.stale_after_seconds)

    def _empty_state(self) -> dict[str, Any]:
        return {
            "device": "",
            "presence": False,
            "distance_cm": None,
            "distance_valid": False,
            "presence_detected": False,
            "presence_source": "none",
            "joystick": "UNKNOWN",
            "joystick_x": None,
            "joystick_y": None,
            "temperature_c": None,
            "humidity_percent": None,
            "pressure_hpa": None,
            "gas_kohms": None,
            "air_status": "UNKNOWN",
            "advice": "Waiting for live data",
            "wifi_rssi": None,
            "last_arduino_raw": "",
            "last_seen_at": "",
            "age_seconds": 0.0,
            "connected": False,
            "stale": True,
        }
