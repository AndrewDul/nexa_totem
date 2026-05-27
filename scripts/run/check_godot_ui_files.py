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
    calendar_store = REPO_ROOT / "system/services/calendar/calendar_store.py"
    todo_store = REPO_ROOT / "system/services/todo/todo_store.py"
    hardware_gateway_dir = REPO_ROOT / "system/services/hardware_gateway"
    hardware_state = hardware_gateway_dir / "hardware_state.py"
    hardware_readme = hardware_gateway_dir / "README.md"
    hardware_dev_runner = REPO_ROOT / "scripts/run/run_hardware_gateway_dev.py"
    hardware_api_check = REPO_ROOT / "scripts/test/check_hardware_gateway_api.py"
    api_client = scripts_dir / "diagnostics_api_client.gd"
    home_dir = scripts_dir / "home"
    home_messages_dir = home_dir / "messages"
    home_behaviors_dir = home_dir / "behaviors"
    system_scripts_dir = scripts_dir / "system"
    system_notifications_dir = system_scripts_dir / "notifications"
    assets_dir = project / "assets"
    icons_dir = assets_dir / "icons"
    design_tokens = system_scripts_dir / "design_tokens.gd"
    nexa_message = home_messages_dir / "nexa_message.gd"
    message_queue = home_messages_dir / "message_queue.gd"
    behavior_registry = home_behaviors_dir / "home_behavior_registry.gd"
    face_behavior_state = home_behaviors_dir / "face_behavior_state.gd"
    notification_policy = system_notifications_dir / "notification_policy.gd"
    input_router = system_scripts_dir / "input_router.gd"

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
    calendar_store_text = read_text(calendar_store)
    todo_store_text = read_text(todo_store)
    hardware_state_text = read_text(hardware_state)
    hardware_dev_runner_text = read_text(hardware_dev_runner)
    hardware_api_check_text = read_text(hardware_api_check)
    design_tokens_text = read_text(design_tokens)
    nexa_message_text = read_text(nexa_message)
    message_queue_text = read_text(message_queue)
    behavior_registry_text = read_text(behavior_registry)
    face_behavior_state_text = read_text(face_behavior_state)
    notification_policy_text = read_text(notification_policy)
    input_router_text = read_text(input_router)
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
    add("renderer_no_forward_mobile_vulkan", all(term not in project_text.lower() for term in ["forward_plus", 'rendering_method="mobile"', "vulkan"]), "Project does not enable Forward+, Mobile, or Vulkan rendering.")
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
    add("todo_store_exists", todo_store.exists(), "To Do store exists.")
    add("hardware_gateway_folder", hardware_gateway_dir.exists(), "Hardware gateway folder exists.")
    add("hardware_gateway_readme", hardware_readme.exists(), "Hardware gateway README exists.")
    add("hardware_state_store", "class HardwareStateStore" in hardware_state_text, "HardwareStateStore exists.")
    add("run_hardware_gateway_dev", hardware_dev_runner.exists(), "Hardware gateway dev runner exists.")
    add("check_hardware_gateway_api", hardware_api_check.exists(), "Hardware gateway API check exists.")
    add("api_localhost", "127.0.0.1" in live_api_text and "8769" in live_api_text, "API binds localhost port 8769.")
    add("home_system_folder_structure", all(path.exists() for path in [home_dir, home_messages_dir, home_behaviors_dir, system_scripts_dir, system_notifications_dir, assets_dir, icons_dir]), "Home/system/assets folder structure exists.")
    add("home_system_readmes", all((path / "README.md").exists() for path in [home_dir, home_messages_dir, home_behaviors_dir, system_scripts_dir, system_notifications_dir, assets_dir, icons_dir]), "New Home/system/assets folders have README files.")
    add("design_tokens_file", design_tokens.exists() and "SCREEN_WIDTH := 640" in design_tokens_text and "SCREEN_HEIGHT := 480" in design_tokens_text and "HOME_MESSAGE_TEXT_X := 342" in design_tokens_text and "HOME_MESSAGE_TEXT_W := 264" in design_tokens_text and "HOME_MESSAGE_FACE_IDLE_CENTER_X := 320" in design_tokens_text and "HOME_MESSAGE_FACE_MSG_CENTER_X := 160" in design_tokens_text and "HOME_FACE_OFFSCREEN_LEFT_X := -120" in design_tokens_text and "HOME_FACE_OFFSCREEN_RIGHT_X := 760" in design_tokens_text and "HOME_MESSAGE_AUTO_DISMISS_SECONDS := 4.0" in design_tokens_text and "STARTUP_SEQUENCE_SECONDS := 5.0" in design_tokens_text and "ANIM_FACE_TO_MESSAGE_SECONDS := 0.32" in design_tokens_text and "INACTIVITY_TIMEOUT_SECONDS := 30.0" in design_tokens_text, "Design tokens represent screen, face-left/text-right layout, offscreen positions, animations, startup, and inactivity timeout.")
    add("nexa_message_model", nexa_message.exists() and all(term in nexa_message_text for term in ["title", "body", "source", "message_type", "priority", "display_policy", "actions", "home_or_indicator", "urgent_interrupt"]), "NexaMessage model fields and display policies exist.")
    add("message_queue_model", message_queue.exists() and all(term in message_queue_text for term in ["push_message", "dismiss_active", "peek_next", "pop_next", "list_pending", "critical", "warning", "important", "reminder", "normal", "silent"]), "Message queue priority and list behavior exists.")
    add("home_behavior_registry", behavior_registry.exists() and all(term in behavior_registry_text for term in ["startup_greeting", "idle_calm", "notification_soft", "warning_soft", "private_locked", "happy", "calm", "focused", "concerned", "locked", "led_behavior", "sound_cue"]), "Home behavior registry includes initial expressions, LED placeholders, and sound placeholders.")
    add("face_behavior_state", face_behavior_state.exists() and "behavior_last_applied_id" in face_behavior_state_text and "current_led_behavior" in face_behavior_state_text and "current_sound_cue" in face_behavior_state_text, "Face behavior state placeholder exists without hardware control.")
    add("notification_policy_file", notification_policy.exists() and "home_or_indicator" in notification_policy_text and "urgent_interrupt" in notification_policy_text and "CRITICAL_INTERRUPT_RESERVED" in notification_policy_text, "Notification policy reserves urgent interrupts.")
    add("input_router_notes", input_router.exists() and all(action in input_router_text for action in ["nexa_up", "nexa_down", "nexa_left", "nexa_right", "nexa_accept", "nexa_back", "nexa_exit"]), "Input router shared action notes exist.")

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
    add("todo_api_endpoints", all(endpoint in live_api_text for endpoint in ["/api/todo/overview", "/api/todo/lists", "/api/todo/lists/create", "/api/todo/lists/update", "/api/todo/lists/delete", "/api/todo/tasks", "/api/todo/tasks/create", "/api/todo/tasks/update", "/api/todo/tasks/delete", "/api/todo/tasks/mark-done", "/api/todo/tasks/mark-active", "/api/todo/due", "/api/todo/dismiss", "/api/todo/snooze", "/api/todo/settings/stats"]), "To Do API endpoints exist.")
    add("hardware_api_endpoints", "/api/hardware/state" in live_api_text and "/api/hardware" in live_api_text and "/hardware-dashboard" in live_api_text, "Hardware API endpoints exist in localhost API.")
    add("study_sqlite_store", "sqlite3" in study_store_text and "var/data/study/nexa_study.db" in study_store_text and "NEXA_STUDY_DB_PATH" in study_store_text, "Study store uses local SQLite with test DB override.")
    add("reminders_sqlite_store", "sqlite3" in reminders_store_text and "var/data/reminders/nexa_reminders.db" in reminders_store_text and "NEXA_REMINDERS_DB_PATH" in reminders_store_text and "PRAGMA user_version = 1" in reminders_store_text, "Reminders store uses local SQLite with schema version and test DB override.")
    add("todo_sqlite_store", "sqlite3" in todo_store_text and "var/data/todo/nexa_todo.db" in todo_store_text and "NEXA_TODO_DB_PATH" in todo_store_text and "PRAGMA user_version = 1" in todo_store_text and "todo_lists" in todo_store_text and "todo_tasks" in todo_store_text, "To Do store uses local SQLite with schema version and test DB override.")
    add("study_duplicate_similar", "normalize_name" in study_store_text and "SequenceMatcher" in study_store_text and '"duplicate"' in study_store_text and '"similar"' in study_store_text, "Study store has duplicate and similar detection.")
    add("pin_hash_hidden", "pin_hash" in settings_store_text and "pin_salt" in settings_store_text and "safe_settings" in settings_store_text and "SENSITIVE_KEYS" in settings_store_text, "Settings API can remove PIN hash and salt.")
    add("pin_four_digits", "valid_pin" in settings_store_text and "len(pin) == 4" in settings_store_text and "pin.isdigit()" in settings_store_text, "PIN is constrained to four digits.")
    add("private_settings", "private_notifications_enabled" in settings_store_text and "private_reminders_enabled" in settings_store_text, "Private notification and reminder settings exist.")
    add("user_profile_settings", all(term in settings_store_text for term in ['"user"', '"first_name"', '"last_name"', '"preferred_name"', "_clean_user_profile_value", "value.strip()[:40]"]) and "user profile settings" in read_text(REPO_ROOT / "scripts/test/check_settings_api.py"), "Settings store/API supports local User profile fields.")
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
    add("environment_tile", '"title": "Environment"' in main_text and '"subtitle": "Air & room"' in main_text, "Environment menu tile exists.")
    add("environment_screen", 'nav.current_screen = "Environment"' in main_text and "func _draw_environment" in main_text, "Environment screen exists.")
    add("hardware_status_indicator", "Local network connected" in main_text and "Local network disconnected" in main_text and "func _draw_hardware_status_indicator" in main_text, "Local network status indicator exists.")
    add("hardware_polling_interval", "hardware_poll_interval_seconds := 1.0" in main_text and 'api.request_get("/api/hardware/state")' in main_text and "hardware_poll_elapsed += delta" in main_text, "Hardware polling runs around once per second.")
    add("presence_foundation", "last_seen_user_at" in main_text and "hardware_presence_active" in main_text and "presence_absence_seconds" in main_text and "presence_show_clock_after_seconds := 30.0" in main_text and "func _update_presence_face_clock" in main_text, "Presence Face/Clock foundation exists.")
    add("joystick_foundation", "hardware_last_joystick" in main_text and "joystick_repeat_delay_seconds := 0.35" in main_text and "joystick_select_cooldown_seconds := 0.5" in main_text and "func _handle_hardware_joystick" in main_text, "Joystick debounce foundation exists.")
    banned_network_terms = ["nmcli", "hostapd", "dnsmasq", "iptables", "nft ", "systemctl restart NetworkManager", "ifconfig", "iw ", "ip route"]
    new_script_text = hardware_dev_runner_text + "\n" + hardware_api_check_text
    add("hardware_scripts_no_network_config_commands", all(term not in new_script_text for term in banned_network_terms), "Hardware scripts do not contain network configuration commands.")
    add("no_hardcoded_wifi_password_in_code", "nexa12345" not in new_script_text and "nexa12345" not in main_text and "nexa12345" not in live_api_text, "No hardcoded Wi-Fi password appears in code.")
    add("menu_tile_width", "284.0" in main_text, "Menu tile width 284 is represented.")
    add("menu_tile_height", "72.0" in main_text, "Menu tile height 72 is represented.")
    add("menu_two_columns", "index % 2" in main_text and "300.0" in main_text, "Menu uses two columns.")
    menu_tap_func = main_text.split("func _handle_menu_tap", 1)[1].split("func _handle_diagnostics_tap", 1)[0] if "func _handle_menu_tap" in main_text and "func _handle_diagnostics_tap" in main_text else ""
    add("menu_time_opens_clock", 'tile["title"] == "Time"' in menu_tap_func and "_open_clock()" in menu_tap_func, "Menu Time tile opens Clock.")
    add("menu_study_opens_study", 'tile["title"] == "Study"' in menu_tap_func and '_open_study("home")' in menu_tap_func, "Menu Study tile opens Study.")
    for subtitle in ["Clock", "Focus", "Alerts", "Events", "Tasks", "Play", "System", "Setup"]:
        add(f"menu_subtitle_{subtitle}", f'"subtitle": "{subtitle}"' in main_text, f"Menu subtitle {subtitle} is represented.")
    add("control_center_cards", "Control Center" in main_text and "var controls: Array" in main_text and "_draw_notification" in main_text, "Control Center card drawing is represented.")
    add("control_center_safe_mode", "CONTROL_CENTER_SAFE_MODE := true" in main_text and "_draw_control_center_safe" in main_text, "Control Center safe drawing mode exists.")
    add("settings_ui", "SETTINGS_TILES" in main_text and 'nav.current_screen = "Settings"' in main_text and "_draw_settings_home" in main_text, "Settings UI home exists.")
    add("settings_pages", all(page in main_text for page in ["Appearance", "User", "Notifications", "Modes", "Quick Shelf", "Display", "Sound", "Network", "Remote", "Privacy", "Diagnostics", "Safety", "Exit NeXa"]), "Settings MVP pages are represented.")
    add("settings_user_page", all(term in main_text for term in ['"title": "User"', '"subtitle": "Profile"', '"First name"', '"Last name"', '"How should NeXa call you?"', '"Save"', '"section": "user"', '"key": "first_name"', '"key": "last_name"', '"key": "preferred_name"', 'target.begins_with("settings_user_")', '"User profile saved."']), "Settings User page stores first, last, and preferred call names.")
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
    add("quick_shelf_calendar_action", 'tile_name == "Calendar"' in main_text and "_open_calendar()" in main_text, "Quick Shelf Calendar opens Calendar.")
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
    add("calendar_service_files", calendar_store.exists() and "NEXA_CALENDAR_DB_PATH" in calendar_store_text and "var/data/calendar/nexa_calendar.db" in calendar_store_text, "Calendar local SQLite service exists.")
    add("calendar_api_endpoints", all(endpoint in live_api_text for endpoint in ["/api/calendar/month", "/api/calendar/day", "/api/calendar/events/create", "/api/calendar/events/update", "/api/calendar/events/delete", "/api/calendar/due", "/api/calendar/dismiss", "/api/calendar/snooze", "/api/calendar/settings/stats"]), "Calendar API endpoints exist.")
    add("calendar_screen", 'nav.current_screen == "Calendar"' in main_text and "func _draw_calendar" in main_text and "func _handle_calendar_tap" in main_text, "Calendar screen exists.")
    add("menu_calendar_action", 'tile["title"] == "Calendar"' in main_text and "_open_calendar()" in main_text, "Menu Calendar opens Calendar.")
    add("calendar_header_nav", '"Previous"' in main_text and '"Next"' in main_text and "_calendar_change_month(-1)" in main_text and "_calendar_change_month(1)" in main_text, "Calendar header has Previous and Next navigation.")
    add("calendar_header_nav_spacing", 'Rect2(330, 30, 84, 30)' in main_text and 'Rect2(422, 30, 74, 30)' in main_text and 'Rect2(520, 22, 92, 34)' in main_text and 'Rect2(466, 30, 78, 30)' not in main_text.split("func _draw_calendar", 1)[1].split("func _draw_calendar_weekdays", 1)[0], "Calendar Previous/Next buttons are left of Home without overlap.")
    add("calendar_month_api", "/api/calendar/month?year=" in main_text and "month_name" in main_text and "calendar_year" in main_text, "Calendar month name and year are drawn from API data.")
    add("calendar_weekday_row", '["M", "T", "W", "T", "F", "S", "S"]' in main_text and "_draw_calendar_weekdays" in main_text, "Calendar weekday row M T W T F S S exists.")
    add("calendar_42_cells", "for index in range(42)" in main_text and "func _calendar_cell_rect" in main_text, "Calendar grid draws 42 cells.")
    add("calendar_day_numbers_int", 'var day_number := int(cell.get("day_number", 0))' in main_text and 'var day_text := str(day_number) if day_number > 0 else ""' in main_text and 'str(cell.get("day_number", ""))' not in main_text, "Calendar day numbers are rendered as integer strings.")
    add("calendar_styles", "is_sunday" in main_text and "is_today" in main_text and "is_selected" in main_text and "Color(1.0, 0.45, 0.45" in main_text and "ThemeScript.BLUE" in main_text, "Calendar Sunday, today, and selected styles exist.")
    add("calendar_event_indicators", "func _draw_calendar_event_indicator" in main_text and "events_count" in main_text and '"3+"' in main_text and "has_reminder" in main_text, "Calendar event indicators exist.")
    add("calendar_day_details", "func _draw_calendar_day_details" in main_text and '"Add"' in main_text and '"Edit"' in main_text and '"Delete"' in main_text and '"Select one event first."' in main_text, "Calendar day details and event selection exist.")
    add("calendar_form", "func _draw_calendar_form" in main_text and "calendar_form_title" in main_text and "calendar_form_description" in main_text and "calendar_form_date" in main_text and "calendar_form_time" in main_text and '{"keyboard_mode": "datetime"}' in main_text, "Calendar Add/Edit event form exists with datetime keyboard.")
    add("calendar_options", all(term in main_text for term in ["Off / At time / 5 min before / 15 min before / 1 hour before", "Snooze: Off / 5 min / 10 min / 30 min", "Repeat: None / Daily / Weekly / Monthly / Yearly", "_calendar_cycle_reminder", "_calendar_cycle_snooze", "_calendar_cycle_repeat"]), "Calendar reminder, snooze, and repeat options exist.")
    add("calendar_delete_confirm", '"Delete selected event?"' in main_text and "DELETE_CALENDAR_EVENT" in main_text and '"/api/calendar/events/delete"' in main_text, "Calendar delete confirmation exists.")
    add("calendar_due_polling", "calendar_poll_accumulator" in main_text and "calendar_interval := 5.0 if calendar_due_modal_open else 30.0" in main_text and 'api.request_get("/api/calendar/due")' in main_text, "Calendar due polling exists and is not every frame.")
    add("calendar_notifications", '"type": "calendar"' in main_text and '"Calendar"' in main_text and '"/api/calendar/dismiss"' in main_text and '"/api/calendar/snooze"' in main_text and "calendar_due_modal_open" in main_text and "_dismiss_pending_calendar_notification" in main_text, "Calendar due notifications integrate with generic notifications.")
    add("calendar_no_fake_data", '"Study Java"' not in main_text and '"Dentist"' not in main_text and "No fake" not in main_text, "Calendar UI has no hardcoded fake event rows.")
    add("todo_screen", 'nav.current_screen == "To Do"' in main_text and "func _draw_todo" in main_text and "func _handle_todo_tap" in main_text, "To Do screen exists.")
    add("menu_todo_action", 'tile["title"] == "To Do"' in main_text and "_open_todo()" in main_text, "Menu To Do opens To Do.")
    add("quick_shelf_todo_action", 'tile_name == "To Do"' in main_text and "_open_todo()" in main_text and '"To Do"' in main_text.split("const QUICK_SHELF_OPTIONS", 1)[1].split("const STUDY_TILES", 1)[0], "Quick Shelf To Do opens To Do.")
    add("todo_main_new_list", '"To Do"' in main_text and '"New List"' in main_text and "func _draw_todo_lists" in main_text, "To Do main screen has title, New List, and list cards.")
    add("todo_new_list_aligned_home", 'Rect2(412, 26, 92, 30), "New List"' in main_text and 'if Rect2(412, 26, 92, 30).has_point(position):' in main_text and 'Rect2(520, 22, 92, 34)' in main_text and 'Rect2(412, 30, 92, 30), "New List"' not in main_text, "New List is aligned near Home and its tap hitbox matches the visible button.")
    add("todo_scroll", "todo_scroll_y" in main_text and "todo_task_scroll_y" in main_text and "_todo_lists_scroll_rect" in main_text and "_todo_tasks_scroll_rect" in main_text and "_draw_scrollbar(view, todo_scroll_y" in main_text, "To Do list and task scrolling exists.")
    add("todo_list_form", "func _draw_todo_list_form" in main_text and '"Emoji"' in main_text and '"List name"' in main_text and '"/api/todo/lists/create"' in main_text, "New List form exists with emoji and list name.")
    add("todo_task_list", "func _draw_todo_task_list" in main_text and '"Add Task"' in main_text and '"Active"' in main_text and '"Completed"' in main_text, "Task list screen has Add Task plus Active and Completed sections.")
    add("todo_detail_back_below_header", 'Rect2(30, 70, 74, 30), "Back"' in main_text and 'if Rect2(30, 70, 74, 30).has_point(position):' in main_text and 'Rect2(30, 30, 74, 30), "Back"' not in main_text, "To Do detail Back button sits below the title/header and its tap hitbox matches.")
    add("todo_detail_add_task_clear_home", 'Rect2(400, 26, 92, 30), "Add Task"' in main_text and 'if Rect2(400, 26, 92, 30).has_point(position):' in main_text and 'Rect2(496, 30, 92, 30), "Add Task"' not in main_text, "To Do detail Add Task button is left of Home and its tap hitbox matches.")
    todo_task_list_draw = main_text.split("func _draw_todo_task_list", 1)[1].split("func _draw_todo_task_row", 1)[0] if "func _draw_todo_task_list" in main_text and "func _draw_todo_task_row" in main_text else ""
    add("todo_detail_header_name_only", 'str(list_item.get("name", "Inbox"))' in todo_task_list_draw and 'str(list_item.get("emoji", "📥")) + " " + str(list_item.get("name", "Inbox"))' not in todo_task_list_draw, "To Do detail header renders only the list name, without emoji concatenation.")
    add("todo_task_content_below_back", "return Rect2(24, 108, 592, 344)" in main_text and 'Vector2(44, 128 - todo_task_scroll_y)' in main_text and "var y := 146.0" in main_text, "To Do task list content starts below the lowered Back button.")
    add("todo_task_detail", "func _draw_todo_task_detail" in main_text and '"Mark Done"' in main_text and '"Mark Active"' in main_text and '"Edit"' in main_text and '"Delete"' in main_text, "Task Details panel exists with task actions.")
    add("todo_task_delete_confirm", '"Delete this task?"' in main_text and "DELETE_TODO_TASK" in main_text and '"/api/todo/tasks/delete"' in main_text, "Task delete confirmation exists.")
    add("todo_task_form", "func _draw_todo_task_form" in main_text and "todo_form_title" in main_text and "todo_form_date" in main_text and "todo_form_time" in main_text and '{"keyboard_mode": "datetime"}' in main_text, "Task form exists with datetime keyboard fields.")
    add("todo_repeat_options", all(term in main_text for term in ["Repeat: None / Every X hours / Every X days / Weekly / Monthly / Yearly", "_todo_cycle_repeat", "Every X hours", "Every X days", "Weekly", "Monthly", "Yearly"]), "To Do repeat options exist.")
    add("todo_due_polling", "todo_poll_accumulator" in main_text and "todo_interval := 5.0 if todo_due_modal_open else 30.0" in main_text and 'api.request_get("/api/todo/due")' in main_text, "To Do due polling exists and is not every frame.")
    add("todo_notifications", '"type": "todo"' in main_text and '"To Do"' in main_text and '"/api/todo/dismiss"' in main_text and '"/api/todo/snooze"' in main_text and '"/api/todo/tasks/mark-done"' in main_text and "todo_due_modal_open" in main_text, "To Do due notifications integrate with generic notifications.")
    global_overlay_func = main_text.split("func _draw_global_overlays", 1)[1].split("func _draw_transition", 1)[0] if "func _draw_global_overlays" in main_text and "func _draw_transition" in main_text else ""
    tap_prefix = main_text.split("func _handle_tap", 1)[1].split("func _handle_menu_tap", 1)[0] if "func _handle_tap" in main_text and "func _handle_menu_tap" in main_text else ""
    add("todo_non_intrusive_policy", "todo_due_modal_open" not in global_overlay_func and 'nav.current_screen == "Face Home"' in tap_prefix and "_sync_notification_policy_after_rebuild" in main_text and '"To Do Reminder"' in main_text, "To Do reminders no longer draw a global blocking modal outside Home.")
    add("todo_notification_dismiss_safe", '"/api/todo/tasks/delete"' not in notification_dismiss_func and '"/api/todo/dismiss"' in notification_dismiss_func, "To Do notification removal does not delete tasks.")
    add("todo_no_fake_notifications", '"To Do reminders will appear here"' not in main_text and '"Fake To Do"' not in main_text, "No fake To Do notification rows exist.")
    games_source = ""
    if "func _games_card_rect" in main_text and "func _open_menu" in main_text:
        games_source += main_text.split("func _games_card_rect", 1)[1].split("func _open_menu", 1)[0]
    if "func _draw_games" in main_text and "func _draw_todo" in main_text:
        games_source += main_text.split("func _draw_games", 1)[1].split("func _draw_todo", 1)[0]
    add("menu_games_tile", '{"icon": "◆", "title": "Games", "subtitle": "Play"}' in main_text, "Menu Games tile exists.")
    add("menu_games_action", 'tile["title"] == "Games"' in main_text and "_open_games()" in main_text, "Menu Games opens Games.")
    add("games_screen", 'nav.current_screen = "Games"' in main_text and '"Games":' in main_text and "func _draw_games" in main_text and "func _handle_games_tap" in main_text, "Games screen exists in the Godot router.")
    add("games_library", "func _draw_games_library" in main_text and '"Tic-Tac-Toe"' in main_text and '"Coming Soon"' in main_text and '"Choose a game"' in main_text and '"Exit"' in main_text, "Games Library has Tic-Tac-Toe, Coming Soon cards, and Exit.")
    add("tic_tac_toe_menu", "func _draw_tic_tac_toe_menu" in main_text and '"Play with Someone"' in main_text and '"Play with NeXa"' in main_text and '"How to Play"' in main_text and '"Back"' in main_text and '"Exit"' in main_text, "Tic-Tac-Toe menu has play modes, help, Back, and Exit.")
    add("tic_tac_toe_game_screen", "func _draw_tic_tac_toe_game" in main_text and "func _ttt_cell_rect" in main_text and "for index in range(9)" in main_text and "tic_tac_toe_selected_cell" in main_text, "Tic-Tac-Toe game screen has a 3x3 board and selected cell.")
    add("tic_tac_toe_navigation", all(term in main_text for term in ['direction == "left"', 'tic_tac_toe_selected_cell not in [0, 3, 6]', 'direction == "right"', 'tic_tac_toe_selected_cell not in [2, 5, 8]', 'direction == "up"', 'tic_tac_toe_selected_cell not in [0, 1, 2]', 'direction == "down"', 'tic_tac_toe_selected_cell not in [6, 7, 8]', "_ttt_play_selected_cell()"]), "Tic-Tac-Toe board navigation and accept placement exist.")
    add("tic_tac_toe_logic", all(term in main_text for term in ["TTT_WIN_LINES", "func _ttt_get_winner", "func _ttt_is_draw", "func _ttt_available_moves", "func _ttt_choose_nexa_move", "func _ttt_find_winning_move", "func _ttt_winner_for_board"]), "Tic-Tac-Toe local win/draw/move logic exists.")
    add("tic_tac_toe_nexa_order", all(term in main_text for term in ["var winning_move := _ttt_find_winning_move(TTT_PLAYER_O)", "var blocking_move := _ttt_find_winning_move(TTT_PLAYER_X)", "tic_tac_toe_board[4]", "for corner in [0, 2, 6, 8]", "return int(moves[0])"]), "NeXa move order is win, block, center, corner, free.")
    add("tic_tac_toe_result_modal", "func _draw_tic_tac_toe_result_modal" in main_text and '"Play Again"' in main_text and "_ttt_activate_result_button" in main_text, "Tic-Tac-Toe result modal has Play Again, Back, and Exit.")
    add("games_exit_confirm", "func _draw_tic_tac_toe_exit_confirm" in main_text and '"Exit game?"' in main_text and '"Your current game will be lost."' in main_text and "_games_exit_pressed" in main_text, "Active game exit confirmation exists.")
    add("games_input_actions", all(action in project_text for action in ["nexa_up", "nexa_down", "nexa_left", "nexa_right", "nexa_accept", "nexa_back", "nexa_exit"]) and "_handle_games_action_event" in main_text, "Shared NeXa input actions exist for keyboard and future remote/joystick.")
    add("games_hitboxes_match_draw", all(term in main_text for term in ["_games_card_rect(index)", "_ttt_menu_button_rect(index)", "_ttt_cell_rect(index)", "_ttt_back_rect()", "_ttt_exit_rect()", "_ttt_new_game_rect()", "_ttt_result_button_rect(index)"]), "Games visible rects and tap hitboxes use shared rect helpers.")
    add("games_no_network_ai", all(term not in games_source.lower() for term in ["api.request", "http", "llm", "model", "openai"]) and "NeXa is thinking" in games_source, "Tic-Tac-Toe uses no HTTP/API/LLM/model calls.")
    add("games_non_intrusive_notifications", "_draw_global_overlays()" in main_text and "_draw_top_bar_indicators()" in main_text and 'if nav.current_screen == "Games":' in main_text and "_handle_top_indicator_tap" in main_text, "Games are not covered by normal notification popups; indicators are used when supported.")
    home_message_draw = main_text.split("func _draw_home_message_mode", 1)[1].split("func _draw_top_bar_indicators", 1)[0] if "func _draw_home_message_mode" in main_text and "func _draw_top_bar_indicators" in main_text else ""
    add("home_message_state", all(term in main_text for term in ["home_message_active", "home_message_title", "home_message_body", "home_message_scroll_y", "nexa_message_indicator_count", "nexa_messages_data"]), "Home Message Mode runtime state exists.")
    add("startup_sequence", all(term in main_text for term in ["STARTUP_SEQUENCE_SECONDS := 5.0", "startup_sequence_active", "startup_sequence_elapsed", "startup_check_status", "func _draw_startup_sequence", "func _update_startup_sequence", "func _finish_startup_sequence", "func _draw_startup_brand", "func _draw_startup_face", '"NeXa"', '"ToTem"', '"DevDul"', "_startup_alpha(0.45, 1.00)", "_startup_alpha(1.15, 0.95)", "_startup_alpha(1.75, 0.95)", "_startup_ease(2.45, 1.75)", "lerpf(590.0, 285.0", "startup_check_done"]) and "api.request" not in main_text.split("func _update_startup_sequence", 1)[1].split("func _finish_startup_sequence", 1)[0], "Startup animation state machine uses slower 5 second nonblocking timing.")
    add("startup_greeting_profile", all(term in main_text for term in ["func _get_user_first_name", "func _get_user_preferred_name", "func _get_startup_greeting_title", 'return "Hello"', '"NeXa is ready."', "_get_startup_greeting_title()"]) and '"Hello, Andrzej."' not in main_text, "Startup greeting resolves preferred name, first name, then plain Hello.")
    add("home_message_timer", all(term in main_text for term in ["HOME_MESSAGE_AUTO_DISMISS_SECONDS := 4.0", "home_message_visible_elapsed", "home_message_auto_dismiss_seconds", "home_message_auto_dismiss_enabled", "func _update_home_message_visible_timer", 'nav.current_screen != "Face Home"', "_close_home_message_preview(true)", "home_message_started_visible = nav.current_screen == \"Face Home\""]), "Home messages auto-dismiss after 4 visible seconds on Home only.")
    add("home_message_enter_animation", all(term in main_text for term in ["home_message_enter_active", "home_message_enter_elapsed", "home_message_enter_seconds", "func _update_home_message_enter", "func _home_message_enter_y_offset", "func _home_message_enter_alpha", "lerpf(-180.0, 0.0", "color.a *= text_alpha"]), "Home greeting/message text slides down 180px and fades in/out via unified text_alpha.")
    add("home_message_close", all(term in main_text for term in ["func _home_message_close_rect", "func _draw_circular_close_button", "func _handle_home_message_close_tap", "_home_message_close_rect().has_point(position)", "_close_home_message_preview(true)"]) and "delete" not in main_text.split("func _handle_home_message_close_tap", 1)[1].split("func _activate_home_message_action", 1)[0].lower(), "Circular Home message close button exists and does not delete source records.")
    add("home_message_layout", "HOME_MESSAGE_TEXT_X := 342.0" in main_text and "HOME_MESSAGE_TEXT_W := 264.0" in main_text and "HOME_MESSAGE_FACE_CENTER := Vector2(160.0, 245.0)" in main_text and "HOME_MESSAGE_FACE_IDLE_CENTER := Vector2(320.0, 245.0)" in main_text and "face.draw_face_at" in main_text and "HOME_MESSAGE_TEXT_X := 34.0" not in main_text and "HOME_MESSAGE_FACE_CENTER := Vector2(480.0, 245.0)" not in main_text and "Rect2(584, 58, 26, 26)" in main_text and "342.0 + float(index) * 86.0" in main_text, "Home Message Mode uses face-LEFT (x=0..320, center=160) / text-RIGHT (x=342..606) layout with correct close and action rects.")
    add("home_message_swipe_delete", all(term in main_text for term in ["messages_swipe_active_id", "messages_swipe_start_x", "messages_swipe_start_y", "messages_swipe_row_index", "func _begin_message_row_swipe", "func _finish_message_row_swipe", "func _dismiss_nexa_message_by_id"]) and "absf(dx) > 60.0" in main_text, "Message rows support swipe-to-dismiss with 60px threshold and abs(dx)>abs(dy) guard.")
    add("home_message_exit_animation", all(term in main_text for term in ["home_message_exit_active", "home_message_exit_elapsed", "home_message_exit_seconds", "func _start_home_message_enter", "func _start_home_message_exit", "func _update_home_message_exit_anim", "func _finish_home_message_exit"]), "Home message enter and exit animation state machine exists.")
    add("home_message_animation_helpers", all(term in main_text for term in ["func _home_message_text_y_offset", "func _home_message_text_alpha", "func _home_message_face_center", "func _home_message_face_scale", "HOME_MESSAGE_FACE_IDLE_CENTER.lerp(HOME_MESSAGE_FACE_CENTER", "lerpf(HOME_MESSAGE_FACE_IDLE_SCALE, HOME_MESSAGE_FACE_SCALE"]), "Home message animation helpers exist for text offset, alpha, and face position/scale lerps.")
    add("home_face_transition", all(term in main_text for term in ["func _home_face_transition_center", "func _draw_face_home_during_transition", "HOME_FACE_OFFSCREEN_LEFT_X", "HOME_FACE_OFFSCREEN_RIGHT_X", "HOME_FACE_OFFSCREEN_DOWN_Y", "HOME_FACE_OFFSCREEN_UP_Y", '"menu_open"', '"clock_open"', '"control_open"', '"quick_open"']), "Face animates offscreen during screen transitions with per-direction mapping.")
    add("home_message_no_container", "_draw_card" not in home_message_draw and "Color(0.045" not in home_message_draw and "bubble" not in home_message_draw.lower(), "Home message text is not drawn inside a card, border, or bubble container.")
    add("home_message_wrapping_scroll", "_wrap_text_to_width" in main_text and "lines.size() <= 5" in main_text and "_home_message_max_scroll" in main_text and '_apply_scroll("home_message"' in main_text and "_handle_home_message_action_event" in main_text, "Home messages wrap, vertically balance short text, and scroll long text.")
    add("home_clock", all(term in main_text for term in ["func _draw_home_clock", "func _home_clock_rect", '"%02d:%02d"', "_draw_text(label", "14, Color(0.58", "Rect2(482, 22, 56, 24)", "Rect2(546, 22, 30, 28)", "Rect2(584, 22, 30, 28)"]), "Subtle Home HH:MM clock exists and avoids indicator rects.")
    add("message_center", 'nav.current_screen = "Messages"' in main_text and "func _draw_messages_center" in main_text and '"No messages"' in main_text and "_message_row_rect" in main_text and "_open_messages_center" in main_text, "NeXa Messages center exists.")
    add("top_indicators", all(term in main_text for term in ["_message_indicator_rect", "_notification_indicator_rect", "_draw_message_indicator", "_draw_notification_indicator", "_handle_top_indicator_tap", "_open_control_center_notifications"]) and "🔔" not in main_text and "💬" not in main_text, "Custom-drawn message and notification indicators exist without emoji dependency.")
    add("notification_policy_non_intrusive", "_sync_notification_policy_after_rebuild" in main_text and "_show_next_home_item_if_available" in main_text and "_next_home_notification_preview" in main_text and "reminders_due_modal_open = nav.current_screen == \"Face Home\"" in main_text and "calendar_due_modal_open = nav.current_screen == \"Face Home\"" in main_text and "todo_due_modal_open = nav.current_screen == \"Face Home\"" in main_text and "notifications_data = next_notifications" in main_text, "Normal reminder/calendar/todo notifications store in Notification Center and can preview on Home without interrupting non-Home screens.")
    add("inactivity_controller", "inactivity_elapsed" in main_text and "INACTIVITY_TIMEOUT_SECONDS := 30.0" in main_text and 'INACTIVITY_EXEMPT_SCREENS := ["Games"]' in main_text and "func _update_inactivity" in main_text and "func _reset_user_activity" in main_text and "text_input_open" in main_text.split("func _update_inactivity", 1)[1].split("func _reset_user_activity", 1)[0], "Inactivity return exists with 30 second timeout, Games exemption, and text input guard.")
    add("home_behaviors_runtime", all(term in main_text for term in ["startup_greeting", "soft_idle_blink", "face_blink_active", "face_next_blink_seconds", "_apply_home_behavior", "current_led_behavior", "current_sound_cue"]) and "print(" not in main_text.split("func _update_face_behavior", 1)[1].split("func _update_inactivity", 1)[0], "Startup greeting and soft idle blink behavior runtime exists without per-frame print spam.")
    add("study_break_game_suggestion", all(term in main_text for term in ["study_break_game_suggested_for_segment_id", "break_elapsed >= 30", '"Want to play a quick game during your break?"', '"open_games"', '"not_now"', "study_break_game_active", "kind == \"focus\"", '_open_study("smart_study")']), "Smart Study break game suggestion, one-shot dismissal, Yes action, and break-end return are represented.")
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
