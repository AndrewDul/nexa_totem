"""Shared validation result helpers for NeXa ToTem diagnostics."""

import time

from system.services.diagnostics.status import STATUS_UNKNOWN, VALID_STATUSES, utc_now_iso


def make_validation_result(
    validation,
    status=STATUS_UNKNOWN,
    message="Validation has not run yet.",
    started_at=None,
    finished_at=None,
    duration_ms=None,
    details=None,
    source="diagnostics_validation",
):
    """Create a plain dictionary that describes one validation run."""
    clean_status = status if status in VALID_STATUSES else STATUS_UNKNOWN
    return {
        "validation": validation,
        "status": clean_status,
        "message": message,
        "started_at": started_at or utc_now_iso(),
        "finished_at": finished_at or utc_now_iso(),
        "duration_ms": duration_ms,
        "details": details or {},
        "source": source,
    }


def validation_status_from_component_status(component_status):
    """Return a validation status from a component status dictionary."""
    if not component_status:
        return STATUS_UNKNOWN
    status = component_status.get("status", STATUS_UNKNOWN)
    return status if status in VALID_STATUSES else STATUS_UNKNOWN


def timed_validation(validation, callback, source="diagnostics_validation"):
    """Run a validation callback and return a validation result."""
    started_at = utc_now_iso()
    start = time.monotonic()
    try:
        result = callback()
    except Exception as exc:
        finished_at = utc_now_iso()
        return make_validation_result(
            validation=validation,
            status="error",
            message=f"{validation} validation failed.",
            started_at=started_at,
            finished_at=finished_at,
            duration_ms=int((time.monotonic() - start) * 1000),
            details={"error": str(exc)},
            source=source,
        )

    finished_at = utc_now_iso()
    if isinstance(result, dict):
        status = validation_status_from_component_status(result)
        message = result.get("message", "Validation finished.")
        details = result.get("details", {})
    else:
        status = "ok"
        message = "Validation finished."
        details = {"result": result}

    return make_validation_result(
        validation=validation,
        status=status,
        message=message,
        started_at=started_at,
        finished_at=finished_at,
        duration_ms=int((time.monotonic() - start) * 1000),
        details=details,
        source=source,
    )

