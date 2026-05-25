"""Monitor resource usage for known NeXa processes only."""

import os
import time
from pathlib import Path

from system.services.diagnostics.status import utc_now_iso
from system.services.resources.process_registry import get_process_registry

CLOCK_TICKS = os.sysconf(os.sysconf_names.get("SC_CLK_TCK", "SC_CLK_TCK"))


def read_text(path):
    """Read a text file safely."""
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def get_total_memory_kb(proc_root="/proc"):
    """Read total memory from /proc/meminfo."""
    for line in read_text(Path(proc_root) / "meminfo").splitlines():
        if line.startswith("MemTotal:"):
            parts = line.split()
            if len(parts) >= 2:
                try:
                    return int(parts[1])
                except ValueError:
                    return 0
    return 0


def get_total_cpu_time(proc_root="/proc"):
    """Return total CPU ticks from /proc/stat."""
    first_line = read_text(Path(proc_root) / "stat").splitlines()
    if not first_line:
        return 0
    parts = first_line[0].split()
    if not parts or parts[0] != "cpu":
        return 0
    total = 0
    for value in parts[1:]:
        try:
            total += int(value)
        except ValueError:
            continue
    return total


def parse_status_rss_kb(text):
    """Parse VmRSS from /proc/[pid]/status."""
    for line in text.splitlines():
        if line.startswith("VmRSS:"):
            parts = line.split()
            if len(parts) >= 2:
                try:
                    return int(parts[1])
                except ValueError:
                    return 0
    return 0


def parse_process_cpu_ticks(stat_text):
    """Parse user and system CPU ticks from /proc/[pid]/stat."""
    if not stat_text:
        return 0
    try:
        after_name = stat_text.rsplit(")", 1)[1].strip()
    except IndexError:
        return 0
    fields = after_name.split()
    try:
        return int(fields[11]) + int(fields[12])
    except (IndexError, ValueError):
        return 0


def read_process_snapshot(pid, proc_root="/proc"):
    """Read command, memory, and CPU ticks for one process."""
    pid_path = Path(proc_root) / str(pid)
    command = read_text(pid_path / "cmdline").replace("\x00", " ").strip()
    status_text = read_text(pid_path / "status")
    stat_text = read_text(pid_path / "stat")
    if not command and not status_text and not stat_text:
        return None
    return {
        "pid": int(pid),
        "command": command,
        "rss_kb": parse_status_rss_kb(status_text),
        "cpu_ticks": parse_process_cpu_ticks(stat_text),
    }


def list_process_snapshots(proc_root="/proc"):
    """List process snapshots from /proc."""
    snapshots = []
    try:
        entries = Path(proc_root).iterdir()
    except OSError:
        return snapshots
    for entry in entries:
        if not entry.name.isdigit():
            continue
        snapshot = read_process_snapshot(entry.name, proc_root=proc_root)
        if snapshot:
            snapshots.append(snapshot)
    return snapshots


def command_matches(definition, command):
    """Return True when a command matches a NeXa process definition."""
    value = (command or "").lower()
    return any(keyword.lower() in value for keyword in definition.get("match_keywords", []))


def make_not_running_status(definition):
    """Create a process status for a NeXa process that is not running."""
    return {
        "component": definition["component"],
        "display_name": definition["display_name"],
        "status": "not_running",
        "pid": None,
        "cpu_percent": 0.0,
        "memory_rss_mb": 0.0,
        "memory_percent": 0.0,
        "command": "",
        "notes": definition.get("notes", ""),
    }


def make_running_status(definition, snapshot, cpu_percent, total_memory_kb):
    """Create a process status for a running NeXa process."""
    rss_kb = snapshot.get("rss_kb", 0)
    memory_mb = round(rss_kb / 1024.0, 1)
    memory_percent = round((rss_kb / total_memory_kb) * 100.0, 1) if total_memory_kb else 0.0
    return {
        "component": definition["component"],
        "display_name": definition["display_name"],
        "status": "running",
        "pid": snapshot["pid"],
        "cpu_percent": round(cpu_percent, 1),
        "memory_rss_mb": memory_mb,
        "memory_percent": memory_percent,
        "command": snapshot.get("command", ""),
        "notes": definition.get("notes", ""),
    }


def collect_process_statuses(registry=None, process_snapshots=None, cpu_percent_by_pid=None, total_memory_kb=0):
    """Build statuses for known NeXa processes only."""
    definitions = registry or get_process_registry()
    snapshots = process_snapshots or []
    statuses = []
    used_pids = set()
    for definition in definitions:
        matches = [
            snapshot
            for snapshot in snapshots
            if snapshot["pid"] not in used_pids and command_matches(definition, snapshot.get("command", ""))
        ]
        if not matches:
            statuses.append(make_not_running_status(definition))
            continue
        selected = max(matches, key=lambda item: (cpu_percent_by_pid or {}).get(item["pid"], 0.0))
        used_pids.add(selected["pid"])
        statuses.append(
            make_running_status(
                definition,
                selected,
                (cpu_percent_by_pid or {}).get(selected["pid"], 0.0),
                total_memory_kb,
            )
        )
    return statuses


def summarize_processes(processes):
    """Summarize NeXa process resource statuses."""
    running = [item for item in processes if item["status"] == "running"]
    top_cpu = max(processes, key=lambda item: item.get("cpu_percent", 0.0), default=None)
    top_memory = max(processes, key=lambda item: item.get("memory_rss_mb", 0.0), default=None)
    return {
        "running_count": len(running),
        "not_running_count": len(processes) - len(running),
        "top_cpu_component": top_cpu["component"] if top_cpu and top_cpu.get("cpu_percent", 0.0) > 0 else None,
        "top_memory_component": top_memory["component"] if top_memory and top_memory.get("memory_rss_mb", 0.0) > 0 else None,
        "total_nexa_cpu_percent": round(sum(item.get("cpu_percent", 0.0) for item in processes), 1),
        "total_nexa_memory_mb": round(sum(item.get("memory_rss_mb", 0.0) for item in processes), 1),
    }


def collect_resource_snapshot(registry=None, proc_root="/proc", sample_interval=0.2, sleeper=time.sleep):
    """Collect a quick resource snapshot for known NeXa processes only."""
    start_processes = list_process_snapshots(proc_root=proc_root)
    start_cpu = get_total_cpu_time(proc_root=proc_root)
    if sample_interval > 0:
        sleeper(sample_interval)
    end_processes = list_process_snapshots(proc_root=proc_root)
    end_cpu = get_total_cpu_time(proc_root=proc_root)
    total_memory_kb = get_total_memory_kb(proc_root=proc_root)

    start_ticks = {item["pid"]: item["cpu_ticks"] for item in start_processes}
    cpu_delta_total = max(end_cpu - start_cpu, 0)
    cpu_percent_by_pid = {}
    for item in end_processes:
        pid = item["pid"]
        delta = max(item["cpu_ticks"] - start_ticks.get(pid, item["cpu_ticks"]), 0)
        cpu_percent_by_pid[pid] = (delta / cpu_delta_total) * 100.0 if cpu_delta_total else 0.0

    processes = collect_process_statuses(
        registry=registry,
        process_snapshots=end_processes,
        cpu_percent_by_pid=cpu_percent_by_pid,
        total_memory_kb=total_memory_kb,
    )
    summary = summarize_processes(processes)
    status = "ok" if summary["running_count"] > 0 else "not_checked"
    message = "NeXa process resource snapshot is available." if summary["running_count"] > 0 else "No known NeXa processes are running yet."
    return {
        "resource_report": "nexa_processes",
        "status": status,
        "message": message,
        "processes": processes,
        "summary": summary,
        "checked_at": utc_now_iso(),
        "source": "process_monitor",
    }

