import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
GODOT_DIR = REPO_ROOT / "system/ui/godot"


class GodotUiStructureTests(unittest.TestCase):
    def read(self, path):
        return Path(path).read_text(encoding="utf-8")

    def test_godot_project_files_exist(self):
        self.assertTrue(GODOT_DIR.exists())
        self.assertTrue((GODOT_DIR / "project.godot").exists())
        self.assertTrue((GODOT_DIR / "scenes/Main.tscn").exists())

    def test_required_scripts_exist(self):
        for script_name in [
            "main.gd",
            "theme.gd",
            "gesture_detector.gd",
            "navigation_controller.gd",
            "face_renderer.gd",
            "diagnostics_data.gd",
            "diagnostics_api_client.gd",
        ]:
            self.assertTrue((GODOT_DIR / "scripts" / script_name).exists(), script_name)

    def test_target_resolution_is_configured(self):
        project = self.read(GODOT_DIR / "project.godot")
        self.assertIn("viewport_width=640", project)
        self.assertIn("viewport_height=480", project)
        self.assertIn("resizable=false", project)
        self.assertIn("run/max_fps=30", project)
        self.assertIn('renderer/rendering_method="gl_compatibility"', project)
        self.assertIn('renderer/rendering_method.mobile="gl_compatibility"', project)

    def test_fullscreen_is_not_default_for_this_sprint(self):
        project = self.read(GODOT_DIR / "project.godot").lower()
        self.assertNotIn("fullscreen=true", project)

    def test_dev_launcher_is_windowed_fixed_size(self):
        launcher = self.read(REPO_ROOT / "scripts/run/run_godot_ui_dev.sh")
        self.assertIn("--windowed", launcher)
        self.assertIn("--resolution 640x480", launcher)
        self.assertIn("--rendering-driver", launcher)
        self.assertIn("opengl3", launcher)
        self.assertNotIn("--fullscreen", launcher)
        self.assertIn("nexa_godot_lcd_ui", launcher)

    def test_api_launcher_preserves_opengl_renderer(self):
        launcher = self.read(REPO_ROOT / "scripts/run/run_godot_ui_with_api_dev.sh")
        self.assertIn("NEXA_GODOT_RENDERING_DRIVER", launcher)
        self.assertIn("opengl3", launcher)
        self.assertIn("Compatibility/OpenGL", launcher)

    def test_lcd_launcher_exists_as_placeholder(self):
        launcher = self.read(REPO_ROOT / "scripts/run/run_godot_ui_lcd.sh")
        self.assertIn("planned for a later sprint", launcher)
        self.assertIn("run_godot_ui_dev.sh", launcher)

    def test_required_screen_names_are_represented(self):
        text = self._all_godot_text()
        for screen_name in [
            "Face Home",
            "Menu",
            "Clock",
            "Notification Control Center",
            "Diagnostics",
        ]:
            self.assertIn(screen_name, text)

    def test_diagnostics_tab_names_are_represented(self):
        text = self._all_godot_text()
        for tab_name in [
            "Overview",
            "System",
            "Processes",
            "Benchmarks",
            "Camera",
            "Audio",
            "Reports",
            "Logs",
            "Network",
        ]:
            self.assertIn(tab_name, text)

    def test_premium_rounded_style_helpers_are_represented(self):
        text = self._all_godot_text()
        for term in [
            "draw_card",
            "draw_pill",
            "draw_tile",
            "rounded",
        ]:
            self.assertIn(term, text)

    def test_runtime_helpers_are_local_and_callable(self):
        main = self.read(GODOT_DIR / "scripts/main.gd")
        for helper in [
            "func _draw_card",
            "func _draw_tile",
            "func _draw_pill",
            "func _draw_soft_panel",
        ]:
            self.assertIn(helper, main)
        for bad_call in [
            "ThemeScript.draw_card",
            "ThemeScript.draw_tile",
            "ThemeScript.draw_pill",
            "ThemeScript.draw_soft_panel",
        ]:
            self.assertNotIn(bad_call, main)

    def test_diagnostics_api_files_and_localhost_binding_are_represented(self):
        root = REPO_ROOT
        self.assertTrue((root / "scripts/run/run_diagnostics_api.py").exists())
        live_api = self.read(root / "system/services/diagnostics/live_api.py")
        self.assertIn("127.0.0.1", live_api)
        self.assertIn("8769", live_api)

    def test_godot_api_client_and_lazy_polling_are_represented(self):
        main = self.read(GODOT_DIR / "scripts/main.gd")
        client = self.read(GODOT_DIR / "scripts/diagnostics_api_client.gd")
        self.assertNotIn("OS.execute", main)
        self.assertIn("api_offline", client)
        self.assertIn("API offline", main)
        self.assertIn("_update_api_polling", main)
        self.assertIn("_request_active_diagnostics_tab", main)
        self.assertIn("/api/control-center", main)

    def test_live_api_endpoints_and_safe_actions_are_represented(self):
        live_api = self.read(REPO_ROOT / "system/services/diagnostics/live_api.py")
        for endpoint in [
            "/api/camera/preview/start",
            "/api/camera/preview/stop",
            "/api/benchmarks/run",
            "/api/reports/generate",
            "/api/control/remote-network",
        ]:
            self.assertIn(endpoint, live_api)
        self.assertIn("dry_run", live_api)
        self.assertTrue((REPO_ROOT / "system/services/diagnostics/camera_preview.py").exists())
        preview = self.read(REPO_ROOT / "system/services/diagnostics/camera_preview.py")
        self.assertIn("class CameraPreviewWorker", preview)
        self.assertIn('importlib.import_module("picamera2")', preview)
        self.assertIn("preview_thread", preview)
        self.assertIn("rpicam-vid", preview)
        self.assertIn("rpicam_vid_mjpeg", preview)
        self.assertIn("JPEG_SOI", preview)
        self.assertIn("JPEG_EOI", preview)
        self.assertIn("subprocess.Popen", preview)
        self.assertIn("_terminate_process", preview)
        self.assertIn("stale_timeout_seconds", preview)
        self.assertNotIn("rpicam-still", preview)

    def test_active_card_full_blue_style_is_represented(self):
        main = self.read(GODOT_DIR / "scripts/main.gd")
        self.assertIn("Color(0.11, 0.32, 0.66, 1.0)", main)

    def test_no_rect2_translated_usage_remains(self):
        text = "\n".join(
            self.read(path)
            for path in (GODOT_DIR / "scripts").glob("*.gd")
        )
        self.assertNotIn(".translated(", text)

    def test_menu_tile_layout_and_short_subtitles_are_represented(self):
        main = self.read(GODOT_DIR / "scripts/main.gd")
        self.assertIn("284.0", main)
        self.assertIn("72.0", main)
        self.assertIn("index % 2", main)
        for subtitle in [
            "Clock",
            "Focus",
            "Alerts",
            "Events",
            "To-do",
            "Play",
            "System",
            "Setup",
        ]:
            self.assertIn(f'"subtitle": "{subtitle}"', main)

    def test_menu_time_tile_opens_clock(self):
        main = self.read(GODOT_DIR / "scripts/main.gd")
        menu_tap = main.split("func _handle_menu_tap", 1)[1].split("func _handle_diagnostics_tap", 1)[0]
        self.assertIn('tile["title"] == "Time"', menu_tap)
        self.assertIn("_open_clock()", menu_tap)
        self.assertIn('tile["title"] == "Study"', menu_tap)
        self.assertIn('_open_study("home")', menu_tap)
        self.assertIn('tile["title"] == "Diagnostics"', menu_tap)
        self.assertIn("_open_diagnostics()", menu_tap)
        self.assertIn('tile["title"] == "Settings"', menu_tap)
        self.assertIn("_open_settings()", menu_tap)
        time_branch = menu_tap.split('tile["title"] == "Time"', 1)[1].split('elif tile["title"] == "Diagnostics"', 1)[0]
        self.assertNotIn("_open_placeholder", time_branch)

    def test_study_screen_and_pages_are_represented(self):
        main = self.read(GODOT_DIR / "scripts/main.gd")
        for term in [
            'nav.current_screen == "Study"',
            "STUDY_TILES",
            "func _draw_study",
            "_draw_study_smart",
            "_draw_study_flashcards",
            "_draw_study_quizzes",
            "_draw_study_languages",
            "_draw_study_history",
            "_draw_study_settings",
            "_draw_study_stats",
            "_draw_text_input_overlay",
            "_commit_text_input",
            "_draw_study_timer_overlay",
        ]:
            self.assertIn(term, main)
        study_tiles = main.split("const STUDY_TILES", 1)[1].split("var nav", 1)[0]
        for tile in ["Smart Study", "Flashcards", "Quizzes", "Languages", "Study Stats", "History", "Settings"]:
            self.assertIn(tile, main)
            self.assertIn(tile, study_tiles)
        self.assertNotIn('"Pomodoro"', study_tiles)
        self.assertNotIn('"Back"', study_tiles)
        for endpoint in [
            "/api/study/stats",
            "/api/study/smart/start",
            "/api/study/smart/status",
            "/api/study/flashcards/decks",
            "/api/study/quizzes",
            "/api/study/languages/lists",
            "/api/study/history",
        ]:
            self.assertIn(endpoint, main)
        self.assertIn('percent <= 0.05', main)
        self.assertIn('percent <= 0.30', main)
        self.assertIn('percent <= 0.50', main)
        self.assertIn('_open_study("stats")', main)
        self.assertIn("_draw_diagnostics_study_stats", main)
        overlay = main.split("func _draw_study_timer_overlay", 1)[1].split("func _settings_color", 1)[0]
        self.assertIn('": %02d:%02d"', overlay)
        self.assertNotIn("_draw_rounded_rect", overlay)
        self.assertNotIn("_draw_rounded_outline", overlay)
        self.assertIn("InputEventKey", main)
        for text in ["Reveal Answer", "I know this", "Not sure", "I don't know", "Finish", "Continue"]:
            self.assertIn(text, main)
        for text in ['"A"', '"B"', '"C"', '"D"', "Save question", "Mark for review", "Wrong"]:
            self.assertIn(text, main)
        self.assertIn("study_delete_confirm_open = true", main)
        confirm_branch = main.split("if study_delete_confirm_open:", 1)[1].split("func _study_list_count", 1)[0]
        self.assertIn('confirm_text": "DELETE_STUDY_DATA"', confirm_branch)
        self.assertIn("_study_segment_scroll_rect", main)
        self.assertIn("study_segment_scroll_y", main)
        smart_draw = main.split("func _draw_study_smart", 1)[1].split("func _draw_study_flashcards", 1)[0]
        self.assertIn("_draw_scrollbar(view_rect, study_segment_scroll_y", smart_draw)
        self.assertIn("_study_current_segment_is_focus()", smart_draw)
        self.assertIn("note_prompt_pending", main)
        self.assertIn("Rect2(44, 118, 350, 36)", smart_draw)
        self.assertIn("Focus total", smart_draw)
        self.assertIn('"Stop"', smart_draw)
        self.assertIn('"Finish"', smart_draw)
        self.assertIn('"Skip"', smart_draw)
        self.assertIn('"After focus, add a break."', main)
        self.assertIn('"After break, add focus."', main)
        flash_tap = main.split("func _handle_study_flashcards_tap", 1)[1].split("func _submit_flashcard_review", 1)[0]
        self.assertIn('"Select one flashcard set first."', flash_tap)
        self.assertIn("study_flashcard_delete_confirm_open", flash_tap)
        self.assertIn("study_flashcard_mode = \"practice\"", main)
        self.assertIn("Check Answer", main)
        self.assertIn("_draw_study_feedback", main)
        self.assertIn("_check_flashcard_answer", main)
        self.assertIn("study_flashcard_answer_checked", main)
        quiz_tap = main.split("func _handle_study_quizzes_tap", 1)[1].split("func _submit_quiz_answer", 1)[0]
        self.assertIn('"Select one quiz first."', quiz_tap)
        self.assertIn("study_quiz_delete_confirm_open", quiz_tap)
        for text in ["New Quiz", "Add Question", "Start Quiz", "Delete Quiz"]:
            self.assertIn(text, main)
        for text in ["answer_a", "answer_b", "answer_c", "answer_d", "correct_answer_text"]:
            self.assertIn(text, main)
        for text in ["New List", "Add Word", "Edit List", "Start Practice", "Delete List", "Select one language list first.", "Delete Word", "study_language_answer_text"]:
            self.assertIn(text, main)

    def test_reminders_screen_and_notifications_are_represented(self):
        main = self.read(GODOT_DIR / "scripts/main.gd")
        live_api = self.read(REPO_ROOT / "system/services/diagnostics/live_api.py")
        store = self.read(REPO_ROOT / "system/services/reminders/reminders_store.py")
        self.assertIn('nav.current_screen == "Reminders"', main)
        self.assertIn("func _draw_reminders", main)
        self.assertIn("func _handle_reminders_tap", main)
        self.assertIn('tile["title"] == "Reminders"', main)
        self.assertIn('tile_name == "Reminders"', main)
        self.assertIn("_open_reminders()", main)
        for text in ["Add Reminder", '"Edit"', '"Delete"', "Upcoming", "Past", "Reminder text", "Date", "Time", "+5m", "+15m", "+30m", "+1h", "Tomorrow", "Next week", '"Save"', '"Cancel"']:
            self.assertIn(text, main)
        self.assertIn("reminders_selected_id", main)
        self.assertIn("reminders_selected_item", main)
        self.assertIn("reminders_upcoming_scroll_y", main)
        self.assertIn("reminders_past_scroll_y", main)
        self.assertIn("DELETE_REMINDER", main)
        self.assertIn("/api/reminders/due", main)
        self.assertIn("reminders_interval := 1.0 if reminders_due_modal_open else 5.0", main)
        self.assertIn("reminders_due_data = payload", main)
        self.assertIn("due_count > 0", main)
        self.assertIn("reminders_pending_due_id", main)
        self.assertIn("_draw_due_reminder_modal", main)
        self.assertIn("_draw_global_overlays", main)
        global_draw = main.split("func _draw_global_overlays", 1)[1].split("func _draw_transition", 1)[0]
        self.assertIn("_draw_due_reminder_modal()", global_draw)
        tap_func = main.split("func _handle_tap", 1)[1].split("func _handle_menu_tap", 1)[0]
        self.assertIn("_handle_due_notification_modal_tap(position)", tap_func)
        self.assertLess(tap_func.find("_handle_due_notification_modal_tap(position)"), tap_func.find("text_input_open"))
        self.assertIn("func _handle_due_notification_modal_tap", main)
        self.assertIn("func _handle_due_reminder_modal_tap", main)
        self.assertIn("_draw_reminder_top_badge", main)
        for text in ["Private reminder locked", "Enter PIN to view", "Dismiss", "Snooze +5m", '"Open"']:
            self.assertIn(text, main)
        self.assertIn("_draw_reminder_form_field", main)
        self.assertIn("text_input_keyboard_mode", main)
        self.assertIn('{"keyboard_mode": "datetime"}', main)
        self.assertIn('return "0123456789-"', main)
        self.assertIn('return "0123456789:"', main)
        self.assertIn("_text_input_char_allowed", main)
        self.assertIn("reminders_pending_private_after_pin", main)
        self.assertIn("_open_privacy_pin_setup_from_reminders", main)
        self.assertIn("Private reminder enabled.", main)
        self.assertIn("notifications_data", main)
        self.assertIn("_rebuild_notifications_from_reminders", main)
        self.assertIn("_draw_notifications_section_safe", main)
        for endpoint in ["/api/reminders/overview", "/api/reminders/list", "/api/reminders/due", "/api/reminders/create", "/api/reminders/update", "/api/reminders/delete", "/api/reminders/dismiss", "/api/reminders/mark-triggered", "/api/reminders/settings/stats"]:
            self.assertIn(endpoint, live_api)
        self.assertIn("sqlite3", store)
        self.assertIn("var/data/reminders/nexa_reminders.db", store)
        self.assertIn("NEXA_REMINDERS_DB_PATH", store)
        self.assertIn("should_hide_private_reminders", store)

    def test_control_center_cards_are_represented(self):
        main = self.read(GODOT_DIR / "scripts/main.gd")
        self.assertIn("Control Center", main)
        self.assertIn("var controls: Array", main)
        self.assertIn("_draw_notification_row", main)
        self.assertIn("_notification_row_rect", main)
        self.assertIn("_notification_delete_rect", main)
        self.assertIn("_draw_notification_detail_modal", main)
        self.assertIn("_handle_notification_tap", main)
        self.assertIn("_begin_notification_swipe", main)
        self.assertIn("_finish_notification_swipe", main)
        self.assertIn("notification_dismissed_ids", main)
        self.assertIn('"No notifications"', main)
        self.assertNotIn("Reminders will appear here when due", main)
        self.assertNotIn('"Study plan"', main)
        self.assertNotIn('"UI running"', main)
        self.assertIn("notification_scroll_y", main)
        self.assertIn("func _notification_scroll_rect", main)
        self.assertIn("func _notification_max_scroll", main)
        self.assertIn("func _notification_row_rect", main)
        self.assertIn("- notification_scroll_y", main)
        self.assertIn('_apply_scroll("notifications"', main)
        self.assertIn("_draw_scrollbar(list_rect, notification_scroll_y", main)
        dismiss_func = main.split("func _dismiss_notification", 1)[1].split("func _dismiss_pending_due_notification", 1)[0]
        self.assertIn('/api/reminders/dismiss', dismiss_func)
        self.assertNotIn('/api/reminders/delete', dismiss_func)
        self.assertIn("_open_notification_source", main)
        self.assertIn("CONTROL_CENTER_SAFE_MODE := true", main)
        self.assertIn("_draw_control_center_safe", main)
        open_func = main.split("func _open_control_center", 1)[1].split("func _open_diagnostics", 1)[0]
        self.assertNotIn('api.request_get("/api/control-center")', open_func)
        self.assertNotIn('api.request_get("/api/network")', open_func)
        self.assertIn("control_center_refresh_pending", open_func)
        self.assertIn("network_detail_data", main)
        self.assertIn("_draw_wifi_detail_safe", main)
        self.assertIn('selected_control_detail = "wifi"', main)
        self.assertIn('api.request_get("/api/network")', main)
        self.assertIn("brightness_slider_rect", main)
        self.assertIn("sound_slider_rect", main)

    def test_calendar_screen_and_notifications_are_represented(self):
        main = self.read(GODOT_DIR / "scripts/main.gd")
        live_api = self.read(REPO_ROOT / "system/services/diagnostics/live_api.py")
        store = self.read(REPO_ROOT / "system/services/calendar/calendar_store.py")
        self.assertIn('nav.current_screen == "Calendar"', main)
        self.assertIn("func _draw_calendar", main)
        self.assertIn("func _handle_calendar_tap", main)
        self.assertIn('tile["title"] == "Calendar"', main)
        self.assertIn('tile_name == "Calendar"', main)
        self.assertIn("_open_calendar()", main)
        self.assertIn('"Previous"', main)
        self.assertIn('"Next"', main)
        self.assertIn("Rect2(330, 30, 84, 30)", main)
        self.assertIn("Rect2(422, 30, 74, 30)", main)
        self.assertIn("_calendar_change_month(-1)", main)
        self.assertIn("_calendar_change_month(1)", main)
        self.assertIn("month_name", main)
        self.assertIn('["M", "T", "W", "T", "F", "S", "S"]', main)
        self.assertIn("for index in range(42)", main)
        self.assertIn('var day_number := int(cell.get("day_number", 0))', main)
        self.assertIn('var day_text := str(day_number) if day_number > 0 else ""', main)
        self.assertNotIn('str(cell.get("day_number", ""))', main)
        self.assertIn("is_sunday", main)
        self.assertIn("is_today", main)
        self.assertIn("is_selected", main)
        self.assertIn("_draw_calendar_event_indicator", main)
        self.assertIn("events_count", main)
        self.assertIn("has_reminder", main)
        self.assertIn("_draw_calendar_day_details", main)
        for text in ['"Add"', '"Edit"', '"Delete"', '"Select one event first."']:
            self.assertIn(text, main)
        self.assertIn("_draw_calendar_form", main)
        self.assertIn("calendar_form_title", main)
        self.assertIn("calendar_form_description", main)
        self.assertIn("calendar_form_date", main)
        self.assertIn("calendar_form_time", main)
        self.assertIn('{"keyboard_mode": "datetime"}', main)
        for text in ["Off / At time", "5 min before", "15 min before", "1 hour before", "Snooze: Off / 5 min / 10 min / 30 min", "Repeat: None / Daily / Weekly / Monthly / Yearly"]:
            self.assertIn(text, main)
        self.assertIn('"Delete selected event?"', main)
        self.assertIn("DELETE_CALENDAR_EVENT", main)
        self.assertIn("calendar_poll_accumulator", main)
        self.assertIn("calendar_interval := 5.0 if calendar_due_modal_open else 30.0", main)
        self.assertIn('api.request_get("/api/calendar/due")', main)
        self.assertIn('"type": "calendar"', main)
        self.assertIn('"/api/calendar/dismiss"', main)
        self.assertIn('"/api/calendar/snooze"', main)
        self.assertIn("_dismiss_pending_calendar_notification", main)
        self.assertIn("calendar_due_modal_open", main)
        self.assertNotIn('"Dentist"', main)
        for endpoint in ["/api/calendar/month", "/api/calendar/day", "/api/calendar/events/create", "/api/calendar/events/update", "/api/calendar/events/delete", "/api/calendar/due", "/api/calendar/dismiss", "/api/calendar/snooze", "/api/calendar/settings/stats"]:
            self.assertIn(endpoint, live_api)
        self.assertIn("sqlite3", store)
        self.assertIn("var/data/calendar/nexa_calendar.db", store)
        self.assertIn("NEXA_CALENDAR_DB_PATH", store)

    def test_benchmark_and_camera_layout_are_runtime_safe(self):
        main = self.read(GODOT_DIR / "scripts/main.gd")
        self.assertIn('result_raw = active_tab_data.get("result", {})', main)
        self.assertIn("if result_raw is Dictionary", main)
        self.assertIn("if rows_raw is Array", main)
        self.assertNotIn('var result: Dictionary = active_tab_data.get("result", {})', main)
        self.assertNotIn('"Pilot"', main)
        self.assertIn("Remote Wi-Fi", main)
        self.assertIn("194.0 + float(int(index / 2)) * 50.0", main)
        self.assertIn("250.0, 42.0", main)
        self.assertIn("Rect2(44, 196 - offset_y, 270, 160)", main)
        self.assertIn("Rect2(350, 316 - offset_y, 190, 34)", main)
        self.assertIn("_draw_info_row_compact", main)
        self.assertIn("_stop_camera_preview", main)

    def test_settings_ui_is_represented(self):
        main = self.read(GODOT_DIR / "scripts/main.gd")
        self.assertIn("SETTINGS_TILES", main)
        self.assertIn('nav.current_screen = "Settings"', main)
        self.assertIn("settings_current_page", main)
        self.assertIn("_draw_settings_home", main)
        self.assertIn("_draw_settings_detail_page", main)
        self.assertIn('if nav.current_screen == "Settings":', main)
        self.assertIn("_handle_settings_tap(position)", main)
        self.assertIn("func _settings_tile_rect", main)
        self.assertIn("var rect: Rect2 = _settings_tile_rect(index)", main)
        self.assertIn("_settings_scrollbar_hit_rect", main)
        self.assertNotIn('nav.current_screen == "Settings" and _settings_scroll_rect().has_point(position) and _settings_max_scroll() > 0.0', main)
        self.assertIn("_handle_settings_detail_tap", main)
        self.assertIn("_handle_quick_shelf_tap", main)
        self.assertIn("_handle_pin_tap", main)
        self.assertIn("_settings_update", main)
        self.assertIn("settings_data[section] = section_data", main)
        for page in [
            "Appearance",
            "Notifications",
            "Modes",
            "Quick Shelf",
            "Display",
            "Sound",
            "Network",
            "Remote",
            "Privacy",
            "Diagnostics",
            "Safety",
            "Exit NeXa",
        ]:
            self.assertIn(page, main)
        self.assertIn("COLOR_OPTIONS", main)
        self.assertIn("MODE_OPTIONS", main)
        self.assertIn("QUICK_SHELF_OPTIONS", main)
        self.assertIn("/api/settings", main)
        self.assertIn("/api/settings/update", main)
        self.assertIn("/api/privacy/pin/set", main)
        self.assertIn("/api/privacy/pin/verify", main)
        self.assertIn("/api/privacy/lock", main)
        self.assertIn("_settings_color", main)
        self.assertIn("face.draw_face(self, Vector2(WIDTH, HEIGHT), elapsed", main)
        self.assertIn("settings_dropdown_open", main)
        self.assertIn("_draw_settings_dropdown", main)
        self.assertIn("_apply_appearance_preset", main)
        self.assertIn("/api/settings/update-many", main)
        self.assertIn("_theme_background_color", main)
        for row in [
            "Time color",
            "Hour color",
            "Minute color",
            "Second color",
            "Date color",
            "Day color",
            "Month color",
            "Year color",
        ]:
            self.assertIn(row, main)
        self.assertIn('key == "time_color"', main)
        self.assertIn('key == "date_color"', main)
        self.assertIn('"key": "hour_color"', main)
        self.assertIn('"key": "minute_color"', main)
        self.assertIn('"key": "second_color"', main)
        self.assertIn('"key": "day_color"', main)
        self.assertIn('"key": "month_color"', main)
        self.assertIn('"key": "year_color"', main)
        self.assertIn("_open_quick_shelf", main)
        self.assertIn('"Quick Shelf"', main)
        self.assertIn("_draw_quick_shelf", main)
        self.assertIn("_activate_quick_shelf_tile", main)
        self.assertIn("_handle_quick_shelf_panel_tap(position)", main)
        self.assertIn("_quick_shelf_scrollbar_hit_rect", main)
        self.assertIn("swipe_up", main)
        self.assertIn("swipe_down", main)
        self.assertIn("Andrzej Dul", main)
        self.assertIn("DevDul", main)
        self.assertIn("Raspberry Pi 5 2GB", main)
        self.assertIn("OpenGL ES Compatibility", main)
        self.assertNotIn("OS.execute", main)

    def test_quick_shelf_tile_taps_and_actions_are_represented(self):
        main = self.read(GODOT_DIR / "scripts/main.gd")
        tap_func = main.split("func _handle_quick_shelf_panel_tap", 1)[1].split("func _activate_quick_shelf_tile", 1)[0]
        action_func = main.split("func _activate_quick_shelf_tile", 1)[1].split("func _open_diagnostics_tab", 1)[0]
        draw_func = main.split("func _draw_quick_shelf", 1)[1].split("func _quick_shelf_tile_rect", 1)[0]
        scroll_drag_func = main.split("func _begin_scroll_drag", 1)[1].split("func _update_scroll_drag", 1)[0]
        diagnostics_tab_func = main.split("func _open_diagnostics_tab", 1)[1].split("func _open_settings_page", 1)[0]

        self.assertIn('if nav.current_screen == "Quick Shelf":', main)
        self.assertIn("_handle_quick_shelf_panel_tap(position)", main)
        self.assertIn("var rect: Rect2 = _quick_shelf_tile_rect(index)", tap_func)
        self.assertIn("var rect: Rect2 = _quick_shelf_tile_rect(index)", draw_func)
        self.assertIn("quick_shelf_scroll_y", main)
        self.assertIn("_quick_shelf_scrollbar_hit_rect", scroll_drag_func)
        self.assertNotIn(
            'nav.current_screen == "Quick Shelf" and _quick_shelf_scroll_rect().has_point(position) and _quick_shelf_max_scroll() > 0.0',
            scroll_drag_func,
        )
        self.assertIn("InputEventScreenTouch", main)
        self.assertIn("InputEventScreenDrag", main)

        self.assertIn('tile_name == "Settings"', action_func)
        self.assertIn("_open_settings()", action_func)
        self.assertIn('tile_name == "Diagnostics"', action_func)
        self.assertIn("_open_diagnostics()", action_func)
        self.assertIn('tile_name == "Clock"', action_func)
        self.assertIn("_open_clock()", action_func)
        self.assertIn('_open_diagnostics_tab("Network")', action_func)
        self.assertIn('_open_diagnostics_tab("Camera")', action_func)
        self.assertIn('_open_diagnostics_tab("Logs")', action_func)
        self.assertIn('_open_diagnostics_tab("Reports")', action_func)
        self.assertIn('quick_shelf_status_text = tile_name + " planned"', action_func)
        self.assertIn('tile_name == "Exit NeXa"', action_func)
        self.assertIn('_open_settings_page("exit_nexa")', action_func)
        self.assertNotIn("OS.execute", main)
        self.assertNotIn("poweroff", action_func)
        self.assertNotIn("shutdown", action_func)
        self.assertNotIn("reboot", action_func)

        self.assertLess(diagnostics_tab_func.find("_open_diagnostics()"), diagnostics_tab_func.find("active_tab = tab_name"))
        self.assertIn("_request_active_diagnostics_tab()", diagnostics_tab_func)

    def test_face_uses_vertical_eyes_without_strong_glow(self):
        face = self.read(GODOT_DIR / "scripts/face_renderer.gd")
        self.assertIn("_draw_vertical_capsule", face)
        self.assertIn("_draw_bean_eye", face)
        self.assertNotIn("width + 20.0", face)
        self.assertNotIn("height + 24.0", face)

    def test_face_idle_blink_logic_is_represented(self):
        face = self.read(GODOT_DIR / "scripts/face_renderer.gd")
        self.assertIn("BLINK_PERIOD", face)
        self.assertIn("BLINK_DURATION", face)
        self.assertIn("fmod", face)
        self.assertIn("_blink_amount", face)

    def test_scroll_support_is_represented(self):
        main = self.read(GODOT_DIR / "scripts/main.gd")
        for term in [
            "diagnostic_scroll_y",
            "control_center_scroll_y",
            "func _draw_scrollbar",
            "clampf(diagnostic_scroll_y",
            "clampf(control_center_scroll_y",
            "MOUSE_BUTTON_WHEEL_UP",
            "MOUSE_BUTTON_WHEEL_DOWN",
        ]:
            self.assertIn(term, main)

    def test_panel_font_sizes_are_reduced(self):
        main = self.read(GODOT_DIR / "scripts/main.gd")
        self.assertIn('_draw_text("Menu", Vector2(32, 52), 27', main)
        self.assertIn('Vector2(58, 30), 17', main)
        self.assertIn('Vector2(58, 52), 11', main)
        self.assertIn('_draw_text("Control Center", Vector2(44, 64), 26', main)
        self.assertIn('_draw_text("Diagnostics", Vector2(26, 40), 26', main)

    def test_menu_tile_cards_are_represented(self):
        main = self.read(GODOT_DIR / "scripts/main.gd")
        self.assertIn("MENU_TILES", main)
        self.assertIn("_draw_tile(rect", main)
        self.assertIn("Diagnostics", main)

    def test_face_home_label_is_not_drawn_on_home_screen(self):
        main = self.read(GODOT_DIR / "scripts/main.gd")
        self.assertNotIn('_draw_text("Face Home"', main)

    def test_transition_logic_is_represented(self):
        main = self.read(GODOT_DIR / "scripts/main.gd")
        for term in [
            "transition_progress",
            "transition_direction",
            "_draw_transition",
            "TRANSITION_SECONDS",
            "CLOSE_TRANSITION_SECONDS",
        ]:
            self.assertIn(term, main)
        self.assertIn("TRANSITION_SECONDS := 0.14", main)
        self.assertIn("CLOSE_TRANSITION_SECONDS := 0.10", main)
        self.assertIn("transition_overlay", main)
        self.assertIn("_draw_overlay_screen", main)

    def test_redraw_throttling_is_represented(self):
        main = self.read(GODOT_DIR / "scripts/main.gd")
        for term in [
            "TARGET_REDRAW_FPS",
            "REDRAW_INTERVAL",
            "redraw_accumulator",
            "redraw_requested",
            "_request_redraw",
        ]:
            self.assertIn(term, main)

    def test_navigation_close_behaviour_is_represented(self):
        main = self.read(GODOT_DIR / "scripts/main.gd")
        gesture = self.read(GODOT_DIR / "scripts/gesture_detector.gd")
        self.assertIn('nav.current_screen == "Menu" and action == "swipe_right"', main)
        self.assertIn('nav.current_screen == "Clock" and action.begins_with("swipe_")', main)
        self.assertIn("Clock is a passive glance screen, so any swipe returns to Face Home.", main)
        self.assertIn('nav.current_screen == "Notification Control Center" and action == "swipe_up"', main)
        self.assertIn('"swipe_up"', gesture)
        for action in ["swipe_left", "swipe_right", "swipe_up", "swipe_down"]:
            self.assertIn(action, gesture if action == "swipe_up" else main + gesture)

    def test_clock_shows_seconds_and_appearance_colors(self):
        main = self.read(GODOT_DIR / "scripts/main.gd")
        draw_clock = main.split("func _draw_clock", 1)[1].split("func _draw_control_center", 1)[0]
        self.assertIn("now.second", draw_clock)
        self.assertIn("second_text", draw_clock)
        for key in [
            "hour_color",
            "minute_color",
            "second_color",
            "day_color",
            "month_color",
            "year_color",
        ]:
            self.assertIn(key, draw_clock)
        self.assertIn("_draw_centered_segments", draw_clock)

    def test_premium_style_terms_are_represented(self):
        text = self._all_godot_text()
        for term in [
            "draw_card",
            "rounded",
            "transition",
            "Face Home",
            "Menu",
            "Clock",
            "Notification Control Center",
            "Diagnostics",
        ]:
            self.assertIn(term, text)

    def _all_godot_text(self):
        parts = []
        for path in GODOT_DIR.rglob("*"):
            if path.is_file() and path.suffix in {".gd", ".tscn", ".godot", ".md"}:
                parts.append(self.read(path))
        return "\n".join(parts)


if __name__ == "__main__":
    unittest.main()
