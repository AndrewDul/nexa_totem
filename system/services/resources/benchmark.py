"""Benchmark helpers for NeXa component checks."""

import time

from system.services.diagnostics.status import combine_statuses, utc_now_iso


def make_benchmark_result(
    benchmark,
    status="unknown",
    duration_ms=None,
    message="Benchmark has not run yet.",
    details=None,
    source="resource_benchmark",
):
    """Create a benchmark result dictionary."""
    return {
        "benchmark": benchmark,
        "status": status,
        "duration_ms": duration_ms,
        "message": message,
        "details": details or {},
        "source": source,
    }


def time_operation(name, callable_object, source=None):
    """Time one operation and return a benchmark result."""
    start = time.monotonic()
    try:
        result = callable_object()
    except Exception as exc:
        return make_benchmark_result(
            name,
            status="error",
            duration_ms=int((time.monotonic() - start) * 1000),
            message=f"{name} failed.",
            details={"error": str(exc)},
            source=source or name,
        )

    duration_ms = int((time.monotonic() - start) * 1000)
    status = result.get("status", "ok") if isinstance(result, dict) else "ok"
    if status == "missing":
        status = "warning"
    message = f"{name} completed."
    details = {}
    if isinstance(result, dict):
        details = {
            "result_status": result.get("status"),
            "result_message": result.get("message"),
            "result_source": result.get("source"),
        }
    return make_benchmark_result(
        name,
        status=status,
        duration_ms=duration_ms,
        message=message,
        details=details,
        source=source or name,
    )


def combine_benchmark_results(results):
    """Combine benchmark results into one report."""
    values = list(results)
    status = combine_statuses(values)
    slowest = max(values, key=lambda item: item.get("duration_ms") or 0, default=None)
    return {
        "benchmark_report": "resource_benchmark",
        "status": status,
        "message": "Resource benchmarks completed." if values else "No resource benchmarks ran.",
        "benchmarks": values,
        "summary": {
            "benchmark_count": len(values),
            "slowest_benchmark": slowest.get("benchmark") if slowest else None,
            "slowest_duration_ms": slowest.get("duration_ms") if slowest else None,
            "total_duration_ms": sum(item.get("duration_ms") or 0 for item in values),
        },
        "checked_at": utc_now_iso(),
        "source": "resource_benchmark",
    }

