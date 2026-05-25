"""USB speaker and audio output diagnostics."""

import re
import subprocess

from system.services.diagnostics.status import make_component_status

SPEAKER_KEYWORDS = ("usb", "uac", "speaker", "headset", "headphone", "sound blaster")


def run_command(command, timeout=3):
    """Run an audio command and return a small result dictionary."""
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


def parse_aplay_devices(text):
    """Parse `aplay -l` output into playback device dictionaries."""
    devices = []
    pattern = re.compile(r"card\s+(\d+):\s+([^\[]+)\[([^\]]+)\],\s+device\s+(\d+):\s+([^\[]+)\[([^\]]+)\]")
    for line in (text or "").splitlines():
        match = pattern.search(line)
        if not match:
            continue
        devices.append(
            {
                "card": int(match.group(1)),
                "card_id": match.group(2).strip(),
                "card_name": match.group(3).strip(),
                "device": int(match.group(4)),
                "device_id": match.group(5).strip(),
                "device_name": match.group(6).strip(),
            }
        )
    return devices


def parse_pactl_sinks(text):
    """Parse `pactl list short sinks` output into sink dictionaries."""
    sinks = []
    for line in (text or "").splitlines():
        parts = line.split()
        if len(parts) < 2:
            continue
        sinks.append({"index": parts[0], "name": parts[1], "description": " ".join(parts[2:])})
    return sinks


def parse_wpctl_default_output(text):
    """Find the marked default output line from `wpctl status`."""
    for line in (text or "").splitlines():
        stripped = line.strip()
        if stripped.startswith("*"):
            return stripped.lstrip("*").strip()
    return None


def looks_like_usb_speaker(name):
    """Return True when a device name looks like an external speaker output."""
    value = (name or "").lower()
    return any(keyword in value for keyword in SPEAKER_KEYWORDS)


def any_usb_speaker(devices, sinks):
    for device in devices:
        names = " ".join(
            [
                device.get("card_id", ""),
                device.get("card_name", ""),
                device.get("device_id", ""),
                device.get("device_name", ""),
            ]
        )
        if looks_like_usb_speaker(names):
            return True
    return any(looks_like_usb_speaker(sink.get("name", "")) for sink in sinks)


def collect_speaker_status(command_runner=run_command):
    """Check audio output state and return a diagnostics component status."""
    details = {
        "playback_devices": [],
        "sinks": [],
        "default_output": None,
        "commands_available": {},
    }

    aplay = command_runner(["aplay", "-l"])
    details["commands_available"]["aplay"] = not aplay.get("missing", False)
    if aplay["ok"]:
        details["playback_devices"] = parse_aplay_devices(aplay["stdout"])

    pactl = command_runner(["pactl", "list", "short", "sinks"])
    details["commands_available"]["pactl"] = not pactl.get("missing", False)
    if pactl["ok"]:
        details["sinks"] = parse_pactl_sinks(pactl["stdout"])

    wpctl = command_runner(["wpctl", "status"])
    details["commands_available"]["wpctl"] = not wpctl.get("missing", False)
    if wpctl["ok"]:
        details["default_output"] = parse_wpctl_default_output(wpctl["stdout"])

    playback_count = len(details["playback_devices"]) + len(details["sinks"])
    usb_detected = any_usb_speaker(details["playback_devices"], details["sinks"])
    command_available = any(details["commands_available"].values())

    details["playback_devices_found"] = playback_count
    details["usb_speaker_detected"] = usb_detected

    if usb_detected and playback_count > 0:
        status = "ok"
        message = "USB speaker is connected and audio output is available."
    elif playback_count > 0:
        status = "warning"
        message = "Audio output is available, but a USB speaker was not clearly detected."
    elif command_available:
        status = "missing"
        message = "USB speaker is not detected. NeXa ToTem may not be able to play sounds."
    else:
        status = "unknown"
        message = "Audio status could not be checked because audio tools are not available."

    return make_component_status(
        component="usb_speaker",
        status=status,
        message=message,
        details=details,
        source="speaker_status",
    )
