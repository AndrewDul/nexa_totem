"""Small value normalizers for hardware gateway data."""

from __future__ import annotations

from typing import Any


ALLOWED_JOYSTICKS = {"CENTER", "LEFT", "RIGHT", "UP", "DOWN", "SELECT", "UNKNOWN"}
ALLOWED_AIR_STATUS = {"OK", "VENTILATE", "UNKNOWN"}


def normalize_presence(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return int(value) == 1
    if isinstance(value, str):
        cleaned = value.strip().lower()
        if cleaned in {"1", "true", "yes", "on"}:
            return True
        if cleaned in {"0", "false", "no", "off", ""}:
            return False
    return False


def normalize_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def normalize_int(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def normalize_distance(value: Any) -> float | None:
    distance = normalize_float(value)
    if distance is None or distance < 0:
        return None
    return distance


def normalize_joystick(value: Any) -> str:
    cleaned = str(value or "UNKNOWN").strip().upper()
    return cleaned if cleaned in ALLOWED_JOYSTICKS else "UNKNOWN"


def normalize_air_status(value: Any) -> str:
    cleaned = str(value or "UNKNOWN").strip().upper()
    return cleaned if cleaned in ALLOWED_AIR_STATUS else "UNKNOWN"


def advice_for_air_status(air_status: str, has_live_data: bool) -> str:
    if not has_live_data:
        return "Waiting for live data"
    if air_status == "VENTILATE":
        return "Open the window"
    if air_status == "OK":
        return "Air looks okay"
    return "Waiting for live data"
