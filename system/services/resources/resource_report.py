"""Combined resource report shape for NeXa ToTem."""

from system.services.diagnostics.status import combine_statuses, utc_now_iso
from system.services.resources.process_monitor import collect_resource_snapshot


def make_godot_telemetry_placeholder(process_status=None):
    """Return honest placeholder telemetry for the planned Godot LCD UI."""
    running = bool(process_status and process_status.get("status") == "running")
    return {
        "component": "nexa_godot_lcd_ui",
        "status": "unknown" if running else "not_running",
        "fps": None,
        "frame_time_ms": None,
        "gpu_usage_percent": None,
        "gpu_usage_supported": False,
        "message": "Godot LCD UI telemetry is not available yet."
        if running
        else "Godot LCD UI is not running yet.",
    }


def build_resource_report(process_snapshot=None, benchmark_results=None, godot_telemetry=None):
    """Build a report for NeXa resource use and optional benchmarks."""
    snapshot = process_snapshot or collect_resource_snapshot()
    benchmarks = list(benchmark_results or [])
    godot_process = None
    for process in snapshot.get("processes", []):
        if process.get("component") == "nexa_godot_lcd_ui":
            godot_process = process
            break

    telemetry = godot_telemetry or make_godot_telemetry_placeholder(godot_process)
    statuses = [snapshot]
    statuses.extend(benchmarks)
    status = combine_statuses(statuses)
    return {
        "resource_report": "nexa_resource_overview",
        "status": status,
        "message": "NeXa resource report is available.",
        "process_snapshot": snapshot,
        "benchmarks": benchmarks,
        "godot_telemetry": telemetry,
        "checked_at": utc_now_iso(),
        "source": "resource_report",
    }

