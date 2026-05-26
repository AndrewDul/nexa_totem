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
    main_text = read_text(scripts_dir / "main.gd")
    face_text = read_text(scripts_dir / "face_renderer.gd")
    gesture_text = read_text(scripts_dir / "gesture_detector.gd")
    all_text = project_text + "\n" + read_text(main_scene)
    scripts_text = ""
    for script_name in REQUIRED_SCRIPTS:
        script_text = read_text(scripts_dir / script_name)
        scripts_text += "\n" + script_text
        all_text += "\n" + script_text

    add("project_folder", project.exists(), "Godot project folder exists.")
    add("project_godot", project_godot.exists(), "project.godot exists.")
    add("main_scene", main_scene.exists(), "Main.tscn exists.")
    for script_name in REQUIRED_SCRIPTS:
        add(f"script_{script_name}", (scripts_dir / script_name).exists(), f"{script_name} exists.")

    add("resolution_width", "viewport_width=640" in project_text, "Viewport width is 640.")
    add("resolution_height", "viewport_height=480" in project_text, "Viewport height is 480.")
    add("not_resizable", "resizable=false" in project_text, "Window is marked not resizable.")
    add("max_fps_30", "run/max_fps=30" in project_text or "application/run/max_fps=30" in project_text, "Project caps runtime at 30 FPS.")
    add("not_fullscreen_default", "fullscreen=true" not in project_text.lower(), "Fullscreen is not configured by default.")
    add("windowed_intent", "--windowed" in read_text(run_dev), "Development launcher uses windowed mode.")
    add("fixed_resolution_intent", "--resolution 640x480" in read_text(run_dev), "Development launcher uses 640x480.")

    for screen_name in SCREEN_NAMES:
        add(f"screen_{screen_name}", screen_name in all_text, f"{screen_name} is represented.")
    for tab_name in DIAGNOSTIC_TABS:
        add(f"tab_{tab_name}", tab_name in all_text, f"{tab_name} tab is represented.")

    add("no_rect2_translated", ".translated(" not in scripts_text, "Godot scripts do not use Rect2.translated.")
    add("local_runtime_helpers", "func _draw_card" in main_text and "func _draw_pill" in main_text and "func _draw_soft_panel" in main_text and "func _draw_tile" in main_text, "Local callable drawing helpers exist in main.gd.")
    add("no_themescript_runtime_helper_calls", "ThemeScript.draw_card" not in main_text and "ThemeScript.draw_pill" not in main_text and "ThemeScript.draw_soft_panel" not in main_text and "ThemeScript.draw_tile" not in main_text, "main.gd no longer calls ThemeScript drawing helpers at runtime.")
    add("rounded_style_helpers", "draw_card" in all_text and "draw_pill" in all_text and "draw_tile" in all_text, "Rounded card, pill, and tile helpers exist.")
    add("menu_tile_cards", "_draw_tile(rect" in main_text and "MENU_TILES" in main_text, "Menu tile card drawing is represented.")
    add("menu_tile_width", "284.0" in main_text, "Menu tile width 284 is represented.")
    add("menu_tile_height", "72.0" in main_text, "Menu tile height 72 is represented.")
    add("menu_two_columns", "index % 2" in main_text and "300.0" in main_text, "Menu uses two columns.")
    for subtitle in ["Clock", "Focus", "Alerts", "Events", "To-do", "Play", "System", "Setup"]:
        add(f"menu_subtitle_{subtitle}", f'"subtitle": "{subtitle}"' in main_text, f"Menu subtitle {subtitle} is represented.")
    add("control_center_cards", "Control Center" in main_text and "var controls: Array" in main_text and "_draw_notification" in main_text, "Control Center card drawing is represented.")
    add("no_visible_face_home_label", '_draw_text("Face Home"' not in main_text, "Face Home label is not drawn on the home screen.")
    add("vertical_eyes", "_draw_vertical_capsule" in face_text and "_draw_bean_eye" in face_text, "Vertical bean eyes are represented.")
    add("blink_logic", "BLINK_PERIOD" in face_text and "BLINK_DURATION" in face_text and "fmod" in face_text, "Idle blink cycle logic is represented.")
    add("eye_glow_reduced", "width + 20.0" not in face_text and "height + 24.0" not in face_text, "Strong eye glow/halo layers are removed or reduced.")
    add("scroll_offsets", "diagnostic_scroll_y" in main_text and "control_center_scroll_y" in main_text, "Diagnostics and Control Center scroll offsets are represented.")
    add("scrollbar_helper", "func _draw_scrollbar" in main_text, "Scrollbar drawing helper is represented.")
    add("scroll_clamp", "clampf(diagnostic_scroll_y" in main_text and "clampf(control_center_scroll_y" in main_text, "Scroll clamp logic is represented.")
    add("mouse_wheel_scroll", "MOUSE_BUTTON_WHEEL_UP" in main_text and "MOUSE_BUTTON_WHEEL_DOWN" in main_text, "Mouse wheel scrolling is represented.")
    add("reduced_panel_fonts", '_draw_text("Menu", Vector2(32, 52), 27' in main_text and '_draw_text("Control Center", Vector2(44, 64), 26' in main_text and '_draw_text("Diagnostics", Vector2(26, 40), 26' in main_text, "Panel font sizes were reduced.")
    add("redraw_throttling", "TARGET_REDRAW_FPS" in main_text and "REDRAW_INTERVAL" in main_text and "redraw_accumulator" in main_text, "Redraw throttling is represented.")
    add("transition_logic", "transition_progress" in main_text and "_draw_transition" in main_text and "TRANSITION_SECONDS" in main_text, "Lightweight transition logic is represented.")
    add("fast_transitions", "TRANSITION_SECONDS := 0.14" in main_text and "CLOSE_TRANSITION_SECONDS := 0.10" in main_text, "Panel transition durations are 0.16 seconds or less.")
    add("overlay_transition_rendering", "transition_overlay" in main_text and "_draw_overlay_screen" in main_text, "Transitions draw Face Home plus one overlay panel.")
    add("reverse_swipe_close_menu", 'nav.current_screen == "Menu" and action == "swipe_right"' in main_text, "Menu reverse swipe closes to Face Home.")
    add("reverse_swipe_close_clock", 'nav.current_screen == "Clock" and action == "swipe_left"' in main_text, "Clock reverse swipe closes to Face Home.")
    add("reverse_swipe_close_control_center", 'nav.current_screen == "Notification Control Center" and action == "swipe_up"' in main_text, "Control Center reverse swipe closes to Face Home.")
    add("swipe_up_detected", '"swipe_up"' in gesture_text, "Gesture detector supports swipe up.")
    for term in ["draw_card", "rounded", "transition", "Face Home", "Menu", "Clock", "Notification Control Center", "Diagnostics"]:
        add(f"premium_term_{term}", term in all_text, f"{term} is represented in polished UI files.")

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
