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
    "diagnostics_api_client.gd",
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
    run_with_api = REPO_ROOT / "scripts/run/run_godot_ui_with_api_dev.sh"
    run_lcd = REPO_ROOT / "scripts/run/run_godot_ui_lcd.sh"
    run_api = REPO_ROOT / "scripts/run/run_diagnostics_api.py"
    live_api = REPO_ROOT / "system/services/diagnostics/live_api.py"
    camera_preview = REPO_ROOT / "system/services/diagnostics/camera_preview.py"
    settings_store = REPO_ROOT / "system/services/settings/settings_store.py"
    study_store = REPO_ROOT / "system/services/study/study_store.py"
    reminders_store = REPO_ROOT / "system/services/reminders/reminders_store.py"
    api_client = scripts_dir / "diagnostics_api_client.gd"

    project_text = read_text(project_godot)
    main_text = read_text(scripts_dir / "main.gd")
    face_text = read_text(scripts_dir / "face_renderer.gd")
    gesture_text = read_text(scripts_dir / "gesture_detector.gd")
    api_client_text = read_text(api_client)
    live_api_text = read_text(live_api)
    camera_preview_text = read_text(camera_preview)
    settings_store_text = read_text(settings_store)
    study_store_text = read_text(study_store)
    reminders_store_text = read_text(reminders_store)
    live_collectors_text = read_text(REPO_ROOT / "system/services/diagnostics/live_collectors.py")
    job_runner_text = read_text(REPO_ROOT / "system/services/diagnostics/job_runner.py")
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
    add("renderer_gl_compatibility", 'renderer/rendering_method="gl_compatibility"' in project_text, "Project uses Godot Compatibility renderer.")
    add("renderer_gl_compatibility_mobile", 'renderer/rendering_method.mobile="gl_compatibility"' in project_text, "Project mobile rendering method uses Compatibility renderer.")
    add("not_fullscreen_default", "fullscreen=true" not in project_text.lower(), "Fullscreen is not configured by default.")
    add("windowed_intent", "--windowed" in read_text(run_dev), "Development launcher uses windowed mode.")
    add("fixed_resolution_intent", "--resolution 640x480" in read_text(run_dev), "Development launcher uses 640x480.")
    add("dev_runner_rendering_driver", "--rendering-driver" in read_text(run_dev) and "opengl3" in read_text(run_dev), "Development launcher defaults to OpenGL rendering driver.")
    add("api_runner_rendering_driver", "--rendering-driver" in read_text(run_with_api) or "NEXA_GODOT_RENDERING_DRIVER" in read_text(run_with_api), "API development launcher preserves OpenGL rendering driver.")
    add("diagnostics_api_client_exists", api_client.exists(), "Godot diagnostics API client exists.")
    add("run_diagnostics_api_exists", run_api.exists(), "Diagnostics API runner exists.")
    add("live_api_exists", live_api.exists(), "Diagnostics live API exists.")
    add("camera_preview_exists", camera_preview.exists(), "Camera live preview worker exists.")
    add("settings_store_exists", settings_store.exists(), "Settings store exists.")
    add("study_store_exists", study_store.exists(), "Study store exists.")
    add("reminders_store_exists", reminders_store.exists(), "Reminders store exists.")
    add("api_localhost", "127.0.0.1" in live_api_text and "8769" in live_api_text, "API binds localhost port 8769.")

    for screen_name in SCREEN_NAMES:
        add(f"screen_{screen_name}", screen_name in all_text, f"{screen_name} is represented.")
    for tab_name in DIAGNOSTIC_TABS:
        add(f"tab_{tab_name}", tab_name in all_text, f"{tab_name} tab is represented.")

    add("no_rect2_translated", ".translated(" not in scripts_text, "Godot scripts do not use Rect2.translated.")
    add("godot_no_os_execute", "OS.execute" not in scripts_text, "Godot does not execute shell commands.")
    add("local_runtime_helpers", "func _draw_card" in main_text and "func _draw_pill" in main_text and "func _draw_soft_panel" in main_text and "func _draw_tile" in main_text, "Local callable drawing helpers exist in main.gd.")
    add("no_themescript_runtime_helper_calls", "ThemeScript.draw_card" not in main_text and "ThemeScript.draw_pill" not in main_text and "ThemeScript.draw_soft_panel" not in main_text and "ThemeScript.draw_tile" not in main_text, "main.gd no longer calls ThemeScript drawing helpers at runtime.")
    add("settings_api_endpoints", "/api/settings" in live_api_text and "/api/settings/update" in live_api_text and "/api/settings/update-many" in live_api_text and "/api/privacy/pin/set" in live_api_text and "/api/privacy/pin/verify" in live_api_text and "/api/privacy/status" in live_api_text, "Settings and privacy API endpoints exist.")
    add("study_api_endpoints", "/api/study/overview" in live_api_text and "/api/study/pomodoro/start" in live_api_text and "/api/study/flashcards/decks/create" in live_api_text and "/api/study/quizzes/create" in live_api_text and "/api/study/languages/lists/create" in live_api_text and "/api/study/stats" in live_api_text, "Study API endpoints exist.")
    add("reminders_api_endpoints", all(endpoint in live_api_text for endpoint in ["/api/reminders/overview", "/api/reminders/list", "/api/reminders/due", "/api/reminders/create", "/api/reminders/update", "/api/reminders/delete", "/api/reminders/dismiss", "/api/reminders/mark-triggered", "/api/reminders/settings/stats"]), "Reminders API endpoints exist.")
    add("study_sqlite_store", "sqlite3" in study_store_text and "var/data/study/nexa_study.db" in study_store_text and "NEXA_STUDY_DB_PATH" in study_store_text, "Study store uses local SQLite with test DB override.")
    add("reminders_sqlite_store", "sqlite3" in reminders_store_text and "var/data/reminders/nexa_reminders.db" in reminders_store_text and "NEXA_REMINDERS_DB_PATH" in reminders_store_text and "PRAGMA user_version = 1" in reminders_store_text, "Reminders store uses local SQLite with schema version and test DB override.")
    add("study_duplicate_similar", "normalize_name" in study_store_text and "SequenceMatcher" in study_store_text and '"duplicate"' in study_store_text and '"similar"' in study_store_text, "Study store has duplicate and similar detection.")
    add("pin_hash_hidden", "pin_hash" in settings_store_text and "pin_salt" in settings_store_text and "safe_settings" in settings_store_text and "SENSITIVE_KEYS" in settings_store_text, "Settings API can remove PIN hash and salt.")
    add("pin_four_digits", "valid_pin" in settings_store_text and "len(pin) == 4" in settings_store_text and "pin.isdigit()" in settings_store_text, "PIN is constrained to four digits.")
    add("private_settings", "private_notifications_enabled" in settings_store_text and "private_reminders_enabled" in settings_store_text, "Private notification and reminder settings exist.")
    add("no_real_power_commands", "subprocess" not in settings_store_text and "poweroff" not in live_api_text and "shutdown" not in live_api_text and "reboot(" not in live_api_text, "Settings/safety API does not run real power commands.")
    add("api_offline_handling", "api_offline" in api_client_text and "API offline" in main_text, "Godot has API offline handling.")
    add("lazy_polling", "_update_api_polling" in main_text and "_request_active_diagnostics_tab" in main_text, "Godot has lazy active-tab polling markers.")
    add("control_center_light_endpoint", "/api/control-center" in main_text, "Control Center uses the lightweight control-center endpoint.")
    add("control_center_delayed_refresh", "control_center_refresh_pending" in main_text and "after transition" in main_text, "Control Center refresh is delayed until after transition.")
    add("control_center_cached_first", "cached data first" in main_text and "api.request_get(\"/api/control-center\")" not in main_text.split("func _open_control_center", 1)[1].split("func _open_diagnostics", 1)[0], "Control Center opens from cached/local defaults.")
    add("control_center_wifi_detail", "network_detail_data" in main_text and "_draw_wifi_detail_safe" in main_text and 'selected_control_detail = "wifi"' in main_text, "Control Center Wi-Fi detail panel is represented.")
    add("control_center_network_lazy", 'api.request_get("/api/network")' in main_text and 'api.request_get("/api/network")' not in main_text.split("func _open_control_center", 1)[1].split("func _open_diagnostics", 1)[0], "Control Center requests network details outside the open transition.")
    add("control_center_no_full_network_scan", "saved_networks" not in live_collectors_text.split("def control_center_data", 1)[1], "Control Center data avoids full saved/available Wi-Fi lists.")
    add("brightness_slider_drag", "brightness_slider_rect" in main_text and "slider_drag_kind == \"brightness\"" in main_text, "Brightness slider hit and drag logic exists.")
    add("sound_slider_drag", "sound_slider_rect" in main_text and "slider_drag_kind == \"sound\"" in main_text, "Sound slider hit and drag logic exists.")
    add("sound_no_raw_null_display", '"Sound", "value": str(sound_percent)' in main_text and 'str(control_center_data.get("sound_percent", "Unknown"))' not in main_text, "Sound tile does not display raw null.")
    add("overview_cpu_gpu", "CPU Use" in main_text and "gpu_usage_status" in live_collectors_text and "gpu_usage_percent" in live_collectors_text, "Overview includes CPU usage and GPU status.")
    add("benchmark_safe_dictionary", "result_raw = active_tab_data.get(\"result\", {})" in main_text and "if result_raw is Dictionary" in main_text, "Benchmark result dictionary handles null safely.")
    add("api_arrays_safe", "if rows_raw is Array" in main_text and "if saved_raw is Array" in main_text and "if available_raw is Array" in main_text, "API-derived arrays handle null safely.")
    add("camera_preview_endpoints", "/api/camera/preview/start" in live_api_text and "/api/camera/preview/stop" in live_api_text and "/api/camera/preview/status" in live_api_text, "Camera preview endpoints exist.")
    add("camera_frame_handling", "request_frame" in api_client_text and "_on_camera_frame_received" in main_text and "camera_preview_status" in main_text, "Camera preview frame/status handling exists.")
    add("camera_preview_stop", "_stop_camera_preview" in main_text and "stale_timeout_seconds" in camera_preview_text, "Camera preview stops on close/off or backend stale timeout.")
    add("no_pilot_label", '"Pilot"' not in main_text, "Pilot label is not visible in Godot UI.")
    add("remote_labels", "Remote Wi-Fi" in main_text and '"Remote"' in main_text, "Remote Wi-Fi and Remote labels are represented.")
    add("overview_compact_layout", "204.0 + float(int(index / 2)) * 70.0" not in main_text and "194.0 + float(int(index / 2)) * 50.0" in main_text and "250.0, 42.0" in main_text, "Overview uses compact cards inside Diagnostics panel.")
    add("camera_compact_rows", "_draw_info_row_compact" in main_text and "width: float" in main_text and "x + width" in main_text, "Camera tab uses compact right-column rows.")
    add("camera_buttons_compact", "Rect2(350, 316 - offset_y, 190, 34)" in main_text and "Rect2(350, 356 - offset_y, 190, 34)" in main_text, "Camera buttons stay inside the content panel.")
    add("camera_live_worker", "class CameraPreviewWorker" in camera_preview_text and "preview_thread" in camera_preview_text and "Picamera2" in camera_preview_text, "Camera preview uses a live worker/session.")
    add("rpicam_vid_mjpeg", "rpicam-vid" in camera_preview_text and "rpicam_vid_mjpeg" in camera_preview_text and "subprocess.Popen" in camera_preview_text, "Camera preview prefers persistent rpicam-vid MJPEG worker.")
    add("jpeg_marker_parsing", "JPEG_SOI" in camera_preview_text and "JPEG_EOI" in camera_preview_text and "extract_jpeg_frames" in camera_preview_text, "Camera preview parses JPEG SOI/EOI markers.")
    add("picamera2_guarded", "importlib.import_module(\"picamera2\")" in camera_preview_text and "except Exception" in camera_preview_text, "Picamera2 import is guarded.")
    add("no_repeated_still_preview", "rpicam-still" not in camera_preview_text and "select_capture_command" not in live_api_text, "Preview does not use repeated rpicam-still captures.")
    add("camera_layout_fixed", "Rect2(44, 196 - offset_y, 270, 160)" in main_text and "Rect2(350, 316 - offset_y, 190, 34)" in main_text, "Camera tab uses fixed preview and right action column.")
    add("network_lists", "saved_networks" in live_collectors_text and "available_networks" in live_collectors_text and "actions_are_dry_run" in live_collectors_text and "remote_connected" in live_collectors_text, "Network endpoint returns saved and available networks plus remote state.")
    add("benchmark_result_rows", '"results": rows' in job_runner_text and "duration_ms" in job_runner_text and "result.get(\"results\"" in main_text, "Benchmark job returns visible result rows.")
    add("benchmark_on_request", "/api/benchmarks/run" in live_api_text and "start_benchmarks" in live_api_text, "Benchmarks run on request only.")
    add("report_on_request", "/api/reports/generate" in live_api_text and "start_report" in live_api_text, "Reports generate on request only.")
    add("active_full_blue", "Color(0.11, 0.32, 0.66, 1.0)" in main_text, "Active/pressed cards use full-blue styling.")
    add("rounded_style_helpers", "draw_card" in all_text and "draw_pill" in all_text and "draw_tile" in all_text, "Rounded card, pill, and tile helpers exist.")
    add("menu_tile_cards", "_draw_tile(rect" in main_text and "MENU_TILES" in main_text, "Menu tile card drawing is represented.")
    add("menu_tile_width", "284.0" in main_text, "Menu tile width 284 is represented.")
    add("menu_tile_height", "72.0" in main_text, "Menu tile height 72 is represented.")
    add("menu_two_columns", "index % 2" in main_text and "300.0" in main_text, "Menu uses two columns.")
    menu_tap_func = main_text.split("func _handle_menu_tap", 1)[1].split("func _handle_diagnostics_tap", 1)[0] if "func _handle_menu_tap" in main_text and "func _handle_diagnostics_tap" in main_text else ""
    add("menu_time_opens_clock", 'tile["title"] == "Time"' in menu_tap_func and "_open_clock()" in menu_tap_func, "Menu Time tile opens Clock.")
    add("menu_study_opens_study", 'tile["title"] == "Study"' in menu_tap_func and '_open_study("home")' in menu_tap_func, "Menu Study tile opens Study.")
    for subtitle in ["Clock", "Focus", "Alerts", "Events", "To-do", "Play", "System", "Setup"]:
        add(f"menu_subtitle_{subtitle}", f'"subtitle": "{subtitle}"' in main_text, f"Menu subtitle {subtitle} is represented.")
    add("control_center_cards", "Control Center" in main_text and "var controls: Array" in main_text and "_draw_notification" in main_text, "Control Center card drawing is represented.")
    add("control_center_safe_mode", "CONTROL_CENTER_SAFE_MODE := true" in main_text and "_draw_control_center_safe" in main_text, "Control Center safe drawing mode exists.")
    add("settings_ui", "SETTINGS_TILES" in main_text and 'nav.current_screen = "Settings"' in main_text and "_draw_settings_home" in main_text, "Settings UI home exists.")
    add("settings_pages", all(page in main_text for page in ["Appearance", "Notifications", "Modes", "Quick Shelf", "Display", "Sound", "Network", "Remote", "Privacy", "Diagnostics", "Safety", "Exit NeXa"]), "Settings MVP pages are represented.")
    add("settings_lists", "COLOR_OPTIONS" in main_text and "MODE_OPTIONS" in main_text and "QUICK_SHELF_OPTIONS" in main_text, "Settings color, mode, and Quick Shelf lists are represented.")
    add("settings_api_client", "/api/settings" in main_text and "/api/settings/update" in main_text and "/api/privacy/pin/set" in main_text and "/api/privacy/pin/verify" in main_text, "Godot requests settings and PIN endpoints.")
    add("settings_tap_routing", 'if nav.current_screen == "Settings":' in main_text and "_handle_settings_tap(position)" in main_text, "Settings screen is included in tap routing.")
    add("settings_tile_hitbox_matches_draw", "func _settings_tile_rect" in main_text and "var rect: Rect2 = _settings_tile_rect(index)" in main_text, "Settings Home draw and hitbox use the same tile rect helper.")
    add("settings_scroll_does_not_eat_taps", "_settings_scrollbar_hit_rect" in main_text and 'nav.current_screen == "Settings" and _settings_scroll_rect().has_point(position) and _settings_max_scroll() > 0.0' not in main_text, "Settings scroll drag does not consume normal tile taps.")
    add("settings_row_updates", "_handle_settings_detail_tap" in main_text and "_settings_update" in main_text and "settings_data[section] = section_data" in main_text, "Settings rows update local settings and post to API.")
    add("settings_quick_shelf_toggle", "_handle_quick_shelf_tap" in main_text and "enabled_tiles" in main_text, "Quick Shelf selection toggles are represented.")
    add("settings_pin_keypad", "_handle_pin_tap" in main_text and "_pin_submit" in main_text and "/api/privacy/lock" in main_text, "Privacy PIN keypad and lock actions are represented.")
    add("appearance_live_preview", "_settings_color" in main_text and "face.draw_face(self, Vector2(WIDTH, HEIGHT), elapsed" in main_text and "tile_accent_color" in main_text, "Appearance settings affect live face/accent preview.")
    add("appearance_background", "_theme_background_color" in main_text and "background_color" in main_text and "_draw_menu" in main_text, "Appearance background color is used in drawing.")
    add("appearance_dropdowns", "settings_dropdown_open" in main_text and "_draw_settings_dropdown" in main_text and "_handle_settings_dropdown_tap" in main_text, "Appearance dropdown option lists are represented.")
    add("appearance_presets", "_apply_appearance_preset" in main_text and "_appearance_preset_values" in main_text and "/api/settings/update-many" in main_text, "Appearance presets update multiple keys.")
    clock_color_keys = ["time_color", "hour_color", "minute_color", "second_color", "date_color", "day_color", "month_color", "year_color"]
    add("appearance_clock_color_rows", all(key in main_text for key in clock_color_keys) and all(title in main_text for title in ["Time color", "Hour color", "Minute color", "Second color", "Date color", "Day color", "Month color", "Year color"]), "Appearance rows include Clock time/date color settings.")
    add("appearance_time_group_update", 'key == "time_color"' in main_text and '"key": "hour_color"' in main_text and '"key": "minute_color"' in main_text and '"key": "second_color"' in main_text and "_settings_update_many" in main_text, "Time color uses grouped update-many behavior.")
    add("appearance_date_group_update", 'key == "date_color"' in main_text and '"key": "day_color"' in main_text and '"key": "month_color"' in main_text and '"key": "year_color"' in main_text and "_settings_update_many" in main_text, "Date color uses grouped update-many behavior.")
    add("settings_store_clock_color_defaults", all(f'"{key}"' in settings_store_text for key in clock_color_keys), "Settings store defaults include Clock time/date color keys.")
    add("settings_store_clock_color_validation", "APPEARANCE_COLOR_KEYS" in settings_store_text and all(f'"{key}"' in settings_store_text for key in clock_color_keys) and "invalid_color" in settings_store_text, "Settings store validates Clock time/date color keys.")
    add("appearance_presets_clock_colors", all(f'"{key}"' in main_text for key in clock_color_keys) and all(preset in main_text for preset in ["NeXa Blue", "Apple Dark", "Warm Desk", "Focus Green", "Night Red", "Soft Pink", "Minimal White"]), "Appearance presets include Clock time/date colors.")
    add("quick_shelf_screen", '"Quick Shelf"' in main_text and "_open_quick_shelf" in main_text and "_draw_quick_shelf" in main_text, "Quick Shelf panel screen exists.")
    add("quick_shelf_swipe", "swipe_up" in main_text and "quick_open" in main_text and "quick_close" in main_text, "Quick Shelf opens with swipe up and closes with swipe down/Escape.")
    add("quick_shelf_saved_tiles", "_settings_enabled_quick_shelf" in main_text and "enabled_tiles" in main_text and "_quick_shelf_tile_rect" in main_text, "Quick Shelf uses selected settings tiles.")
    add("quick_shelf_actions", "_activate_quick_shelf_tile" in main_text and "_open_diagnostics_tab" in main_text and "_open_settings_page" in main_text, "Quick Shelf tile click actions are represented.")
    add("quick_shelf_tap_routing", 'if nav.current_screen == "Quick Shelf":' in main_text and "_handle_quick_shelf_panel_tap(position)" in main_text, "Quick Shelf screen routes taps to the panel tap handler.")
    quick_tap_func = main_text.split("func _handle_quick_shelf_panel_tap", 1)[1].split("func _activate_quick_shelf_tile", 1)[0] if "func _handle_quick_shelf_panel_tap" in main_text and "func _activate_quick_shelf_tile" in main_text else ""
    quick_draw_func = main_text.split("func _draw_quick_shelf", 1)[1].split("func _quick_shelf_tile_rect", 1)[0] if "func _draw_quick_shelf" in main_text and "func _quick_shelf_tile_rect" in main_text else ""
    quick_action_func = main_text.split("func _activate_quick_shelf_tile", 1)[1].split("func _open_diagnostics_tab", 1)[0] if "func _activate_quick_shelf_tile" in main_text and "func _open_diagnostics_tab" in main_text else ""
    scroll_drag_func = main_text.split("func _begin_scroll_drag", 1)[1].split("func _update_scroll_drag", 1)[0] if "func _begin_scroll_drag" in main_text and "func _update_scroll_drag" in main_text else ""
    add("quick_shelf_tap_uses_tile_rect", "var rect: Rect2 = _quick_shelf_tile_rect(index)" in quick_tap_func, "Quick Shelf tap hitboxes use the shared tile rect helper.")
    add("quick_shelf_draw_uses_tile_rect", "var rect: Rect2 = _quick_shelf_tile_rect(index)" in quick_draw_func, "Quick Shelf drawing uses the shared tile rect helper.")
    add("quick_shelf_scrollbar_drag_only", "_quick_shelf_scrollbar_hit_rect" in main_text and 'nav.current_screen == "Quick Shelf" and _quick_shelf_scroll_rect().has_point(position) and _quick_shelf_max_scroll() > 0.0' not in scroll_drag_func, "Quick Shelf drag-scroll starts from the scrollbar strip, not tile bodies.")
    add("quick_shelf_status_text", "quick_shelf_status_text" in main_text and 'quick_shelf_status_text = tile_name + " planned"' in main_text, "Quick Shelf planned tiles show visible status text.")
    add("quick_shelf_settings_action", 'tile_name == "Settings"' in quick_action_func and "_open_settings()" in quick_action_func, "Quick Shelf Settings tile opens Settings.")
    add("quick_shelf_diagnostics_action", 'tile_name == "Diagnostics"' in quick_action_func and "_open_diagnostics()" in quick_action_func, "Quick Shelf Diagnostics tile opens Diagnostics.")
    add("quick_shelf_clock_action", 'tile_name == "Clock"' in quick_action_func and "_open_clock()" in quick_action_func, "Quick Shelf Clock tile opens Clock.")
    add("quick_shelf_network_action", '_open_diagnostics_tab("Network")' in quick_action_func, "Quick Shelf Network tile opens the Network Diagnostics tab.")
    add("quick_shelf_camera_action", '_open_diagnostics_tab("Camera")' in quick_action_func, "Quick Shelf Camera tile opens the Camera Diagnostics tab.")
    add("quick_shelf_logs_action", '_open_diagnostics_tab("Logs")' in quick_action_func, "Quick Shelf Logs tile opens the Logs Diagnostics tab.")
    add("quick_shelf_reports_action", '_open_diagnostics_tab("Reports")' in quick_action_func, "Quick Shelf Reports tile opens the Reports Diagnostics tab.")
    add("quick_shelf_exit_safe", 'tile_name == "Exit NeXa"' in quick_action_func and '_open_settings_page("exit_nexa")' in quick_action_func and "OS.execute" not in scripts_text and "poweroff" not in quick_action_func and "shutdown" not in quick_action_func and "reboot" not in quick_action_func, "Quick Shelf Exit NeXa opens planned Settings safety page without real power commands.")
    diagnostics_tab_func = main_text.split("func _open_diagnostics_tab", 1)[1].split("func _open_settings_page", 1)[0] if "func _open_diagnostics_tab" in main_text and "func _open_settings_page" in main_text else ""
    add("quick_shelf_diagnostics_tab_order", "_open_diagnostics()" in diagnostics_tab_func and "active_tab = tab_name" in diagnostics_tab_func and diagnostics_tab_func.find("_open_diagnostics()") < diagnostics_tab_func.find("active_tab = tab_name") and "_request_active_diagnostics_tab()" in diagnostics_tab_func, "Quick Shelf opens Diagnostics before selecting and requesting the chosen tab.")
    add("quick_shelf_touch_routing", "InputEventScreenTouch" in main_text and "InputEventScreenDrag" in main_text, "Touch taps and drags route through the same gesture path.")
    add("quick_shelf_study_actions", '"Study Stats"' in main_text and '_open_study("home")' in main_text and '_open_study("stats")' in main_text, "Quick Shelf Study and Study Stats actions are represented.")
    add("quick_shelf_reminders_action", 'tile_name == "Reminders"' in main_text and "_open_reminders()" in main_text, "Quick Shelf Reminders opens Reminders.")
    add("reminders_screen", 'nav.current_screen == "Reminders"' in main_text and "func _draw_reminders" in main_text and "_handle_reminders_tap" in main_text, "Reminders screen exists.")
    add("menu_reminders_action", 'tile["title"] == "Reminders"' in main_text and "_open_reminders()" in main_text, "Menu Reminders opens Reminders.")
    add("reminders_tables", "Upcoming" in main_text and "Past" in main_text and "reminders_upcoming_scroll_y" in main_text and "reminders_past_scroll_y" in main_text and "_draw_reminders_table" in main_text, "Reminders Upcoming and Past scrollable tables exist.")
    add("reminders_single_selection", "reminders_selected_id" in main_text and "reminders_selected_item" in main_text and "_select_reminder" in main_text and '"Select one reminder first."' in main_text, "Reminders single selected reminder state exists.")
    add("reminders_form", all(term in main_text for term in ["Add Reminder", '"Edit"', '"Delete"', "Reminder text", "Date", "Time", "+5m", "+15m", "+30m", "+1h", "Tomorrow", "Next week", '"Save"', '"Cancel"', "DELETE_REMINDER", "_draw_reminder_form_field"]), "Reminders Add/Edit/Delete form exists.")
    add("reminders_due_notifications", "reminders_poll_accumulator" in main_text and "/api/reminders/due" in main_text and "reminders_interval := 1.0 if reminders_due_modal_open else 5.0" in main_text and "reminders_due_data = payload" in main_text and "due_count > 0" in main_text and "reminders_pending_due_id" in main_text and "_request_redraw()" in main_text.split("func _handle_reminders_api", 1)[1] and "_draw_due_reminder_modal" in main_text and "_draw_reminder_top_badge" in main_text and "Dismiss" in main_text and "Snooze +5m" in main_text and '"Open"' in main_text, "Reminder due polling and notification actions exist.")
    add("reminders_datetime_keyboard", "text_input_keyboard_mode" in main_text and '{"keyboard_mode": "datetime"}' in main_text and "func _text_input_keys" in main_text and 'return "0123456789-"' in main_text and 'return "0123456789:"' in main_text and "_text_input_char_allowed" in main_text, "Reminder date/time uses numeric datetime keyboard and filters physical keyboard input.")
    add("reminders_private_pin", "Private reminder locked" in main_text and "requires_pin" in main_text and "should_hide_private_reminders" in reminders_store_text and "NEXA_SETTINGS_PATH" in reminders_store_text and "reminders_pending_private_after_pin" in main_text and "_open_privacy_pin_setup_from_reminders" in main_text and 'pin_enabled' in main_text and "Private reminder enabled." in main_text, "Private reminder lock placeholder and privacy PIN setup integration exist.")
    notification_dismiss_func = main_text.split("func _dismiss_notification", 1)[1].split("func _dismiss_pending_due_notification", 1)[0] if "func _dismiss_notification" in main_text and "func _dismiss_pending_due_notification" in main_text else ""
    add("control_center_notification_model", "notifications_data" in main_text and "notification_selected" in main_text and "notification_detail_modal_open" in main_text and "notification_dismissed_ids" in main_text and "_rebuild_notifications_from_reminders" in main_text, "Control Center notifications are data-driven from due reminders.")
    add("control_center_no_fake_notifications", '"Study plan"' not in main_text and '"UI running"' not in main_text, "Hardcoded fake Control Center notification rows are removed.")
    add("control_center_notification_rows", "_notification_row_rect" in main_text and "_notification_delete_rect" in main_text and "_draw_notification_row" in main_text and '"No notifications"' in main_text, "Notification rows, delete buttons, and empty state exist.")
    add("control_center_notification_modal", "_draw_notification_detail_modal" in main_text and "_handle_notification_tap" in main_text and "_open_notification_source" in main_text, "Notification tap opens a detail modal with source open action.")
    add("control_center_notification_swipe", "notification_swipe_start_x" in main_text and "notification_swipe_start_y" in main_text and "notification_swipe_active_id" in main_text and "_begin_notification_swipe" in main_text and "_finish_notification_swipe" in main_text and "absf(dx) > 60.0" in main_text, "Notification rows support left/right swipe dismissal.")
    add("control_center_notification_dismiss_safe", '/api/reminders/dismiss' in notification_dismiss_func and '/api/reminders/delete' not in notification_dismiss_func, "Notification dismissal calls reminder dismiss and does not delete reminder records.")
    add("control_center_notification_private_locked", '"Private reminder locked"' in main_text and '"Enter PIN to view"' in main_text and "requires_pin" in main_text, "Private reminder notifications use locked placeholders.")
    add("control_center_reminders_card", '"Reminders"' in main_text and "notifications_data" in main_text and "_draw_notifications_section_safe" in main_text, "Control Center Reminders notifications section exists.")
    add("study_screen", 'nav.current_screen == "Study"' in main_text and "func _draw_study" in main_text and "STUDY_TILES" in main_text, "Study screen exists.")
    study_tiles_const = main_text.split("const STUDY_TILES", 1)[1].split("var nav", 1)[0] if "const STUDY_TILES" in main_text and "var nav" in main_text else ""
    add("study_home_tiles", all(tile in study_tiles_const for tile in ["Smart Study", "Flashcards", "Quizzes", "Languages", "Study Stats", "History", "Settings"]) and '"Pomodoro"' not in study_tiles_const and '"Back"' not in study_tiles_const, "Study Home has Smart Study and no Pomodoro/Back tile.")
    add("study_pages", all(term in main_text for term in ["_draw_study_smart", "_draw_study_flashcards", "_draw_study_quizzes", "_draw_study_languages", "_draw_study_history", "_draw_study_settings", "_draw_study_stats"]), "Study pages are represented.")
    add("study_text_input", "text_input_open" in main_text and "_draw_text_input_overlay" in main_text and "_commit_text_input" in main_text and "event.unicode" in main_text and "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.,?!-/:" in main_text, "Reusable Study text input overlay supports physical and on-screen keyboard input.")
    overlay_func = main_text.split("func _draw_study_timer_overlay", 1)[1].split("func _settings_color", 1)[0] if "func _draw_study_timer_overlay" in main_text and "func _settings_color" in main_text else ""
    add("study_timer_overlay", "_draw_study_timer_overlay" in main_text and "remaining_seconds" in overlay_func and "planned_seconds" in overlay_func and "_draw_rounded_rect" not in overlay_func and "_draw_rounded_outline" not in overlay_func, "Face Home timer overlay is plain text only.")
    add("study_timer_color_thresholds", "percent <= 0.05" in main_text and "percent <= 0.30" in main_text and "percent <= 0.50" in main_text, "Timer overlay color threshold logic exists.")
    smart_draw = main_text.split("func _draw_study_smart", 1)[1].split("func _draw_study_flashcards", 1)[0] if "func _draw_study_smart" in main_text and "func _draw_study_flashcards" in main_text else ""
    add("study_smart_segments", "study_segments" in main_text and "+ Focus" in main_text and "+ Break" in main_text and "_validate_study_segments" in main_text and "/api/study/smart/start" in main_text, "Smart Study custom segment builder exists.")
    add("study_smart_segment_scroll", "_study_segment_scroll_rect" in main_text and "study_segment_scroll_y" in main_text and "_draw_scrollbar(view_rect, study_segment_scroll_y" in smart_draw, "Smart Study segment list scroll exists.")
    add("study_smart_focus_note_controls", "_study_current_segment_is_focus()" in smart_draw and "note_prompt_pending" in main_text and '"What did you learn?"' in main_text and '"Add note"' in smart_draw and '"Skip"' in smart_draw and '"Stop"' in smart_draw and '"Finish"' in smart_draw, "Smart Study focus-note prompt and active Stop/Finish exist.")
    add("study_smart_layout_final", "Rect2(44, 118, 350, 36)" in smart_draw and "Rect2(44, 164, 350, 36)" in smart_draw and "Focus total" in smart_draw and "Validation:" in smart_draw and '"After focus, add a break."' in main_text and '"After break, add focus."' in main_text, "Smart Study fields, summary, and alternating guards are represented.")
    add("study_flashcards_complete", all(term in main_text for term in ["New Flashcards", "Delete Flashcards", "Select one flashcard set first.", "Check Answer", "Reveal Answer", "I know this", "Not sure", "I don't know", "typed_answer", "revealed_answer", "Finish", "Continue", "study_flashcard_delete_confirm_open", 'study_flashcard_mode = "practice"', "_draw_study_feedback"]), "Flashcards single-selection editor/practice flow is represented.")
    add("study_flashcards_mastered_50", "correct >= 50" in study_store_text, "Flashcards mastered threshold requires 50 correct answers.")
    add("study_quiz_complete", all(term in main_text for term in ["New Quiz", "Add Question", "Start Quiz", "Delete Quiz", "Select one quiz first.", "Save question", "correct_answer", "study_pending_correct_answer", "Mark for review", "Repeat wrong", "Repeat marked", "study_quiz_delete_confirm_open", "answer_a", "answer_b", "answer_c", "answer_d", "correct_answer_text"]), "Quiz single-selection editor and solve flow is represented.")
    add("study_language_complete", all(term in main_text + live_api_text + study_store_text for term in ["New List", "Add Word", "Edit List", "Start Practice", "Delete List", "Select one language list first.", "Check Answer", "Reveal Answer", '"Correct"', '"Wrong"', "Delete Word", "study_language_mode", "study_language_answer_text", "correct_count >= 50", "/api/study/languages/practice/next", "/api/study/languages/list", "delete_language_word"]), "Language list edit and typed practice flow is represented.")
    settings_tap = main_text.split("func _handle_study_settings_tap", 1)[1].split("func _study_list_count", 1)[0] if "func _handle_study_settings_tap" in main_text and "func _study_list_count" in main_text else ""
    add("study_delete_two_step", "if study_delete_confirm_open:" in settings_tap and "study_delete_confirm_open = true" in settings_tap and 'confirm_text": "DELETE_STUDY_DATA"' in settings_tap and "Use Delete all first" in settings_tap, "Study delete all requires confirmation state before API call.")
    add("study_api_calls", all(endpoint in main_text for endpoint in ["/api/study/stats", "/api/study/smart/start", "/api/study/smart/status", "/api/study/flashcards/decks", "/api/study/quizzes", "/api/study/languages/lists", "/api/study/history"]), "Godot calls Study APIs.")
    add("diagnostics_study_stats", '"Study Stats"' in main_text and "/api/study/stats" in main_text and "_draw_diagnostics_study_stats" in main_text, "Diagnostics has Study Stats tab.")
    add("about_page", "Andrzej Dul" in main_text and "DevDul" in main_text and "Raspberry Pi 5 2GB" in main_text and "OpenGL ES Compatibility" in main_text, "About page includes project, author, hardware, software, and safety content.")
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
    gesture_func = main_text.split("func _handle_gesture", 1)[1].split("func _handle_tap", 1)[0] if "func _handle_gesture" in main_text and "func _handle_tap" in main_text else ""
    add("clock_any_swipe_close", 'nav.current_screen == "Clock" and action.begins_with("swipe_")' in gesture_func and "Clock is a passive glance screen" in gesture_func, "Clock closes to Face Home on any swipe.")
    add("reverse_swipe_close_control_center", 'nav.current_screen == "Notification Control Center" and action == "swipe_up"' in main_text, "Control Center reverse swipe closes to Face Home.")
    add("swipe_up_detected", '"swipe_up"' in gesture_text, "Gesture detector supports swipe up.")
    clock_draw_func = main_text.split("func _draw_clock", 1)[1].split("func _draw_control_center", 1)[0] if "func _draw_clock" in main_text and "func _draw_control_center" in main_text else ""
    add("clock_seconds", "now.second" in clock_draw_func and "second_text" in clock_draw_func, "Clock screen includes seconds.")
    add("clock_time_colors", all(key in clock_draw_func for key in ["hour_color", "minute_color", "second_color"]), "Clock draws hour, minute, and second colors from Appearance.")
    add("clock_date_colors", all(key in clock_draw_func for key in ["day_color", "month_color", "year_color"]), "Clock draws day, month, and year colors from Appearance.")
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
