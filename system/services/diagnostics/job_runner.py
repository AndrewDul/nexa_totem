"""Background jobs for diagnostics benchmarks, reports, and checks."""

from __future__ import annotations

import threading
import time

from system.devices.output.usb_speaker.speaker_status import collect_speaker_status
from system.devices.sensors.camera_csi.camera_status import validate_camera_capture
from system.services.diagnostics.live_collectors import audio_data, camera_data, network_data, overview_data, process_data, system_data, write_report


def _run_once(state, name, target):
    current = state.get_job(name)
    if current.get("status") in {"pending", "running"}:
        return current
    state.set_job(name, "pending")

    def worker():
        state.set_job(name, "running")
        try:
            result = target()
            state.set_job(name, "done", result=result)
        except Exception as exc:  # pragma: no cover - defensive API boundary
            state.set_job(name, "error", error=str(exc))

    threading.Thread(target=worker, daemon=True).start()
    return state.get_job(name)


def start_benchmarks(state):
    def timed_row(name, func):
        started = time.monotonic()
        try:
            func()
            status = "ok"
        except Exception:  # pragma: no cover - defensive benchmark boundary
            status = "error"
        return {"name": name, "duration_ms": round((time.monotonic() - started) * 1000.0, 1), "status": status}

    def target():
        rows = [
            timed_row("Overview", lambda: overview_data(state)),
            timed_row("System", system_data),
            timed_row("Processes", process_data),
            timed_row("Audio", audio_data),
            timed_row("Camera", lambda: camera_data(state)),
            timed_row("Network", lambda: network_data(state)),
        ]
        return {"status": "ok", "results": rows}

    return _run_once(state, "benchmarks", target)


def start_report(state):
    def target():
        payload = {
            "generated_at": time.time(),
            "overview": overview_data(state),
            "system": system_data(),
            "processes": process_data(),
        }
        path = write_report("live_diagnostics_latest.json", payload)
        payload["report_path"] = path
        return payload

    return _run_once(state, "reports", target)


def start_camera_check(state):
    return _run_once(state, "camera_check", validate_camera_capture)


def start_audio_check(state):
    return _run_once(state, "audio_check", collect_speaker_status)
