"""Backend data shape for the future diagnostics panel."""

from system.services.diagnostics.status import combine_statuses, make_component_status, utc_now_iso
from system.services.diagnostics.reports import DEFAULT_REPORT_ROOT, latest_report_path, read_json_report

DEFAULT_LATEST_REPORTS = (
    "system_status",
    "pi_health",
    "audio_output",
    "camera_status",
    "camera_capture",
    "unit_tests",
)


def unavailable_report(report_type):
    """Return a small placeholder for a missing latest report."""
    return {
        "report": report_type,
        "status": "not_checked",
        "message": "Latest report is not available yet.",
        "details": {},
        "source": "diagnostic_panel_data",
    }


def read_latest_reports(report_types=DEFAULT_LATEST_REPORTS, report_root=DEFAULT_REPORT_ROOT):
    """Read latest reports without running hardware checks."""
    reports = {}
    for report_type in report_types:
        path = latest_report_path(report_type, report_root=report_root)
        if not path.exists():
            reports[report_type] = unavailable_report(report_type)
            continue
        try:
            reports[report_type] = read_json_report(path)
        except (OSError, ValueError):
            reports[report_type] = {
                "report": report_type,
                "status": "error",
                "message": "Latest report could not be read.",
                "details": {"path": str(path)},
                "source": "diagnostic_panel_data",
            }
    return reports


def build_components_from_reports(latest_reports):
    """Build component status data from saved latest reports."""
    system_status = latest_reports.get("system_status", {})
    if isinstance(system_status.get("components"), dict):
        return dict(system_status["components"])

    components = {}
    report_map = {
        "pi_health": "raspberry_pi",
        "audio_output": "usb_speaker",
        "camera_status": "camera_csi",
    }
    for report_name, component_name in report_map.items():
        report = latest_reports.get(report_name, {})
        if report.get("component") == component_name:
            components[component_name] = report
        else:
            components[component_name] = make_component_status(
                component=component_name,
                status="not_checked",
                message="Latest component report is not available yet.",
                source="diagnostic_panel_data",
            )
    return components


def build_diagnostic_panel_data(report_root=DEFAULT_REPORT_ROOT, report_types=DEFAULT_LATEST_REPORTS):
    """Build diagnostics panel data from saved JSON reports only."""
    latest_reports = read_latest_reports(report_types=report_types, report_root=report_root)
    components = build_components_from_reports(latest_reports)
    any_available = any(report.get("status") != "not_checked" for report in latest_reports.values())

    if components:
        status = combine_statuses(components)
    elif any_available:
        status = "unknown"
    else:
        status = "not_checked"

    message = "Diagnostic data is available." if any_available else "No saved diagnostic reports are available yet."
    return {
        "panel": "diagnostics",
        "status": status,
        "message": message,
        "latest_reports": latest_reports,
        "components": components,
        "checked_at": utc_now_iso(),
        "source": "diagnostic_panel_data",
    }

