"""Local prototype settings store for NeXa ToTem."""

from __future__ import annotations

import copy
import hashlib
import hmac
import json
import secrets
import time
from pathlib import Path


SETTINGS_PATH = Path("var/data/nexa_settings.json")
COLOR_OPTIONS = {
    "Blue",
    "Sky Blue",
    "Cyan",
    "White",
    "Warm White",
    "Yellow",
    "Orange",
    "Red",
    "Pink",
    "Purple",
    "Green",
    "Mint",
    "Brown",
    "Gold",
    "Grey",
    "Graphite",
    "Black",
}
PRESET_OPTIONS = {
    "NeXa Blue",
    "Apple Dark",
    "Warm Desk",
    "Focus Green",
    "Night Red",
    "Soft Pink",
    "Minimal White",
}
APPEARANCE_COLOR_KEYS = {
    "eye_color",
    "mouth_color",
    "tile_accent_color",
    "background_color",
    "led_color",
    "time_color",
    "hour_color",
    "minute_color",
    "second_color",
    "date_color",
    "day_color",
    "month_color",
    "year_color",
}

DEFAULT_SETTINGS = {
    "appearance": {
        "eye_color": "Blue",
        "mouth_color": "Blue",
        "tile_accent_color": "Blue",
        "background_color": "Black",
        "led_color": "Blue",
        "time_color": "White",
        "hour_color": "White",
        "minute_color": "White",
        "second_color": "Grey",
        "date_color": "Grey",
        "day_color": "Grey",
        "month_color": "Grey",
        "year_color": "Grey",
        "preset": "NeXa Blue",
    },
    "notifications": {
        "style": "Banner",
        "show_on_face_home": True,
        "icon_only": False,
        "control_center_only": False,
        "use_sound": True,
        "use_led": True,
        "use_face_expression": True,
        "use_behaviour": True,
        "private_notifications_enabled": False,
        "private_reminders_enabled": False,
    },
    "privacy": {
        "pin_enabled": False,
        "pin_hash": "",
        "pin_salt": "",
        "private_unlock_until": 0,
        "private_unlock_seconds": 300,
    },
    "modes": {"current_mode": "Normal"},
    "quick_shelf": {
        "enabled_tiles": [
            "Brightness",
            "Sound",
            "Quiet Mode",
            "Network",
            "Reminders",
            "To Do",
            "Study",
            "Diagnostics",
            "Settings",
        ]
    },
    "display": {
        "brightness_percent": 65,
        "auto_brightness": False,
        "show_clock_on_face": True,
        "show_date_on_face": False,
        "text_size": "Normal",
        "reduce_motion": False,
        "screen_timeout": "planned",
    },
    "sound": {
        "volume_percent": 50,
        "muted": False,
        "sound_theme": "Soft",
        "button_sound": True,
        "notification_sound": True,
        "error_sound": True,
        "quiet_hours": "planned",
    },
    "network": {
        "wifi_connect_actions": "dry_run_planned",
        "remote_wifi_enabled": False,
    },
    "remote": {
        "controller_enabled": True,
        "vibration_enabled": False,
    },
    "diagnostics": {
        "collect_logs": True,
        "log_level": "Normal",
    },
    "safety": {
        "confirm_exit": True,
        "confirm_power_actions": True,
    },
}

SENSITIVE_KEYS = {"pin_hash", "pin_salt"}


def _merge_defaults(value, default):
    if isinstance(default, dict):
        merged = copy.deepcopy(default)
        if isinstance(value, dict):
            for key, item in value.items():
                if key in merged:
                    merged[key] = _merge_defaults(item, merged[key])
        return merged
    return value if value is not None else copy.deepcopy(default)


def default_settings():
    return copy.deepcopy(DEFAULT_SETTINGS)


def load_settings(path=SETTINGS_PATH):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default_settings()
    return _merge_defaults(data, DEFAULT_SETTINGS)


def save_settings(settings, path=SETTINGS_PATH):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    safe = _merge_defaults(settings, DEFAULT_SETTINGS)
    temp = target.with_suffix(".tmp")
    temp.write_text(json.dumps(safe, indent=2, sort_keys=True), encoding="utf-8")
    temp.replace(target)
    return safe


def safe_settings(settings):
    cleaned = copy.deepcopy(settings)
    privacy = cleaned.get("privacy", {})
    for key in SENSITIVE_KEYS:
        privacy.pop(key, None)
    return cleaned


def get_settings(path=SETTINGS_PATH):
    return safe_settings(load_settings(path))


def update_setting(section, key, value, path=SETTINGS_PATH):
    settings = load_settings(path)
    if section not in DEFAULT_SETTINGS or key not in DEFAULT_SETTINGS[section]:
        return {"status": "error", "error": "unknown_setting"}
    if section == "appearance" and key in APPEARANCE_COLOR_KEYS and value not in COLOR_OPTIONS:
        return {"status": "error", "error": "invalid_color"}
    if section == "appearance" and key == "preset" and value not in PRESET_OPTIONS:
        return {"status": "error", "error": "invalid_preset"}
    settings[section][key] = value
    saved = save_settings(settings, path)
    return {"status": "ok", "settings": safe_settings(saved)}


def update_many(updates, path=SETTINGS_PATH):
    settings = load_settings(path)
    if not isinstance(updates, list):
        return {"status": "error", "error": "updates_must_be_list"}
    for item in updates:
        if not isinstance(item, dict):
            return {"status": "error", "error": "invalid_update"}
        section = str(item.get("section", ""))
        key = str(item.get("key", ""))
        value = item.get("value")
        if section not in DEFAULT_SETTINGS or key not in DEFAULT_SETTINGS[section]:
            return {"status": "error", "error": "unknown_setting"}
        if section == "appearance" and key in APPEARANCE_COLOR_KEYS and value not in COLOR_OPTIONS:
            return {"status": "error", "error": "invalid_color"}
        if section == "appearance" and key == "preset" and value not in PRESET_OPTIONS:
            return {"status": "error", "error": "invalid_preset"}
    for item in updates:
        settings[str(item["section"])][str(item["key"])] = item.get("value")
    saved = save_settings(settings, path)
    return {"status": "ok", "settings": safe_settings(saved)}


def reset_section(section, path=SETTINGS_PATH):
    settings = load_settings(path)
    if section not in DEFAULT_SETTINGS:
        return {"status": "error", "error": "unknown_section"}
    settings[section] = copy.deepcopy(DEFAULT_SETTINGS[section])
    saved = save_settings(settings, path)
    return {"status": "ok", "settings": safe_settings(saved)}


def valid_pin(pin):
    return isinstance(pin, str) and len(pin) == 4 and pin.isdigit()


def _hash_pin(pin, salt):
    return hashlib.pbkdf2_hmac("sha256", pin.encode("utf-8"), salt.encode("utf-8"), 100_000).hex()


def set_pin(pin, path=SETTINGS_PATH):
    if not valid_pin(pin):
        return {"status": "error", "error": "pin_must_be_4_digits"}
    settings = load_settings(path)
    salt = secrets.token_hex(16)
    settings["privacy"]["pin_salt"] = salt
    settings["privacy"]["pin_hash"] = _hash_pin(pin, salt)
    settings["privacy"]["pin_enabled"] = True
    settings["privacy"]["private_unlock_until"] = 0
    saved = save_settings(settings, path)
    return {"status": "ok", "pin_enabled": True, "settings": safe_settings(saved)}


def verify_pin(pin, path=SETTINGS_PATH, now=None):
    now = time.time() if now is None else now
    settings = load_settings(path)
    privacy = settings["privacy"]
    if not valid_pin(pin) or not privacy.get("pin_enabled"):
        return {"status": "ok", "unlocked": False, "message": "invalid_pin"}
    expected = privacy.get("pin_hash", "")
    salt = privacy.get("pin_salt", "")
    actual = _hash_pin(pin, salt) if salt else ""
    if expected and hmac.compare_digest(expected, actual):
        unlock_until = int(now + int(privacy.get("private_unlock_seconds", 300)))
        privacy["private_unlock_until"] = unlock_until
        save_settings(settings, path)
        return {"status": "ok", "unlocked": True, "unlock_until": unlock_until, "message": "unlocked"}
    return {"status": "ok", "unlocked": False, "message": "wrong_pin"}


def lock_private(path=SETTINGS_PATH):
    settings = load_settings(path)
    settings["privacy"]["private_unlock_until"] = 0
    save_settings(settings, path)
    return {"status": "ok", "unlocked": False, "unlock_until": 0}


def is_private_unlocked(settings=None, now=None):
    now = time.time() if now is None else now
    settings = load_settings() if settings is None else settings
    privacy = settings.get("privacy", {})
    if not privacy.get("pin_enabled", False):
        return True
    return float(privacy.get("private_unlock_until", 0) or 0) > now


def should_hide_private_notifications(settings=None, now=None):
    settings = load_settings() if settings is None else settings
    return bool(settings.get("notifications", {}).get("private_notifications_enabled", False)) and not is_private_unlocked(settings, now)


def should_hide_private_reminders(settings=None, now=None):
    settings = load_settings() if settings is None else settings
    return bool(settings.get("notifications", {}).get("private_reminders_enabled", False)) and not is_private_unlocked(settings, now)


def privacy_status(path=SETTINGS_PATH, now=None):
    now = time.time() if now is None else now
    settings = load_settings(path)
    privacy = settings["privacy"]
    return {
        "status": "ok",
        "pin_enabled": bool(privacy.get("pin_enabled", False)),
        "unlocked": is_private_unlocked(settings, now),
        "private_notifications_enabled": bool(settings["notifications"].get("private_notifications_enabled", False)),
        "private_reminders_enabled": bool(settings["notifications"].get("private_reminders_enabled", False)),
        "unlock_seconds": int(privacy.get("private_unlock_seconds", 300)),
        "unlock_until": int(privacy.get("private_unlock_until", 0) or 0),
    }
