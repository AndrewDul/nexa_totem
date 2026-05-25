"""Shared component status helpers for NeXa ToTem."""

from datetime import datetime, timezone

STATUS_OK = "ok"
STATUS_WARNING = "warning"
STATUS_ERROR = "error"
STATUS_MISSING = "missing"
STATUS_UNKNOWN = "unknown"
STATUS_NOT_CHECKED = "not_checked"

VALID_STATUSES = {
    STATUS_OK,
    STATUS_WARNING,
    STATUS_ERROR,
    STATUS_MISSING,
    STATUS_UNKNOWN,
    STATUS_NOT_CHECKED,
}


def utc_now_iso():
    """Return the current UTC time in a compact ISO format."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def make_component_status(
    component,
    status=STATUS_UNKNOWN,
    message="Status has not been checked yet.",
    details=None,
    checked_at=None,
    source="diagnostics",
):
    """Create a plain dictionary that describes one component state."""
    clean_status = status if status in VALID_STATUSES else STATUS_UNKNOWN
    return {
        "component": component,
        "status": clean_status,
        "message": message,
        "details": details or {},
        "checked_at": checked_at or utc_now_iso(),
        "source": source,
    }


def combine_statuses(statuses):
    """Return the overall status for a list or dictionary of component statuses."""
    if isinstance(statuses, dict):
        values = list(statuses.values())
    else:
        values = list(statuses)

    if not values:
        return STATUS_NOT_CHECKED

    status_values = [item.get("status", STATUS_UNKNOWN) for item in values]
    if STATUS_ERROR in status_values:
        return STATUS_ERROR

    warning_states = {
        STATUS_WARNING,
        STATUS_MISSING,
        STATUS_UNKNOWN,
        STATUS_NOT_CHECKED,
    }
    if any(value in warning_states for value in status_values):
        return STATUS_WARNING

    return STATUS_OK
