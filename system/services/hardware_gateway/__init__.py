"""Hardware gateway state helpers for NeXa ToTem."""

from system.services.hardware_gateway.hardware_state import HardwareStateStore, parse_arduino_raw_line

latest_hardware_state = HardwareStateStore()

__all__ = ["HardwareStateStore", "latest_hardware_state", "parse_arduino_raw_line"]
