"""Raspberry Pi and Linux host health checks."""

import os
import platform
import shutil
import socket
import subprocess
from pathlib import Path

from system.services.diagnostics.status import make_component_status


def run_command(command, timeout=3):
    """Run a safe command and return a small result dictionary."""
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (FileNotFoundError, subprocess.SubprocessError, OSError) as exc:
        return {"ok": False, "stdout": "", "stderr": str(exc), "missing": isinstance(exc, FileNotFoundError)}

    return {
        "ok": result.returncode == 0,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
        "missing": False,
    }


def parse_os_release(text):
    values = {}
    for line in text.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key] = value.strip().strip('"')
    return values.get("PRETTY_NAME") or values.get("NAME")


def parse_cpu_temperature(text):
    clean = (text or "").strip()
    if not clean:
        return None
    if clean.startswith("temp="):
        clean = clean.replace("temp=", "").replace("'C", "")
    try:
        value = float(clean)
    except ValueError:
        return None
    if value > 1000:
        value = value / 1000.0
    return round(value, 1)


def parse_meminfo(text):
    values = {}
    for line in text.splitlines():
        if ":" not in line:
            continue
        key, rest = line.split(":", 1)
        parts = rest.strip().split()
        if not parts:
            continue
        try:
            values[key] = int(parts[0]) * 1024
        except ValueError:
            continue

    total = values.get("MemTotal")
    available = values.get("MemAvailable")
    free = values.get("MemFree")
    if total is None:
        return {}
    if available is None:
        available = free
    used = total - available if available is not None else None
    return {"total_bytes": total, "used_bytes": used, "available_bytes": available}


def parse_uptime_seconds(text):
    try:
        return int(float(text.split()[0]))
    except (IndexError, TypeError, ValueError):
        return None


def parse_throttled_output(text):
    raw = (text or "").strip()
    if "=" in raw:
        raw = raw.split("=", 1)[1].strip()
    try:
        value = int(raw, 16)
    except ValueError:
        return {
            "throttled_raw": raw or None,
            "undervoltage_detected": None,
            "throttling_detected": None,
            "flags": {},
        }

    flags = {
        "under_voltage_now": bool(value & (1 << 0)),
        "frequency_capped_now": bool(value & (1 << 1)),
        "throttled_now": bool(value & (1 << 2)),
        "soft_temperature_limit_now": bool(value & (1 << 3)),
        "under_voltage_has_occurred": bool(value & (1 << 16)),
        "frequency_capped_has_occurred": bool(value & (1 << 17)),
        "throttling_has_occurred": bool(value & (1 << 18)),
        "soft_temperature_limit_has_occurred": bool(value & (1 << 19)),
    }
    return {
        "throttled_raw": raw,
        "undervoltage_detected": flags["under_voltage_now"] or flags["under_voltage_has_occurred"],
        "throttling_detected": flags["throttled_now"] or flags["throttling_has_occurred"],
        "flags": flags,
    }


def read_text(path):
    try:
        return Path(path).read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def collect_pi_health(command_runner=run_command, file_reader=read_text):
    """Collect host health and return a diagnostics component status."""
    details = {
        "hostname": socket.gethostname(),
        "kernel": platform.release(),
        "machine": platform.machine(),
    }

    os_release = file_reader("/etc/os-release")
    if os_release:
        details["os"] = parse_os_release(os_release)

    uptime = file_reader("/proc/uptime")
    details["uptime_seconds"] = parse_uptime_seconds(uptime)

    temperature = parse_cpu_temperature(file_reader("/sys/class/thermal/thermal_zone0/temp"))
    if temperature is None:
        temp_result = command_runner(["vcgencmd", "measure_temp"])
        if temp_result["ok"]:
            temperature = parse_cpu_temperature(temp_result["stdout"])
    details["temperature_c"] = temperature

    memory = parse_meminfo(file_reader("/proc/meminfo"))
    if memory:
        details["memory"] = memory

    disk = shutil.disk_usage("/")
    details["disk_root"] = {
        "total_bytes": disk.total,
        "used_bytes": disk.used,
        "available_bytes": disk.free,
    }

    throttled_result = command_runner(["vcgencmd", "get_throttled"])
    if throttled_result["ok"]:
        details.update(parse_throttled_output(throttled_result["stdout"]))
    else:
        details["throttled_raw"] = None
        details["vcgencmd_available"] = not throttled_result.get("missing", False)
        if details["vcgencmd_available"]:
            details["vcgencmd_get_throttled_error"] = throttled_result.get("stderr") or "Command failed."

    volts_result = command_runner(["vcgencmd", "measure_volts"])
    if volts_result["ok"]:
        details["voltage_raw"] = volts_result["stdout"]

    status = "ok"
    messages = []
    if temperature is None:
        status = "unknown"
        messages.append("CPU temperature could not be read.")
    elif temperature >= 80:
        status = "warning"
        messages.append("CPU temperature is high.")

    if details.get("undervoltage_detected"):
        status = "warning"
        messages.append("Undervoltage has been detected.")
    if details.get("throttling_detected"):
        status = "warning"
        messages.append("Throttling has been detected.")

    if details.get("vcgencmd_get_throttled_error"):
        status = "warning"
        messages.append("Throttling state could not be read.")

    if not messages:
        messages.append("Raspberry Pi health looks normal.")

    return make_component_status(
        component="raspberry_pi",
        status=status,
        message=" ".join(messages),
        details=details,
        source="pi_health",
    )
