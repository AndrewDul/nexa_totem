#!/usr/bin/env python3
"""Print USB speaker and audio output diagnostics."""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system.devices.output.usb_speaker.speaker_status import collect_speaker_status
from system.services.diagnostics.reports import write_json_report


def write_test_tone(path, seconds=1, sample_rate=44100, frequency=880):
    import math
    import struct

    frames = int(seconds * sample_rate)
    with wave.open(str(path), "w") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(sample_rate)
        for index in range(frames):
            sample = int(12000 * math.sin(2 * math.pi * frequency * index / sample_rate))
            output.writeframes(struct.pack("<h", sample))


def play_test_sound():
    if shutil.which("speaker-test"):
        result = subprocess.run(
            ["speaker-test", "-t", "sine", "-f", "880", "-l", "1"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0, result.stderr.strip() or result.stdout.strip()

    for tool in ("paplay", "pw-play", "aplay"):
        if not shutil.which(tool):
            continue
        with tempfile.NamedTemporaryFile(suffix=".wav") as temp_file:
            write_test_tone(Path(temp_file.name))
            result = subprocess.run(
                [tool, temp_file.name],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0, result.stderr.strip() or result.stdout.strip()

    return False, "No supported sound playback tool was found."


def main():
    parser = argparse.ArgumentParser(description="Check USB speaker and audio output.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    parser.add_argument("--play-test-sound", action="store_true", help="Play a short test tone.")
    parser.add_argument("--save-report", action="store_true", help="Save the latest JSON report.")
    args = parser.parse_args()

    status = collect_speaker_status()
    if args.play_test_sound:
        played, message = play_test_sound()
        status["details"]["test_sound_played"] = played
        status["details"]["test_sound_message"] = message

    if args.save_report:
        write_json_report(status, REPO_ROOT / "var/reports/diagnostics/audio_output_latest.json")

    if args.json:
        print(json.dumps(status, indent=2, sort_keys=True))
        return

    print(f"USB speaker: {status['status']}")
    print(status["message"])
    details = status["details"]
    print(f"Playback outputs found: {details.get('playback_devices_found', 0)}")
    print(f"USB speaker detected: {details.get('usb_speaker_detected', False)}")
    if args.play_test_sound:
        print(f"Test sound played: {details['test_sound_played']}")
        print(details["test_sound_message"])


if __name__ == "__main__":
    main()
