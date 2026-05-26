"""Live diagnostics collectors for the localhost diagnostics API."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from pathlib import Path

from system.devices.output.usb_speaker.speaker_status import collect_speaker_status
from system.devices.sensors.camera_csi.camera_status import collect_camera_status
from system.services.diagnostics.live_state import LOG_DIR, REPORT_DIR
from system.services.resources.process_monitor import collect_resource_snapshot
from system.services.system_health.pi_health import collect_pi_health


def _read_text(path):
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return ""


class CpuSampler:
    """Small /proc/stat delta sampler for API CPU usage."""

    def __init__(self):
        self.previous = None

    def read(self):
        text = _read_text("/proc/stat").splitlines()
        if not text:
            return None
        parts = text[0].split()
        if not parts or parts[0] != "cpu":
            return None
        values = []
        for raw in parts[1:]:
            try:
                values.append(int(raw))
            except ValueError:
                values.append(0)
        total = sum(values)
        idle = values[3] + (values[4] if len(values) > 4 else 0)
        current = (total, idle)
        if not self.previous:
            self.previous = current
            return None
        prev_total, prev_idle = self.previous
        self.previous = current
        total_delta = max(total - prev_total, 0)
        idle_delta = max(idle - prev_idle, 0)
        if not total_delta:
            return None
        return round((1.0 - idle_delta / total_delta) * 100.0, 1)


CPU_SAMPLER = CpuSampler()


def cpu_temperature_c():
    raw = _read_text("/sys/class/thermal/thermal_zone0/temp")
    if not raw:
        return None
    try:
        value = float(raw)
    except ValueError:
        return None
    if value > 1000:
        value = value / 1000.0
    return round(value, 1)


def memory_info():
    values = {}
    for line in _read_text("/proc/meminfo").splitlines():
        if ":" not in line:
            continue
        key, rest = line.split(":", 1)
        parts = rest.strip().split()
        if not parts:
            continue
        try:
            values[key] = int(parts[0])
        except ValueError:
            continue
    total = values.get("MemTotal")
    available = values.get("MemAvailable", values.get("MemFree"))
    if not total or available is None:
        return {"ram_usage_percent": None, "ram_used_mb": None, "ram_total_mb": None}
    used = max(total - available, 0)
    return {
        "ram_usage_percent": round((used / total) * 100.0, 1),
        "ram_used_mb": round(used / 1024.0, 1),
        "ram_total_mb": round(total / 1024.0, 1),
    }


def disk_root():
    try:
        disk = shutil.disk_usage("/")
    except OSError:
        return {"disk_usage_percent": None, "disk_used_gb": None, "disk_total_gb": None}
    return {
        "disk_usage_percent": round((disk.used / disk.total) * 100.0, 1) if disk.total else None,
        "disk_used_gb": round(disk.used / (1024 ** 3), 1),
        "disk_total_gb": round(disk.total / (1024 ** 3), 1),
    }


def run_command(command, timeout=2):
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False, timeout=timeout)
    except (FileNotFoundError, subprocess.SubprocessError, OSError) as exc:
        return {"ok": False, "stdout": "", "stderr": str(exc), "missing": isinstance(exc, FileNotFoundError)}
    return {"ok": result.returncode == 0, "stdout": result.stdout.strip(), "stderr": result.stderr.strip(), "missing": False}


def connected_ssid():
    for command in (["iwgetid", "-r"], ["nmcli", "-t", "-f", "active,ssid", "dev", "wifi"]):
        result = run_command(command, timeout=2)
        if not result["ok"]:
            continue
        output = result["stdout"].strip()
        if command[0] == "iwgetid" and output:
            return output
        for line in output.splitlines():
            if line.startswith("yes:"):
                return line.split(":", 1)[1] or None
    return None


def wifi_enabled():
    result = run_command(["nmcli", "radio", "wifi"], timeout=2)
    if result["ok"]:
        return result["stdout"].strip().lower() == "enabled"
    return None


def saved_networks():
    result = run_command(["nmcli", "-t", "-f", "NAME,TYPE", "connection", "show"], timeout=2)
    if not result["ok"]:
        return []
    names = []
    for line in result["stdout"].splitlines():
        parts = line.split(":")
        if len(parts) >= 2 and parts[-1] in {"wifi", "802-11-wireless"}:
            name = ":".join(parts[:-1]).strip()
            if name and name not in names:
                names.append(name)
    return names[:8]


def available_networks():
    result = run_command(["nmcli", "-t", "-f", "SSID", "dev", "wifi", "list", "--rescan", "no"], timeout=3)
    if not result["ok"]:
        return []
    names = []
    for line in result["stdout"].splitlines():
        name = line.strip()
        if name and name not in names:
            names.append(name)
    return names[:8]


def network_data(state):
    return {
        "status": "ok",
        "wifi_enabled": wifi_enabled(),
        "connected_ssid": connected_ssid(),
        "saved_networks": saved_networks(),
        "available_networks": available_networks(),
        "remote_network_state": state.remote_network_state,
        "pilot_connected": "unknown",
        "remote_connected": "unknown",
        "actions_are_dry_run": True,
        "write_actions": "dry_run_planned",
    }


def network_summary(state):
    return {
        "status": "ok",
        "wifi_enabled": wifi_enabled(),
        "connected_ssid": connected_ssid(),
        "remote_network_state": state.remote_network_state,
        "pilot_connected": "unknown",
        "remote_connected": "unknown",
        "actions_are_dry_run": True,
    }


def _audio_volume_state():
    result = run_command(["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"], timeout=2)
    if result["ok"] and result["stdout"]:
        parts = result["stdout"].replace("[", "").replace("]", "").split()
        muted = "MUTED" in parts
        for part in parts:
            try:
                return round(float(part) * 100), muted
            except ValueError:
                continue
    result = run_command(["pactl", "get-sink-volume", "@DEFAULT_SINK@"], timeout=2)
    if result["ok"] and "%" in result["stdout"]:
        for part in result["stdout"].split():
            if part.endswith("%"):
                try:
                    return int(part.rstrip("%")), None
                except ValueError:
                    continue
    return None, None


def audio_data():
    status = collect_speaker_status()
    details = status.get("details", {})
    speaker_name = details.get("default_output")
    if not speaker_name and details.get("playback_devices"):
        speaker_name = details["playback_devices"][0].get("device_name")
    volume_percent, muted = _audio_volume_state()
    return {
        "status": status.get("status", "unknown"),
        "speaker_status": status.get("status", "unknown"),
        "speaker_name": speaker_name or "Unknown",
        "volume_percent": volume_percent,
        "muted": muted,
        "issues": status.get("message", "Unknown"),
        "details": details,
    }


def camera_data(state):
    status = collect_camera_status(timeout=2)
    details = status.get("details", {})
    names = details.get("camera_names") or []
    with state.lock:
        preview_enabled = state.preview_enabled
        preview_last_frame_at = state.preview_last_frame_at
        preview_error = state.preview_error
        preview_mode = state.preview_mode
        preview_fps = state.preview_fps
        preview_frame_available = bool(state.preview_frame_bytes)
    age = round(time.time() - preview_last_frame_at, 1) if preview_last_frame_at else None
    return {
        "status": status.get("status", "unknown"),
        "camera_detected": bool(details.get("camera_detected")),
        "camera_ready": status.get("status") == "ok",
        "camera_name": names[0] if names else "Unknown",
        "preview": {
            "enabled": preview_enabled,
            "mode": preview_mode if preview_enabled else "off",
            "fps": preview_fps if preview_enabled else 0,
            "frame_available": preview_frame_available if preview_enabled else False,
            "last_frame_age_seconds": age,
            "error": preview_error,
        },
        "details": details,
    }


def system_data():
    health = collect_pi_health()
    details = health.get("details", {})
    mem = memory_info()
    cpu_percent = CPU_SAMPLER.read()
    if cpu_percent is None:
        time.sleep(0.05)
        cpu_percent = CPU_SAMPLER.read()
    throttling = "unknown"
    if details.get("throttling_detected") is True:
        throttling = "detected"
    elif details.get("throttling_detected") is False:
        throttling = "not_detected"
    return {
        "status": health.get("status", "unknown"),
        "system_ok": health.get("status") == "ok",
        "message": health.get("message", "Unknown"),
        "cpu_temperature_c": details.get("temperature_c") if details.get("temperature_c") is not None else cpu_temperature_c(),
        "cpu_usage_percent": cpu_percent,
        **mem,
        **disk_root(),
        "throttling": throttling,
        "gpu_usage_percent": None,
        "gpu_usage_supported": False,
        "gpu_usage_status": "not_supported",
        "details": details,
    }


def process_data():
    snapshot = collect_resource_snapshot(sample_interval=0.05)
    return {
        "status": snapshot.get("status", "unknown"),
        "processes": snapshot.get("processes", []),
        "summary": snapshot.get("summary", {}),
        "source": "process_monitor",
    }


def overview_data(state):
    system = system_data()
    audio = audio_data()
    camera = camera_data(state)
    network = network_data(state)
    return {
        "status": "ok",
        "overall_status": system.get("status", "unknown"),
        "system_ok": system.get("system_ok"),
        "wifi_enabled": network.get("wifi_enabled"),
        "connected_ssid": network.get("connected_ssid"),
        "remote_network_state": network.get("remote_network_state"),
        "remote_connected": False,
        "cpu_temperature_c": system.get("cpu_temperature_c"),
        "cpu_usage_percent": system.get("cpu_usage_percent"),
        "ram_usage_percent": system.get("ram_usage_percent"),
        "ram_used_mb": system.get("ram_used_mb"),
        "gpu_usage_percent": None,
        "gpu_usage_supported": False,
        "gpu_usage_status": "not_supported",
        "speaker_status": audio.get("speaker_status"),
        "speaker_name": audio.get("speaker_name"),
        "camera_detected": camera.get("camera_detected"),
        "camera_ready": camera.get("camera_ready"),
    }


def control_center_data(state):
    network = network_summary(state)
    audio = audio_data()
    system = system_data()
    with state.lock:
        quiet_mode = state.quiet_mode
        brightness_percent = state.brightness_percent
        brightness_auto = state.brightness_auto
        remote_network_state = state.remote_network_state
        sound_percent = state.sound_percent
        sound_muted = state.sound_muted
    volume_percent = audio.get("volume_percent")
    if volume_percent is None and sound_percent is not None:
        volume_percent = sound_percent
    return {
        "status": "ok",
        "brightness_percent": brightness_percent,
        "brightness_auto": brightness_auto,
        "sound_percent": volume_percent if volume_percent is not None else 50,
        "sound_display": str(volume_percent) + "%" if volume_percent is not None else "Unknown",
        "speaker_name": audio.get("speaker_name"),
        "speaker_status": audio.get("speaker_status"),
        "muted": audio.get("muted") if audio.get("muted") is not None else sound_muted,
        "quiet_mode": quiet_mode,
        "connected_ssid": network.get("connected_ssid"),
        "remote_network_state": remote_network_state,
        "cpu_temperature_c": system.get("cpu_temperature_c"),
    }


def logs_data(limit=80):
    if not LOG_DIR.exists():
        return {"status": "ok", "lines": ["No logs yet"], "source": "var/log"}
    lines = []
    for path in sorted(LOG_DIR.glob("*.log"))[-3:]:
        try:
            path_lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for line in path_lines[-limit:]:
            lines.append(f"{path.name}: {line}")
    return {"status": "ok", "lines": lines[-limit:] or ["No logs yet"], "source": "var/log"}


def reports_data():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    reports = []
    for path in sorted(REPORT_DIR.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True)[:20]:
        reports.append({"name": path.name, "path": str(path), "size_bytes": path.stat().st_size})
    return {"status": "ok", "reports": reports, "message": "No reports yet" if not reports else "Reports available"}


def write_report(name, payload):
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORT_DIR / name
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return str(path)
