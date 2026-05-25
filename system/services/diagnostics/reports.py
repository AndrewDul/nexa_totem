"""JSON report helpers for diagnostics."""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_REPORT_ROOT = Path("var/reports/diagnostics")
DEFAULT_HISTORY_LIMIT = 50


def ensure_report_dir(path="var/reports/diagnostics"):
    """Create and return a diagnostics report directory."""
    report_dir = Path(path)
    report_dir.mkdir(parents=True, exist_ok=True)
    return report_dir


def write_json_report(report, path):
    """Write a diagnostics report as formatted JSON."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target


def read_json_report(path):
    """Read a diagnostics JSON report."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def safe_report_type(report_type):
    """Return a safe report type for filenames."""
    value = re.sub(r"[^A-Za-z0-9_-]+", "_", str(report_type or "report")).strip("_")
    return value or "report"


def utc_timestamp_for_filename(now=None):
    """Return a UTC timestamp that is safe for filenames."""
    current = now or datetime.now(timezone.utc)
    return current.astimezone(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")


def make_timestamped_report_name(report_type, now=None):
    """Create a timestamped report filename."""
    return f"{utc_timestamp_for_filename(now)}_{safe_report_type(report_type)}.json"


def latest_report_path(report_type, report_root=DEFAULT_REPORT_ROOT):
    """Return the path for a latest report type."""
    return Path(report_root) / "latest" / f"{safe_report_type(report_type)}_latest.json"


def history_report_path(report_type, report_root=DEFAULT_REPORT_ROOT, now=None):
    """Return the path for a timestamped history report."""
    return Path(report_root) / "history" / make_timestamped_report_name(report_type, now=now)


def write_latest_report(report_type, report, report_root=DEFAULT_REPORT_ROOT):
    """Write the latest report for a report type."""
    return write_json_report(report, latest_report_path(report_type, report_root=report_root))


def write_history_report(report_type, report, report_root=DEFAULT_REPORT_ROOT, history_limit=DEFAULT_HISTORY_LIMIT):
    """Write a timestamped history report and prune older reports of the same type."""
    report_path = write_json_report(report, history_report_path(report_type, report_root=report_root))
    prune_history_reports(report_type, report_root=report_root, keep=history_limit)
    return report_path


def read_latest_report(report_type, report_root=DEFAULT_REPORT_ROOT):
    """Read the latest report for a report type."""
    return read_json_report(latest_report_path(report_type, report_root=report_root))


def list_history_reports(report_type, report_root=DEFAULT_REPORT_ROOT):
    """List history reports for a report type, newest first."""
    safe_type = safe_report_type(report_type)
    history_dir = Path(report_root) / "history"
    if not history_dir.exists():
        return []
    return sorted(history_dir.glob(f"*_{safe_type}.json"), reverse=True)


def prune_history_reports(report_type, report_root=DEFAULT_REPORT_ROOT, keep=DEFAULT_HISTORY_LIMIT):
    """Keep only the newest history reports for a report type."""
    reports = list_history_reports(report_type, report_root=report_root)
    for report_path in reports[max(0, keep) :]:
        report_path.unlink(missing_ok=True)
    return reports[: max(0, keep)]
