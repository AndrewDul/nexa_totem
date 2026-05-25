"""Collectors that combine component diagnostics."""

from system.services.diagnostics.status import STATUS_OK, combine_statuses, utc_now_iso


def make_system_status(components, device="nexa_totem"):
    """Create the first combined system status shape for NeXa ToTem."""
    overall = combine_statuses(components)
    if overall == STATUS_OK:
        message = "NeXa ToTem system status looks normal."
    elif overall == "error":
        message = "NeXa ToTem system has errors."
    else:
        message = "NeXa ToTem system has warnings."

    return {
        "device": device,
        "status": overall,
        "message": message,
        "components": components,
        "checked_at": utc_now_iso(),
        "source": "diagnostics_collector",
    }
