#!/usr/bin/env python3
"""Validate the Godot LCD UI prototype files without running Godot."""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_DIR = REPO_ROOT / "system/ui/godot"

REQUIRED_SCRIPTS = [
    "main.gd",
    "theme.gd",
    "gesture_detector.gd",
    "navigation_controller.gd",
    "face_renderer.gd",
    "diagnostics_data.gd",
]

SCREEN_NAMES = [
    "Face Home",
    "Menu",
    "Clock",
    "Notification Control Center",
    "Diagnostics",
]

DIAGNOSTIC_TABS = [
    "Overview",
    "System",
    "Processes",
    "Benchmarks",
    "Camera",
    "Audio",
    "Reports",
    "Logs",
    "Network",
]


def read_text(path):
    try:
        return Path(path).read_text(encoding="utf-8")
    except OSError:
        return ""


def validate_godot_ui_files(project_dir=PROJECT_DIR):
    checks = []

    def add(name, passed, message):
        checks.append({"check": name, "passed": bool(passed), "message": message})

    project = Path(project_dir)
    project_godot = project / "project.godot"
    main_scene = project / "scenes/Main.tscn"
    scripts_dir = project / "scripts"
    run_dev = REPO_ROOT / "scripts/run/run_godot_ui_dev.sh"
    run_lcd = REPO_ROOT / "scripts/run/run_godot_ui_lcd.sh"

    project_text = read_text(project_godot)
    all_text = project_text + "\n" + read_text(main_scene)
    for script_name in REQUIRED_SCRIPTS:
        all_text += "\n" + read_text(scripts_dir / script_name)

    add("project_folder", project.exists(), "Godot project folder exists.")
    add("project_godot", project_godot.exists(), "project.godot exists.")
    add("main_scene", main_scene.exists(), "Main.tscn exists.")
    for script_name in REQUIRED_SCRIPTS:
        add(f"script_{script_name}", (scripts_dir / script_name).exists(), f"{script_name} exists.")

    add("resolution_width", "viewport_width=640" in project_text, "Viewport width is 640.")
    add("resolution_height", "viewport_height=480" in project_text, "Viewport height is 480.")
    add("not_resizable", "resizable=false" in project_text, "Window is marked not resizable.")
    add("not_fullscreen_default", "fullscreen=true" not in project_text.lower(), "Fullscreen is not configured by default.")
    add("windowed_intent", "--windowed" in read_text(run_dev), "Development launcher uses windowed mode.")
    add("fixed_resolution_intent", "--resolution 640x480" in read_text(run_dev), "Development launcher uses 640x480.")

    for screen_name in SCREEN_NAMES:
        add(f"screen_{screen_name}", screen_name in all_text, f"{screen_name} is represented.")
    for tab_name in DIAGNOSTIC_TABS:
        add(f"tab_{tab_name}", tab_name in all_text, f"{tab_name} tab is represented.")

    add("run_dev_exists", run_dev.exists(), "Development launcher exists.")
    add("run_lcd_exists", run_lcd.exists(), "LCD launcher placeholder exists.")
    add("run_dev_no_fullscreen", "--fullscreen" not in read_text(run_dev), "Development launcher does not use fullscreen.")

    passed = all(item["passed"] for item in checks)
    return {
        "validator": "godot_ui_files",
        "status": "ok" if passed else "error",
        "message": "Godot UI file validation passed." if passed else "Godot UI file validation failed.",
        "checks": checks,
        "source": "check_godot_ui_files",
    }


def main():
    parser = argparse.ArgumentParser(description="Validate Godot UI prototype files.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    args = parser.parse_args()

    result = validate_godot_ui_files()
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(result["message"])
        for check in result["checks"]:
            marker = "OK" if check["passed"] else "FAIL"
            print(f"- {marker}: {check['message']}")

    raise SystemExit(0 if result["status"] == "ok" else 1)


if __name__ == "__main__":
    main()
