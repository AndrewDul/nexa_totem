"""JSON report helpers for diagnostics."""

import json
from pathlib import Path


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

