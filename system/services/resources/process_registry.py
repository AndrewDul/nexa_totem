"""Known NeXa process definitions."""

NEXA_PROCESS_REGISTRY = [
    {
        "component": "nexa_backend",
        "display_name": "NeXa Backend",
        "process_type": "python",
        "expected": "future",
        "match_keywords": ["nexa_backend", "run_diagnostics.py"],
        "notes": "Main local backend process for future runtime services.",
    },
    {
        "component": "nexa_godot_lcd_ui",
        "display_name": "Godot LCD UI",
        "process_type": "godot",
        "expected": "planned",
        "match_keywords": ["godot", "nexa_godot_lcd_ui", "lcd_ui"],
        "notes": "Local LCD UI process planned for the display.",
    },
    {
        "component": "nexa_web_panel",
        "display_name": "Web Panel",
        "process_type": "web",
        "expected": "planned",
        "match_keywords": ["nexa_web_panel", "web_panel"],
        "notes": "Future local web panel process.",
    },
    {
        "component": "nexa_camera_service",
        "display_name": "Camera Service",
        "process_type": "camera",
        "expected": "future",
        "match_keywords": ["nexa_camera_service", "camera_status.py", "capture_camera_test.py"],
        "notes": "Future camera service and current camera diagnostic scripts.",
    },
    {
        "component": "nexa_sensor_service",
        "display_name": "Sensor Service",
        "process_type": "sensor",
        "expected": "future",
        "match_keywords": ["nexa_sensor_service"],
        "notes": "Future sensor reading service.",
    },
    {
        "component": "nexa_remote_link",
        "display_name": "Remote Link",
        "process_type": "remote",
        "expected": "future",
        "match_keywords": ["nexa_remote_link", "remote_link"],
        "notes": "Future wireless remote link process.",
    },
    {
        "component": "nexa_diagnostics_runner",
        "display_name": "Diagnostics Runner",
        "process_type": "diagnostics",
        "expected": "available",
        "match_keywords": ["run_diagnostics.py", "check_nexa_resources.py"],
        "notes": "Diagnostics runner and resource check scripts.",
    },
    {
        "component": "nexa_test_runner",
        "display_name": "Test Runner",
        "process_type": "test",
        "expected": "available",
        "match_keywords": ["run_unit_tests.py", "run_all_checks.py", "run_resource_benchmark.py"],
        "notes": "Local test and benchmark runner scripts.",
    },
]


def get_process_registry():
    """Return known NeXa process definitions."""
    return [dict(item) for item in NEXA_PROCESS_REGISTRY]


def get_process_definition(component):
    """Return one process definition by component name."""
    for item in NEXA_PROCESS_REGISTRY:
        if item["component"] == component:
            return dict(item)
    return None

