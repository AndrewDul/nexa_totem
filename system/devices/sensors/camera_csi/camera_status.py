"""Raspberry Pi CSI camera diagnostics."""

import re
import shutil
import subprocess
from pathlib import Path

from system.services.diagnostics.status import make_component_status

CAMERA_COMPONENT = "camera_csi"
HELLO_COMMANDS = ("rpicam-hello", "libcamera-hello")
STILL_COMMANDS = ("rpicam-still", "libcamera-still")
DEFAULT_CAPTURE_PATH = Path("var/reports/camera/camera_test_latest.jpg")
MAX_OUTPUT_CHARS = 1200


def run_command(command, timeout=2):
    """Run a camera command and return a small result dictionary."""
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False,
            "stdout": _limit_text(exc.stdout or ""),
            "stderr": "Command timed out.",
            "missing": False,
            "returncode": None,
            "timed_out": True,
        }
    except (FileNotFoundError, subprocess.SubprocessError, OSError) as exc:
        return {
            "ok": False,
            "stdout": "",
            "stderr": str(exc),
            "missing": isinstance(exc, FileNotFoundError),
            "returncode": None,
            "timed_out": False,
        }

    return {
        "ok": result.returncode == 0,
        "stdout": _limit_text(result.stdout.strip()),
        "stderr": _limit_text(result.stderr.strip()),
        "missing": False,
        "returncode": result.returncode,
        "timed_out": False,
    }


def _limit_text(text, limit=MAX_OUTPUT_CHARS):
    value = text.decode("utf-8", errors="replace") if isinstance(text, bytes) else str(text or "")
    if len(value) <= limit:
        return value
    return value[:limit] + "...[truncated]"


def find_first_available(commands, command_finder=shutil.which):
    """Return the first command name that exists on the current system."""
    for command in commands:
        if command_finder(command):
            return command
    return None


def select_camera_command(command_finder=shutil.which):
    """Choose the camera list command, preferring modern Raspberry Pi names."""
    return find_first_available(HELLO_COMMANDS, command_finder=command_finder)


def select_capture_command(command_finder=shutil.which):
    """Choose the still capture command, preferring modern Raspberry Pi names."""
    return find_first_available(STILL_COMMANDS, command_finder=command_finder)


def parse_list_cameras_output(text):
    """Parse rpicam/libcamera list output without needing real camera hardware."""
    value = text or ""
    lowered = value.lower()
    names = []

    if "no cameras available" in lowered:
        return {"camera_detected": False, "camera_count": 0, "camera_names": []}

    pattern = re.compile(r"^\s*(\d+)\s*:\s*([^\[\(\n]+)", re.MULTILINE)
    for match in pattern.finditer(value):
        name = match.group(2).strip()
        if name and name not in names:
            names.append(name)

    return {
        "camera_detected": bool(names),
        "camera_count": len(names),
        "camera_names": names,
    }


def collect_camera_status(command_runner=run_command, command_finder=shutil.which, timeout=2):
    """Run a fast CSI camera status check."""
    camera_command = select_camera_command(command_finder=command_finder)
    details = {
        "commands_available": {command: bool(command_finder(command)) for command in HELLO_COMMANDS},
        "camera_command": camera_command,
        "camera_detected": False,
        "camera_count": 0,
        "camera_names": [],
    }

    if not camera_command:
        return make_component_status(
            component=CAMERA_COMPONENT,
            status="unknown",
            message="Camera status could not be checked because Raspberry Pi camera tools are not available.",
            details=details,
            source="camera_status",
        )

    result = command_runner([camera_command, "--list-cameras"], timeout=timeout)
    details["list_command_returncode"] = result.get("returncode")
    details["list_command_timed_out"] = result.get("timed_out", False)
    if result.get("stdout"):
        details["list_command_stdout"] = _limit_text(result.get("stdout"))
    if result.get("stderr"):
        details["list_command_stderr"] = _limit_text(result.get("stderr"))

    parsed = parse_list_cameras_output((result.get("stdout") or "") + "\n" + (result.get("stderr") or ""))
    details.update(parsed)

    if result.get("ok") and parsed["camera_detected"]:
        status = "ok"
        message = "CSI camera is detected."
    elif result.get("ok"):
        status = "missing"
        message = "CSI camera tools are available, but no CSI camera was detected."
    elif result.get("timed_out"):
        status = "warning"
        message = "CSI camera check timed out."
    elif parsed["camera_detected"]:
        status = "warning"
        message = "CSI camera was listed, but the camera command returned an error."
    elif "no cameras available" in ((result.get("stdout") or "") + (result.get("stderr") or "")).lower():
        status = "missing"
        message = "CSI camera tools are available, but no CSI camera was detected."
    else:
        status = "error"
        message = "CSI camera command failed."

    return make_component_status(
        component=CAMERA_COMPONENT,
        status=status,
        message=message,
        details=details,
        source="camera_status",
    )


def validate_camera_capture(
    output_path=None,
    command_runner=run_command,
    command_finder=shutil.which,
    timeout=6,
):
    """Optionally capture a small test image and return structured diagnostics."""
    capture_command = select_capture_command(command_finder=command_finder)
    target = Path(output_path) if output_path else DEFAULT_CAPTURE_PATH
    details = {
        "commands_available": {command: bool(command_finder(command)) for command in STILL_COMMANDS},
        "capture_command": capture_command,
        "capture_attempted": False,
        "capture_succeeded": False,
    }

    if not capture_command:
        return make_component_status(
            component=CAMERA_COMPONENT,
            status="missing",
            message="Camera capture validation could not run because still capture tools are not available.",
            details=details,
            source="camera_capture",
        )

    try:
        target.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        details["output_error"] = str(exc)
        return make_component_status(
            component=CAMERA_COMPONENT,
            status="error",
            message="Camera capture validation could not prepare the report folder.",
            details=details,
            source="camera_capture",
        )

    command = [
        capture_command,
        "-o",
        str(target),
        "--timeout",
        "1000",
        "--width",
        "640",
        "--height",
        "480",
        "--nopreview",
    ]
    details["capture_attempted"] = True
    result = command_runner(command, timeout=timeout)
    details["capture_command_returncode"] = result.get("returncode")
    details["capture_command_timed_out"] = result.get("timed_out", False)
    if result.get("stdout"):
        details["capture_command_stdout"] = _limit_text(result.get("stdout"))
    if result.get("stderr"):
        details["capture_command_stderr"] = _limit_text(result.get("stderr"))

    if result.get("ok") and target.exists() and target.stat().st_size > 0:
        details["capture_succeeded"] = True
        details["output_path"] = str(target)
        details["output_size_bytes"] = target.stat().st_size
        status = "ok"
        message = "CSI camera capture validation succeeded."
    elif result.get("timed_out"):
        status = "warning"
        message = "CSI camera capture validation timed out."
    else:
        status = "error"
        message = "CSI camera capture validation failed."

    return make_component_status(
        component=CAMERA_COMPONENT,
        status=status,
        message=message,
        details=details,
        source="camera_capture",
    )
