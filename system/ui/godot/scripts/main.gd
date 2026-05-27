extends Control

const NavigationControllerScript := preload("res://scripts/navigation_controller.gd")
const GestureDetectorScript := preload("res://scripts/gesture_detector.gd")
const FaceRendererScript := preload("res://scripts/face_renderer.gd")
const DiagnosticsDataScript := preload("res://scripts/diagnostics_data.gd")
const ThemeScript := preload("res://scripts/theme.gd")
const DiagnosticsApiClientScript := preload("res://scripts/diagnostics_api_client.gd")

const WIDTH := 640.0
const HEIGHT := 480.0
const TARGET_REDRAW_FPS := 30.0
const REDRAW_INTERVAL := 1.0 / TARGET_REDRAW_FPS
const CLOCK_REDRAW_INTERVAL := 1.0
const TRANSITION_SECONDS := 0.14
const CLOSE_TRANSITION_SECONDS := 0.10
const CONTROL_CENTER_SAFE_MODE := true
const TTT_EMPTY := ""
const TTT_PLAYER_X := "X"
const TTT_PLAYER_O := "O"
const TTT_WIN_LINES := [
	[0, 1, 2],
	[3, 4, 5],
	[6, 7, 8],
	[0, 3, 6],
	[1, 4, 7],
	[2, 5, 8],
	[0, 4, 8],
	[2, 4, 6]
]
# Home Message Mode: face LEFT side (x=0..320), text RIGHT side (x=320..640)
const HOME_MESSAGE_FACE_IDLE_CENTER := Vector2(320.0, 245.0)
const HOME_MESSAGE_FACE_IDLE_SCALE := 0.86
const HOME_MESSAGE_FACE_CENTER := Vector2(160.0, 245.0)
const HOME_MESSAGE_FACE_SCALE := 0.52
const HOME_MESSAGE_TEXT_X := 342.0
const HOME_MESSAGE_TEXT_W := 264.0
const HOME_MESSAGE_TEXT_TOP_PADDING := 76.0
const HOME_MESSAGE_TEXT_BOTTOM_PADDING := 54.0
const HOME_MESSAGE_ANIM_ENTER_SECONDS := 0.40
const HOME_MESSAGE_ANIM_EXIT_SECONDS := 0.33
# Transition face offscreen exit positions
const HOME_FACE_OFFSCREEN_LEFT_X := -120.0
const HOME_FACE_OFFSCREEN_RIGHT_X := 760.0
const HOME_FACE_OFFSCREEN_DOWN_Y := 620.0
const HOME_FACE_OFFSCREEN_UP_Y := -140.0
const FONT_SIZE_MESSAGE_TITLE := 22
const FONT_SIZE_MESSAGE_BODY := 16
const FONT_SIZE_MESSAGE_META := 12
const ANIM_FACE_TO_MESSAGE_SECONDS := 0.32
const ANIM_MESSAGE_FADE_SECONDS := 0.22
const INACTIVITY_TIMEOUT_SECONDS := 30.0
const HOME_MESSAGE_AUTO_DISMISS_SECONDS := 4.0
const STARTUP_SEQUENCE_SECONDS := 5.0
const HOME_BEHAVIOR_SOFT_IDLE_BLINK := "soft_idle_blink"
const MESSAGE_PRIORITY_ORDER := {"critical": 5, "warning": 4, "important": 3, "reminder": 2, "normal": 1, "silent": 0}
const INACTIVITY_EXEMPT_SCREENS := ["Games"]
const MENU_TILES := [
	{"icon": "◷", "title": "Time", "subtitle": "Clock"},
	{"icon": "◌", "title": "Study", "subtitle": "Focus"},
	{"icon": "⌁", "title": "Environment", "subtitle": "Air & room"},
	{"icon": "!", "title": "Reminders", "subtitle": "Alerts"},
	{"icon": "□", "title": "Calendar", "subtitle": "Events"},
	{"icon": "✓", "title": "To Do", "subtitle": "Tasks"},
	{"icon": "◆", "title": "Games", "subtitle": "Play"},
	{"icon": "⌁", "title": "Diagnostics", "subtitle": "System"},
	{"icon": "⚙", "title": "Settings", "subtitle": "Setup"}
]
const DIAGNOSTIC_TABS := [
	"Overview",
	"System",
	"Processes",
	"Benchmarks",
	"Camera",
	"Audio",
	"Reports",
	"Logs",
	"Network",
	"Study Stats"
]
const SETTINGS_TILES := [
	{"icon": "◐", "title": "Appearance", "subtitle": "Theme"},
	{"icon": "i", "title": "User", "subtitle": "Profile"},
	{"icon": "!", "title": "Notifications", "subtitle": "Alerts"},
	{"icon": "◆", "title": "Modes", "subtitle": "Behaviour"},
	{"icon": "▤", "title": "Quick Shelf", "subtitle": "Bottom"},
	{"icon": "☼", "title": "Display", "subtitle": "Screen"},
	{"icon": "♪", "title": "Sound", "subtitle": "Audio"},
	{"icon": "⌁", "title": "Network", "subtitle": "Wi-Fi"},
	{"icon": "◇", "title": "Remote", "subtitle": "Control"},
	{"icon": "●", "title": "Privacy", "subtitle": "PIN"},
	{"icon": "▦", "title": "Diagnostics", "subtitle": "Logs"},
	{"icon": "□", "title": "Safety", "subtitle": "Exit"},
	{"icon": "i", "title": "About", "subtitle": "NeXa"},
	{"icon": "×", "title": "Exit NeXa", "subtitle": "Planned"}
]
const COLOR_OPTIONS := ["Blue", "Sky Blue", "Cyan", "White", "Warm White", "Yellow", "Orange", "Red", "Pink", "Purple", "Green", "Mint", "Brown", "Gold", "Grey", "Graphite", "Black"]
const PRESET_OPTIONS := ["NeXa Blue", "Apple Dark", "Warm Desk", "Focus Green", "Night Red", "Soft Pink", "Minimal White"]
const MODE_OPTIONS := ["Normal", "Quiet", "Focus", "Night", "Away", "Demo", "Maintenance"]
const QUICK_SHELF_OPTIONS := ["Clock", "Calendar", "Reminders", "To Do", "Tasks", "Study", "Study Stats", "Games", "Diagnostics", "Network", "Camera", "Air Quality", "Temperature", "Brightness", "Sound", "Quiet Mode", "Remote", "Settings", "LED", "Logs", "Reports", "Exit NeXa"]
const STUDY_TILES := [
	{"title": "Smart Study", "subtitle": "Segments"},
	{"title": "Flashcards", "subtitle": "Sets"},
	{"title": "Quizzes", "subtitle": "Questions"},
	{"title": "Languages", "subtitle": "Words"},
	{"title": "Study Stats", "subtitle": "Progress"},
	{"title": "History", "subtitle": "Events"},
	{"title": "Settings", "subtitle": "Database"}
]

var nav := NavigationControllerScript.new()
var gesture := GestureDetectorScript.new()
var face := FaceRendererScript.new()
var diagnostics_data := DiagnosticsDataScript.new()
var api := DiagnosticsApiClientScript.new()
var elapsed := 0.0
var active_tab := "Overview"
var panel_data := {}
var api_online := false
var api_status_text := "API offline"
var control_center_data := {}
var network_detail_data := {}
var network_detail_pending := false
var overview_live_data := {}
var active_tab_data := {}
var api_poll_accumulator := 0.0
var hardware_state_data := {}
var hardware_connected := false
var hardware_stale := true
var hardware_last_seen_at := ""
var hardware_poll_elapsed := 0.0
var hardware_poll_interval_seconds := 1.0
var last_seen_user_at := 0.0
var hardware_presence_active := false
var presence_absence_seconds := 0.0
var presence_show_clock_after_seconds := 30.0
var clock_shown_for_absence := false
var hardware_last_joystick := "CENTER"
var hardware_last_joystick_action_at := 0.0
var joystick_repeat_delay_seconds := 0.35
var joystick_select_cooldown_seconds := 0.5
var hardware_menu_focus_index := 0
var control_center_refresh_pending := false
var brightness_percent := 65
var sound_percent := 50
var quiet_mode_local := false
var remote_network_local := "planned"
var slider_drag_active := false
var slider_drag_kind := ""
var camera_preview_on := false
var camera_preview_status := "Off"
var camera_frame_texture: ImageTexture = null
var camera_frame_poll_accumulator := 0.0
var selected_control_detail := ""
var transition_active := false
var transition_overlay := ""
var transition_direction := "none"
var transition_progress := 1.0
var transition_duration := TRANSITION_SECONDS
var transition_closing := false
var redraw_accumulator := 0.0
var clock_redraw_accumulator := 0.0
var redraw_requested := true
var diagnostic_scroll_y := 0.0
var control_center_scroll_y := 0.0
var scroll_drag_active := false
var scroll_drag_area := ""
var scroll_drag_last_y := 0.0
var settings_data := {}
var settings_current_page := "home"
var settings_scroll_y := 0.0
var pin_input := ""
var pin_mode := "set"
var privacy_status_data := {}
var settings_status_text := "Saved"
var settings_dropdown_open := false
var settings_dropdown_options: Array = []
var settings_dropdown_section := ""
var settings_dropdown_key := ""
var quick_shelf_scroll_y := 0.0
var quick_shelf_status_text := ""
var reminders_data := {}
var reminders_due_data := {}
var reminders_status_text := ""
var reminders_selected_id := 0
var reminders_selected_item := {}
var reminders_mode := "list"
var reminders_upcoming_scroll_y := 0.0
var reminders_past_scroll_y := 0.0
var reminders_poll_accumulator := 0.0
var reminders_due_modal_open := false
var reminders_form_title := ""
var reminders_form_notes := ""
var reminders_form_date := ""
var reminders_form_time := ""
var reminders_form_private := false
var reminders_pending_due_id := 0
var reminders_pending_private_after_pin := false
var reminders_pending_private_form_mode := ""
var notifications_data := []
var notification_selected := {}
var notification_detail_modal_open := false
var notification_dismissed_ids := {}
var notification_swipe_start_x := 0.0
var notification_swipe_start_y := 0.0
var notification_swipe_active_id := ""
var notification_scroll_y := 0.0
var calendar_data := {}
var calendar_day_data := {}
var calendar_due_data := {}
var calendar_status_text := ""
var calendar_year := 0
var calendar_month := 0
var calendar_selected_date := ""
var calendar_selected_event_id := 0
var calendar_selected_event := {}
var calendar_mode := "month"
var calendar_form_title := ""
var calendar_form_description := ""
var calendar_form_date := ""
var calendar_form_time := ""
var calendar_form_reminder := 0
var calendar_form_snooze := 10
var calendar_form_repeat := "none"
var calendar_event_scroll_y := 0.0
var calendar_poll_accumulator := 0.0
var calendar_due_modal_open := false
var calendar_pending_due_event_id := 0
var calendar_pending_due_occurrence := ""
var todo_lists_data := {}
var todo_tasks_data := {}
var todo_due_data := {}
var todo_status_text := ""
var todo_mode := "lists"
var todo_selected_list_id := 0
var todo_selected_task_id := 0
var todo_selected_task := {}
var todo_scroll_y := 0.0
var todo_task_scroll_y := 0.0
var todo_form_title := ""
var todo_form_notes := ""
var todo_form_date := ""
var todo_form_time := ""
var todo_form_reminder_enabled := false
var todo_form_repeat_unit := "none"
var todo_form_repeat_interval := 1
var todo_list_form_name := ""
var todo_list_form_emoji := "📥"
var todo_poll_accumulator := 0.0
var todo_due_modal_open := false
var todo_pending_due_task_id := 0
var games_mode := "library"
var games_focus_index := 0
var games_library_scroll_y := 0.0
var games_help_open := false
var games_exit_confirm_return := "face_home"
var tic_tac_toe_mode := "someone"
var tic_tac_toe_menu_focus_index := 0
var tic_tac_toe_result_focus_index := 0
var tic_tac_toe_board: Array = [TTT_EMPTY, TTT_EMPTY, TTT_EMPTY, TTT_EMPTY, TTT_EMPTY, TTT_EMPTY, TTT_EMPTY, TTT_EMPTY, TTT_EMPTY]
var tic_tac_toe_current_player := TTT_PLAYER_X
var tic_tac_toe_selected_cell := 4
var tic_tac_toe_result := ""
var tic_tac_toe_game_over := false
var tic_tac_toe_status_text := "Player X turn"
var tic_tac_toe_nexa_thinking := false
var tic_tac_toe_thinking_elapsed := 0.0
var study_current_page := "home"
var study_scroll_y := 0.0
var study_data := {}
var study_status_text := "No study data yet"
var study_selected_deck_id := 0
var study_selected_quiz_id := 0
var study_selected_language_list_id := 0
var study_selected_card := {}
var study_selected_question := {}
var study_selected_word := {}
var study_topic_text := ""
var study_goal_text := ""
var study_note_text := ""
var study_planned_minutes := 25
var study_break_minutes := 5
var study_smart_minutes := 45
var study_smart_break_count := 1
var study_smart_break_minutes := 5
var study_segments: Array = [{"type": "focus", "minutes": 5}]
var study_selected_segment_index := 0
var study_segment_scroll_y := 0.0
var study_active_smart_session_id := 0
var study_delete_confirm_open := false
var study_flashcard_mode := "list"
var study_flashcard_answer_text := ""
var study_flashcard_revealed_answer := false
var study_flashcard_answer_checked := false
var study_flashcard_feedback_text := ""
var study_flashcard_delete_confirm_open := false
var study_quiz_mode := "list"
var study_quiz_answered := false
var study_quiz_feedback_text := ""
var study_quiz_delete_confirm_open := false
var study_pending_correct_answer := "A"
var study_language_mode := "list"
var study_language_answer_text := ""
var study_language_answer_checked := false
var study_language_revealed_word := false
var study_language_feedback_text := ""
var study_language_delete_confirm_open := false
var study_selected_language_word_id := 0
var study_pending_question := ""
var study_pending_answer := ""
var study_pending_quiz_question := ""
var study_pending_answer_a := ""
var study_pending_answer_b := ""
var study_pending_answer_c := ""
var study_pending_answer_d := ""
var study_pending_language_word := ""
var study_pending_language_pronunciation := ""
var text_input_open := false
var text_input_title := ""
var text_input_value := ""
var text_input_target := ""
var text_input_context := {}
var text_input_keyboard_mode := "text"
var study_timer_data := {}
var study_timer_poll_accumulator := 0.0
var home_message_active := false
var home_message_id := ""
var home_message_title := ""
var home_message_body := ""
var home_message_type := "info"
var home_message_priority := "normal"
var home_message_expression := "calm"
var home_message_source := "system"
var home_message_actions: Array = []
var home_message_scroll_y := 0.0
var home_message_fade := 0.0
var home_message_visible_elapsed := 0.0
var home_message_started_visible := false
var home_message_auto_dismiss_seconds := HOME_MESSAGE_AUTO_DISMISS_SECONDS
var home_message_auto_dismiss_enabled := true
var home_message_hidden_ids := {}
var home_message_enter_elapsed := 0.0
var home_message_enter_active := false
var home_message_enter_seconds := 0.40
var home_message_exit_active := false
var home_message_exit_elapsed := 0.0
var home_message_exit_seconds := 0.33
var home_message_exit_remember_hidden := true
var nexa_message_indicator_count := 0
var notification_indicator_count := 0
var nexa_messages_data: Array = []
var nexa_message_dismissed_ids := {}
var notification_preview_hidden_ids := {}
var messages_scroll_y := 0.0
var messages_swipe_active_id := ""
var messages_swipe_start_x := 0.0
var messages_swipe_start_y := 0.0
var messages_swipe_row_index := -1
var startup_sequence_active := false
var startup_sequence_elapsed := 0.0
var startup_sequence_finished := false
var startup_check_status := "pending"
var startup_check_done := false
var startup_greeting_shown := false
var face_expression := "calm"
var face_blink_active := false
var face_blink_progress := 0.0
var face_next_blink_seconds := 9.5
var face_idle_elapsed := 0.0
var face_mouth_style := "neutral"
var face_message_position_progress := 0.0
var current_face_expression := "calm"
var current_led_behavior := "idle_soft"
var current_sound_cue := "none"
var behavior_last_applied_id := ""
var inactivity_elapsed := 0.0
var inactivity_timeout_seconds := INACTIVITY_TIMEOUT_SECONDS
var study_break_game_suggested_for_segment_id := 0
var study_break_game_active := false
var study_break_game_started_at := ""
var study_break_return_screen := "Study"
var study_break_return_mode := "smart_study"
var study_break_return_pending := false
var study_break_last_segment_id := 0
var study_break_not_now_segment_id := 0

func _ready() -> void:
	custom_minimum_size = Vector2(WIDTH, HEIGHT)
	panel_data = diagnostics_data.load_panel_data()
	add_child(api)
	api.data_received.connect(_on_api_data_received)
	api.api_offline.connect(_on_api_offline)
	api.frame_received.connect(_on_camera_frame_received)
	set_process(true)
	_apply_home_behavior("startup_greeting")
	_start_startup_sequence()
	api.request_get("/api/settings")
	api.request_get("/api/hardware/state")
	_request_redraw()

func _process(delta: float) -> void:
	elapsed += delta
	redraw_accumulator += delta
	clock_redraw_accumulator += delta
	if startup_sequence_active:
		_update_startup_sequence(delta)
	_update_face_behavior(delta)
	_update_inactivity(delta)
	_update_presence_face_clock(delta)
	if transition_active:
		transition_progress = minf(1.0, transition_progress + delta / transition_duration)
		if transition_progress >= 1.0:
			transition_active = false
			if transition_closing:
				nav.current_screen = "Face Home"
			elif nav.current_screen == "Notification Control Center":
				control_center_refresh_pending = true
			if nav.current_screen == "Face Home":
				_show_next_home_item_if_available()
			_request_redraw()
	if tic_tac_toe_nexa_thinking:
		tic_tac_toe_thinking_elapsed += delta
		if tic_tac_toe_thinking_elapsed >= 0.30:
			_ttt_finish_nexa_turn()
	if home_message_active:
		home_message_fade = minf(1.0, home_message_fade + delta / ANIM_MESSAGE_FADE_SECONDS)
		face_message_position_progress = minf(1.0, face_message_position_progress + delta / ANIM_FACE_TO_MESSAGE_SECONDS)
		if home_message_exit_active:
			_update_home_message_exit_anim(delta)
		else:
			_update_home_message_enter(delta)
			if not home_message_enter_active:
				_update_home_message_visible_timer(delta)
	elif nav.current_screen == "Face Home" and not startup_sequence_active:
		_show_next_home_item_if_available()
	# Redraw is throttled: Face Home and transitions animate at 30 FPS max,
	# static panels draw only after input/open/tab changes, and Clock ticks once per second.
	var animated := startup_sequence_active or transition_active or nav.current_screen == "Face Home" or elapsed < nav.status_bubble_until or tic_tac_toe_nexa_thinking or face_blink_active
	var clock_tick := nav.current_screen == "Clock" and clock_redraw_accumulator >= CLOCK_REDRAW_INTERVAL
	if (animated or redraw_requested) and redraw_accumulator >= REDRAW_INTERVAL:
		redraw_accumulator = 0.0
		redraw_requested = false
		queue_redraw()
	elif clock_tick:
		clock_redraw_accumulator = 0.0
		queue_redraw()
	_update_api_polling(delta)

func _gui_input(event: InputEvent) -> void:
	if event is InputEventMouseButton or event is InputEventMouseMotion or event is InputEventScreenTouch or event is InputEventScreenDrag:
		_reset_user_activity()
	if event is InputEventMouseButton and event.pressed:
		if event.button_index == MOUSE_BUTTON_WHEEL_UP:
			_handle_scroll_wheel(event.position, -28.0)
			return
		if event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			_handle_scroll_wheel(event.position, 28.0)
			return
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		if event.pressed:
			if _begin_slider_drag(event.position):
				return
			if _begin_notification_swipe(event.position):
				return
			if _begin_message_row_swipe(event.position):
				return
			if _begin_scroll_drag(event.position):
				return
			else:
				gesture.begin(event.position, elapsed)
		else:
			if slider_drag_active:
				_finish_slider_drag()
				return
			if notification_swipe_active_id != "":
				_finish_notification_swipe(event.position)
				return
			if messages_swipe_active_id != "":
				_finish_message_row_swipe(event.position)
				return
			if scroll_drag_active:
				scroll_drag_active = false
				scroll_drag_area = ""
				return
			_handle_gesture(gesture.finish(event.position, elapsed), event.position)
	if event is InputEventMouseMotion and gesture.is_pressed:
		gesture.update(event.position)
	if event is InputEventMouseMotion and scroll_drag_active:
		_update_scroll_drag(event.position)
	if event is InputEventMouseMotion and slider_drag_active:
		_update_slider_drag(event.position)
	if event is InputEventScreenTouch:
		if event.pressed:
			if _begin_slider_drag(event.position):
				return
			if _begin_notification_swipe(event.position):
				return
			if _begin_message_row_swipe(event.position):
				return
			if _begin_scroll_drag(event.position):
				return
			gesture.begin(event.position, elapsed)
		else:
			if slider_drag_active:
				_finish_slider_drag()
				return
			if notification_swipe_active_id != "":
				_finish_notification_swipe(event.position)
				return
			if messages_swipe_active_id != "":
				_finish_message_row_swipe(event.position)
				return
			if scroll_drag_active:
				scroll_drag_active = false
				scroll_drag_area = ""
				return
			_handle_gesture(gesture.finish(event.position, elapsed), event.position)
	if event is InputEventScreenDrag:
		if gesture.is_pressed:
			gesture.update(event.position)
		if scroll_drag_active:
			_update_scroll_drag(event.position)
		if slider_drag_active:
			_update_slider_drag(event.position)

func _unhandled_input(event: InputEvent) -> void:
	if event.is_pressed():
		_reset_user_activity()
	if nav.current_screen != "Games" or event is InputEventKey:
		return
	if _handle_games_action_event(event):
		get_viewport().set_input_as_handled()

func _unhandled_key_input(event: InputEvent) -> void:
	if not event.pressed:
		return
	_reset_user_activity()
	if text_input_open:
		# InputEventKey handling keeps physical keyboard input active while the on-screen keyboard remains visible.
		if event.keycode == KEY_BACKSPACE:
			if text_input_value.length() > 0:
				text_input_value = text_input_value.substr(0, text_input_value.length() - 1)
		elif event.keycode == KEY_ENTER or event.keycode == KEY_KP_ENTER:
			_commit_text_input()
		elif event.keycode == KEY_ESCAPE:
			_close_text_input()
		elif event.keycode == KEY_SPACE:
			if text_input_keyboard_mode == "text":
				text_input_value += " "
		elif event.unicode > 0:
			var typed := char(event.unicode)
			if _text_input_char_allowed(typed):
				text_input_value += typed
		_request_redraw()
		return
	if nav.current_screen == "Face Home" and home_message_active and _handle_home_message_action_event(event):
		return
	if nav.current_screen == "Messages" and _handle_messages_action_event(event):
		return
	if nav.current_screen == "Games" and _handle_games_action_event(event):
		return
	if event.keycode == KEY_LEFT and nav.current_screen == "Face Home":
		_open_menu()
	elif event.keycode == KEY_RIGHT and nav.current_screen == "Face Home":
		_open_clock()
	elif event.keycode == KEY_DOWN and nav.current_screen == "Face Home":
		_open_control_center()
	elif event.keycode == KEY_ESCAPE:
		if text_input_open:
			_close_text_input()
			_request_redraw()
			return
		if nav.current_screen == "Study" and study_current_page != "home":
			_open_study_page("home")
			return
		if nav.current_screen == "Settings" and settings_dropdown_open:
			_close_settings_dropdown()
			_request_redraw()
			return
		if nav.current_screen == "Settings" and settings_current_page != "home":
			_settings_back()
			_request_redraw()
			return
		_go_home()
	_request_redraw()

func _handle_gesture(action: String, position: Vector2) -> void:
	if action == "tap":
		_handle_tap(position)
	elif action == "long_press" and nav.current_screen == "Face Home":
		_open_settings()
	elif nav.current_screen == "Face Home":
		if action == "swipe_left":
			_open_menu()
		elif action == "swipe_right":
			_open_clock()
		elif action == "swipe_down":
			_open_control_center()
		elif action == "swipe_up":
			_open_quick_shelf()
	elif nav.current_screen == "Clock" and action.begins_with("swipe_"):
		# Clock is a passive glance screen, so any swipe returns to Face Home.
		_go_home()
	elif nav.current_screen == "Menu" and action == "swipe_right":
		_go_home()
	elif nav.current_screen == "Notification Control Center" and action == "swipe_up":
		_go_home()
	elif nav.current_screen == "Quick Shelf" and action == "swipe_down":
		_go_home()
	elif nav.current_screen == "Study" and study_current_page == "home" and (action == "swipe_right" or action == "swipe_down"):
		_go_home()
	elif nav.current_screen == "Games" and action == "swipe_right":
		_back_from_game_screen()
	_request_redraw()

func _handle_tap(position: Vector2) -> void:
	_reset_user_activity()
	if _handle_top_indicator_tap(position):
		return
	if nav.current_screen == "Face Home" and (reminders_due_modal_open or calendar_due_modal_open or todo_due_modal_open) and _handle_due_notification_modal_tap(position):
		return
	if text_input_open:
		_handle_text_input_tap(position)
		return
	if transition_active:
		return
	if nav.current_screen == "Face Home":
		if home_message_active:
			_handle_home_message_tap(position)
			return
		nav.show_status_bubble(elapsed)
		return
	if nav.current_screen == "Menu":
		_handle_menu_tap(position)
		return
	if nav.current_screen == "Environment":
		if Rect2(520, 22, 92, 34).has_point(position):
			_go_home()
		return
	if nav.current_screen == "Notification Control Center":
		_handle_control_center_tap(position)
		return
	if nav.current_screen == "Diagnostics":
		if Rect2(536, 22, 78, 34).has_point(position):
			_go_home()
			return
		_handle_diagnostics_action_tap(position)
		_handle_diagnostics_tap(position)
		return
	if nav.current_screen == "Settings":
		_handle_settings_tap(position)
		return
	if nav.current_screen == "Quick Shelf":
		_handle_quick_shelf_panel_tap(position)
		return
	if nav.current_screen == "Study":
		_handle_study_tap(position)
		return
	if nav.current_screen == "Reminders":
		_handle_reminders_tap(position)
		return
	if nav.current_screen == "Calendar":
		_handle_calendar_tap(position)
		return
	if nav.current_screen == "To Do":
		_handle_todo_tap(position)
		return
	if nav.current_screen == "Games":
		_handle_games_tap(position)
		return
	if nav.current_screen == "Messages":
		_handle_messages_tap(position)
		return

func _handle_menu_tap(position: Vector2) -> void:
	for index in range(MENU_TILES.size()):
		var rect: Rect2 = _menu_tile_rect(index)
		if rect.has_point(position):
			hardware_menu_focus_index = index
			var tile: Dictionary = MENU_TILES[index] as Dictionary
			if tile["title"] == "Time":
				_open_clock()
			elif tile["title"] == "Study":
				_open_study("home")
			elif tile["title"] == "Environment":
				_open_environment()
			elif tile["title"] == "Reminders":
				_open_reminders()
			elif tile["title"] == "Calendar":
				_open_calendar()
			elif tile["title"] == "To Do":
				_open_todo()
			elif tile["title"] == "Games":
				_open_games()
			elif tile["title"] == "Diagnostics":
				_open_diagnostics()
			elif tile["title"] == "Settings":
				_open_settings()
			else:
				_open_placeholder(tile["title"] + " placeholder")
			return

func _handle_diagnostics_tap(position: Vector2) -> void:
	for index in range(DIAGNOSTIC_TABS.size()):
		var rect: Rect2 = _diagnostic_tab_rect(index)
		if rect.has_point(position):
			if active_tab == "Camera" and str(DIAGNOSTIC_TABS[index]) != "Camera":
				_stop_camera_preview()
			active_tab = str(DIAGNOSTIC_TABS[index])
			diagnostic_scroll_y = 0.0
			active_tab_data = {}
			_request_active_diagnostics_tab()
			_request_redraw()
			return

func _handle_control_center_tap(position: Vector2) -> void:
	if _handle_notification_tap(position):
		return
	for index in range(6):
		var rect: Rect2 = Rect2(44.0 + float(index % 3) * 184.0, 124.0 + float(int(index / 3)) * 76.0, 164.0, 62.0)
		if not rect.has_point(position):
			continue
		if index == 0:
			selected_control_detail = "brightness"
		elif index == 1:
			selected_control_detail = "sound"
		elif index == 2:
			quiet_mode_local = not quiet_mode_local
			control_center_data["quiet_mode"] = quiet_mode_local
			api.request_post("/api/control/quiet-mode", {"enabled": quiet_mode_local})
			selected_control_detail = "quiet"
		elif index == 3:
			selected_control_detail = "wifi"
			network_detail_pending = true
		elif index == 4:
			remote_network_local = "on" if remote_network_local != "on" else "off"
			control_center_data["remote_network_state"] = remote_network_local
			api.request_post("/api/control/remote-network", {"state": remote_network_local})
			selected_control_detail = "remote"
		elif index == 5:
			_open_diagnostics()

func _handle_notification_tap(position: Vector2) -> bool:
	if nav.current_screen != "Notification Control Center":
		return false
	if notification_detail_modal_open:
		if Rect2(104, 354, 120, 34).has_point(position):
			notification_detail_modal_open = false
			notification_selected = {}
			_request_redraw()
			return true
		if Rect2(260, 354, 120, 34).has_point(position):
			if str(notification_selected.get("type", "")) == "todo":
				api.request_post("/api/todo/tasks/mark-done", {"id": int(notification_selected.get("source_id", 0))})
				_local_remove_notification(str(notification_selected.get("id", "")), true)
			else:
				_dismiss_notification(notification_selected)
			return true
		if Rect2(416, 354, 120, 34).has_point(position):
			_open_notification_source(notification_selected)
			return true
	if not _notification_scroll_rect().has_point(position):
		return false
	for index in range(notifications_data.size()):
		var row := _notification_row_rect(index)
		if not row.has_point(position):
			continue
		var notification: Dictionary = notifications_data[index] as Dictionary
		if _notification_delete_rect(index).has_point(position):
			_dismiss_notification(notification)
			return true
		notification_selected = notification
		notification_detail_modal_open = true
		_request_redraw()
		return true
	return false

func _begin_notification_swipe(position: Vector2) -> bool:
	if nav.current_screen != "Notification Control Center" or notification_detail_modal_open:
		return false
	if not _notification_scroll_rect().has_point(position):
		return false
	for index in range(notifications_data.size()):
		if _notification_row_rect(index).has_point(position):
			var notification: Dictionary = notifications_data[index] as Dictionary
			notification_swipe_active_id = str(notification.get("id", ""))
			notification_swipe_start_x = position.x
			notification_swipe_start_y = position.y
			return notification_swipe_active_id != ""
	return false

func _finish_notification_swipe(position: Vector2) -> void:
	var active_id := notification_swipe_active_id
	notification_swipe_active_id = ""
	if active_id == "":
		return
	var dx := position.x - notification_swipe_start_x
	var dy := position.y - notification_swipe_start_y
	var notification := _notification_by_id(active_id)
	if notification.is_empty():
		return
	if absf(dx) > 60.0 and absf(dx) > absf(dy):
		_dismiss_notification(notification)
		return
	if absf(dy) > 60.0 and absf(dy) > absf(dx):
		_apply_scroll("notifications", -dy)
		return
	for index in range(notifications_data.size()):
		var row: Rect2 = _notification_row_rect(index)
		if str((notifications_data[index] as Dictionary).get("id", "")) != active_id:
			continue
		if _notification_delete_rect(index).has_point(position):
			_dismiss_notification(notification)
		elif row.has_point(position) and absf(dx) < 18.0 and absf(dy) < 18.0:
			notification_selected = notification
			notification_detail_modal_open = true
			_request_redraw()
		return

func _open_notification_source(notification: Dictionary) -> void:
	if str(notification.get("type", "")) == "reminder":
		reminders_selected_id = int(notification.get("source_id", 0))
		notification_detail_modal_open = false
		notification_selected = {}
		_open_reminders()
		_request_redraw()
		return
	if str(notification.get("type", "")) == "calendar":
		calendar_selected_event_id = int(notification.get("source_id", 0))
		calendar_selected_date = str(notification.get("source_date", calendar_selected_date))
		notification_detail_modal_open = false
		notification_selected = {}
		_open_calendar()
		_request_redraw()
		return
	if str(notification.get("type", "")) == "todo":
		todo_selected_list_id = int(notification.get("list_id", 0))
		todo_selected_task_id = int(notification.get("source_id", 0))
		notification_detail_modal_open = false
		notification_selected = {}
		_open_todo_list(todo_selected_list_id)
		todo_mode = "task_detail"
		_request_redraw()
		return

func _handle_settings_tap(position: Vector2) -> void:
	if settings_dropdown_open:
		_handle_settings_dropdown_tap(position)
		return
	if Rect2(520, 22, 92, 34).has_point(position):
		_settings_back()
		return
	if settings_current_page == "home":
		for index in range(SETTINGS_TILES.size()):
			var rect: Rect2 = _settings_tile_rect(index)
			if rect.has_point(position):
				var tile: Dictionary = SETTINGS_TILES[index] as Dictionary
				var title: String = str(tile["title"])
				settings_current_page = _settings_page_id(title)
				settings_scroll_y = 0.0
				if settings_current_page == "privacy":
					api.request_get("/api/privacy/status")
				elif settings_current_page == "network":
					api.request_get("/api/network")
				_request_redraw()
				return
		return
	if settings_current_page == "privacy":
		_handle_pin_tap(position)
		return
	if settings_current_page == "quick_shelf":
		_handle_quick_shelf_tap(position)
		return
	_handle_settings_detail_tap(position)

func _settings_back() -> void:
	if settings_current_page == "home":
		_go_home()
	else:
		settings_current_page = "home"
		settings_scroll_y = 0.0
	_request_redraw()

func _settings_page_id(title: String) -> String:
	return title.to_lower().replace(" ", "_")

func _setting_row_rect(index: int) -> Rect2:
	return Rect2(44, 114.0 + float(index) * 46.0 - settings_scroll_y, 552, 38)

func _handle_settings_detail_tap(position: Vector2) -> void:
	var rows: Array = _settings_rows_for_page(settings_current_page)
	for index in range(rows.size()):
		var rect: Rect2 = _setting_row_rect(index)
		if rect.has_point(position):
			var row: Dictionary = rows[index] as Dictionary
			_apply_settings_row(row)
			return

func _handle_quick_shelf_panel_tap(position: Vector2) -> void:
	var tiles: Array = _settings_enabled_quick_shelf()
	if tiles.is_empty():
		tiles = ["Brightness", "Sound", "Quiet Mode", "Network", "Reminders", "Study", "Diagnostics", "Settings"]
	for index in range(tiles.size()):
		var rect: Rect2 = _quick_shelf_tile_rect(index)
		if rect.has_point(position):
			_activate_quick_shelf_tile(str(tiles[index]))
			return

func _activate_quick_shelf_tile(tile_name: String) -> void:
	quick_shelf_status_text = ""
	if tile_name == "Diagnostics":
		quick_shelf_status_text = "Opening Diagnostics"
		_open_diagnostics()
	elif tile_name == "Settings":
		quick_shelf_status_text = "Opening Settings"
		_open_settings()
	elif tile_name == "Clock":
		quick_shelf_status_text = "Clock"
		_open_clock()
	elif tile_name == "Network":
		quick_shelf_status_text = "Opening Network"
		_open_diagnostics_tab("Network")
	elif tile_name == "Camera":
		quick_shelf_status_text = "Opening Camera"
		_open_diagnostics_tab("Camera")
	elif tile_name == "Logs":
		quick_shelf_status_text = "Opening Logs"
		_open_diagnostics_tab("Logs")
	elif tile_name == "Reports":
		quick_shelf_status_text = "Opening Reports"
		_open_diagnostics_tab("Reports")
	elif tile_name == "Study":
		quick_shelf_status_text = "Opening Study"
		_open_study("home")
	elif tile_name == "Air Quality" or tile_name == "Temperature" or tile_name == "Environment":
		quick_shelf_status_text = "Opening Environment"
		_open_environment()
	elif tile_name == "Study Stats":
		quick_shelf_status_text = "Opening Study Stats"
		_open_study("stats")
	elif tile_name == "Games":
		quick_shelf_status_text = "Opening Games"
		_open_games()
	elif tile_name == "Reminders":
		quick_shelf_status_text = "Opening Reminders"
		_open_reminders()
	elif tile_name == "Calendar":
		quick_shelf_status_text = "Opening Calendar"
		_open_calendar()
	elif tile_name == "To Do" or tile_name == "Tasks":
		quick_shelf_status_text = "Opening To Do"
		_open_todo()
	elif tile_name == "Quiet Mode":
		quiet_mode_local = not quiet_mode_local
		control_center_data["quiet_mode"] = quiet_mode_local
		_settings_update("modes", "current_mode", "Quiet" if quiet_mode_local else "Normal")
		api.request_post("/api/control/quiet-mode", {"enabled": quiet_mode_local})
		quick_shelf_status_text = "Quiet Mode " + ("On" if quiet_mode_local else "Off")
	elif tile_name == "Brightness":
		quick_shelf_status_text = "Brightness " + str(brightness_percent) + "%"
	elif tile_name == "Sound":
		quick_shelf_status_text = "Sound " + str(sound_percent) + "%"
	elif tile_name == "Exit NeXa":
		quick_shelf_status_text = "Exit NeXa planned"
		_open_settings_page("exit_nexa")
	else:
		quick_shelf_status_text = tile_name + " planned"
	_request_redraw()

func _open_diagnostics_tab(tab_name: String) -> void:
	_open_diagnostics()
	active_tab = tab_name
	active_tab_data = {}
	_request_active_diagnostics_tab()
	_request_redraw()

func _open_settings_page(page: String) -> void:
	_open_settings()
	settings_current_page = page
	settings_scroll_y = 0.0

func _handle_quick_shelf_tap(position: Vector2) -> void:
	var enabled: Array = _settings_enabled_quick_shelf()
	for index in range(QUICK_SHELF_OPTIONS.size()):
		var rect: Rect2 = Rect2(44.0 + float(index % 2) * 282.0, 136.0 + float(int(index / 2)) * 44.0 - settings_scroll_y, 260.0, 36.0)
		if rect.has_point(position):
			var name: String = str(QUICK_SHELF_OPTIONS[index])
			if enabled.has(name):
				enabled.erase(name)
			else:
				enabled.append(name)
			_settings_update("quick_shelf", "enabled_tiles", enabled)
			return

func _handle_study_tap(position: Vector2) -> void:
	if Rect2(520, 22, 92, 34).has_point(position):
		if study_current_page == "home":
			_go_home()
		else:
			_open_study_page("home")
		return
	if study_current_page == "home":
		for index in range(STUDY_TILES.size()):
			var rect: Rect2 = _study_tile_rect(index)
			if rect.has_point(position):
				var title: String = str((STUDY_TILES[index] as Dictionary)["title"])
				_open_study_page(_study_page_id(title))
				return
	if study_current_page == "pomodoro":
		_handle_study_pomodoro_tap(position)
	elif study_current_page == "smart_study":
		_handle_study_smart_tap(position)
	elif study_current_page == "flashcards":
		_handle_study_flashcards_tap(position)
	elif study_current_page == "quizzes":
		_handle_study_quizzes_tap(position)
	elif study_current_page == "languages":
		_handle_study_languages_tap(position)
	elif study_current_page == "settings":
		_handle_study_settings_tap(position)

func _handle_reminders_tap(position: Vector2) -> void:
	if reminders_due_modal_open:
		if Rect2(164, 324, 96, 34).has_point(position):
			_dismiss_pending_due_notification()
			return
			if Rect2(272, 324, 112, 34).has_point(position):
				api.request_post("/api/reminders/snooze", {"id": reminders_pending_due_id, "minutes": 5})
				_local_remove_notification("reminder:" + str(reminders_pending_due_id), false)
				reminders_due_modal_open = false
				return
		if Rect2(396, 324, 96, 34).has_point(position):
			reminders_due_modal_open = false
			reminders_selected_id = reminders_pending_due_id
			_open_reminders()
			return
	if Rect2(520, 22, 92, 34).has_point(position):
		_go_home()
		return
	if reminders_mode == "delete_confirm":
		if Rect2(78, 354, 210, 42).has_point(position):
			reminders_mode = "list"
		elif Rect2(352, 354, 210, 42).has_point(position):
			api.request_post("/api/reminders/delete", {"id": reminders_selected_id, "confirm_text": "DELETE_REMINDER"})
			reminders_selected_id = 0
			reminders_selected_item = {}
		_request_redraw()
		return
	if reminders_mode == "add" or reminders_mode == "edit":
		_handle_reminders_form_tap(position)
		return
	if Rect2(44, 88, 160, 34).has_point(position):
		_reminders_open_add_form()
	elif Rect2(220, 88, 160, 34).has_point(position):
		if reminders_selected_id <= 0:
			reminders_status_text = "Select one reminder first."
		else:
			_reminders_open_edit_form()
	elif Rect2(396, 88, 160, 34).has_point(position):
		if reminders_selected_id <= 0:
			reminders_status_text = "Select one reminder first."
		else:
			reminders_mode = "delete_confirm"
	for index in range(_reminders_list_count("upcoming")):
		var rect := _reminder_row_rect("upcoming", index)
		if rect.has_point(position):
			_select_reminder("upcoming", index)
			return
	for index in range(_reminders_list_count("past")):
		var rect := _reminder_row_rect("past", index)
		if rect.has_point(position):
			_select_reminder("past", index)
			return
	_request_redraw()

func _handle_reminders_form_tap(position: Vector2) -> void:
	if Rect2(44, 136, 552, 34).has_point(position):
		_open_text_input("Reminder text", reminders_form_title, "reminder_title", {})
	elif Rect2(44, 178, 552, 34).has_point(position):
		_open_text_input("Notes", reminders_form_notes, "reminder_notes", {})
	elif Rect2(44, 220, 260, 34).has_point(position):
		_open_text_input("Date YYYY-MM-DD", reminders_form_date, "reminder_date", {"keyboard_mode": "datetime"})
	elif Rect2(324, 220, 170, 34).has_point(position):
		_open_text_input("Time HH:MM", reminders_form_time, "reminder_time", {"keyboard_mode": "datetime"})
	elif Rect2(510, 220, 86, 34).has_point(position):
		_reminders_toggle_private()
	elif Rect2(44, 274, 76, 30).has_point(position):
		_reminders_apply_relative_minutes(5)
	elif Rect2(130, 274, 76, 30).has_point(position):
		_reminders_apply_relative_minutes(15)
	elif Rect2(216, 274, 76, 30).has_point(position):
		_reminders_apply_relative_minutes(30)
	elif Rect2(302, 274, 76, 30).has_point(position):
		_reminders_apply_relative_minutes(60)
	elif Rect2(388, 274, 92, 30).has_point(position):
		_reminders_apply_relative_days(1)
	elif Rect2(490, 274, 106, 30).has_point(position):
		_reminders_apply_relative_days(7)
	elif Rect2(44, 390, 170, 34).has_point(position):
		_reminders_save_form()
	elif Rect2(232, 390, 170, 34).has_point(position):
		reminders_mode = "list"

func _handle_calendar_tap(position: Vector2) -> void:
	if Rect2(520, 22, 92, 34).has_point(position):
		_go_home()
		return
	if calendar_mode == "delete_confirm":
		if Rect2(78, 354, 210, 42).has_point(position):
			calendar_mode = "details"
		elif Rect2(352, 354, 210, 42).has_point(position):
			api.request_post("/api/calendar/events/delete", {"id": calendar_selected_event_id, "confirm_text": "DELETE_CALENDAR_EVENT"})
		_request_redraw()
		return
	if calendar_mode == "add" or calendar_mode == "edit":
		_handle_calendar_form_tap(position)
		return
	if Rect2(330, 30, 84, 30).has_point(position):
		_calendar_change_month(-1)
		return
	if Rect2(422, 30, 74, 30).has_point(position):
		_calendar_change_month(1)
		return
	if Rect2(44, 426, 92, 34).has_point(position):
		_calendar_open_add_form()
		return
	if Rect2(148, 426, 92, 34).has_point(position):
		if calendar_selected_event_id <= 0:
			calendar_status_text = "Select one event first."
		else:
			_calendar_open_edit_form()
		_request_redraw()
		return
	if Rect2(252, 426, 92, 34).has_point(position):
		if calendar_selected_event_id <= 0:
			calendar_status_text = "Select one event first."
		else:
			calendar_mode = "delete_confirm"
		_request_redraw()
		return
	for index in range(42):
		var cell := _calendar_cell_rect(index)
		if cell.has_point(position):
			_calendar_select_cell(index)
			return
	var events: Array = _calendar_day_events()
	for index in range(events.size()):
		var row := _calendar_event_row_rect(index)
		if row.has_point(position):
			var event: Dictionary = events[index] as Dictionary
			calendar_selected_event_id = int(event.get("id", 0))
			calendar_selected_event = event
			_request_redraw()
			return

func _handle_calendar_form_tap(position: Vector2) -> void:
	if Rect2(44, 118, 552, 32).has_point(position):
		_open_text_input("Event title", calendar_form_title, "calendar_title", {})
	elif Rect2(44, 156, 552, 32).has_point(position):
		_open_text_input("Description", calendar_form_description, "calendar_description", {})
	elif Rect2(44, 194, 260, 32).has_point(position):
		_open_text_input("Date YYYY-MM-DD", calendar_form_date, "calendar_date", {"keyboard_mode": "datetime"})
	elif Rect2(324, 194, 170, 32).has_point(position):
		_open_text_input("Time HH:MM", calendar_form_time, "calendar_time", {"keyboard_mode": "datetime"})
	elif Rect2(44, 240, 160, 32).has_point(position):
		_calendar_cycle_reminder()
	elif Rect2(224, 240, 160, 32).has_point(position):
		_calendar_cycle_snooze()
	elif Rect2(404, 240, 160, 32).has_point(position):
		_calendar_cycle_repeat()
	elif Rect2(44, 390, 170, 34).has_point(position):
		_calendar_save_form()
	elif Rect2(232, 390, 170, 34).has_point(position):
		calendar_mode = "details"

func _handle_todo_tap(position: Vector2) -> void:
	if Rect2(520, 22, 92, 34).has_point(position):
		_go_home()
		return
	if todo_mode == "delete_confirm":
		if Rect2(78, 354, 210, 42).has_point(position):
			todo_mode = "task_detail"
		elif Rect2(352, 354, 210, 42).has_point(position):
			api.request_post("/api/todo/tasks/delete", {"id": todo_selected_task_id, "confirm_text": "DELETE_TODO_TASK"})
			todo_mode = "list_detail"
		_request_redraw()
		return
	if todo_mode == "list_form":
		_handle_todo_list_form_tap(position)
		return
	if todo_mode == "task_form":
		_handle_todo_task_form_tap(position)
		return
	if todo_mode == "task_detail":
		_handle_todo_task_detail_tap(position)
		return
	if todo_mode == "lists":
		if Rect2(412, 26, 92, 30).has_point(position):
			_todo_open_list_form()
			return
		var lists := _todo_lists()
		for index in range(lists.size()):
			var rect := _todo_list_card_rect(index)
			if rect.has_point(position):
				var item: Dictionary = lists[index] as Dictionary
				_open_todo_list(int(item.get("id", 0)))
				return
		return
	if todo_mode == "list_detail":
		if Rect2(30, 70, 74, 30).has_point(position):
			todo_mode = "lists"
			api.request_get("/api/todo/lists")
			_request_redraw()
			return
		if Rect2(400, 26, 92, 30).has_point(position):
			_todo_open_task_form(false)
			return
		var active := _todo_active_tasks()
		for index in range(active.size()):
			var row := _todo_task_row_rect(index, false)
			if row.has_point(position):
				var task: Dictionary = active[index] as Dictionary
				_todo_select_task(task)
				todo_mode = "task_detail"
				return
		var completed := _todo_completed_tasks()
		for index in range(completed.size()):
			var crow := _todo_task_row_rect(index, true)
			if crow.has_point(position):
				var ctask: Dictionary = completed[index] as Dictionary
				_todo_select_task(ctask)
				todo_mode = "task_detail"
				return

func _handle_todo_list_form_tap(position: Vector2) -> void:
	if Rect2(44, 150, 120, 34).has_point(position):
		_open_text_input("Emoji", todo_list_form_emoji, "todo_list_emoji", {})
	elif Rect2(178, 150, 418, 34).has_point(position):
		_open_text_input("List name", todo_list_form_name, "todo_list_name", {})
	elif Rect2(44, 390, 170, 34).has_point(position):
		if todo_list_form_name.strip_edges() == "":
			todo_status_text = "List name is required."
		else:
			api.request_post("/api/todo/lists/create", {"name": todo_list_form_name, "emoji": todo_list_form_emoji})
			todo_mode = "lists"
	elif Rect2(232, 390, 170, 34).has_point(position):
		todo_mode = "lists"
	_request_redraw()

func _handle_todo_task_form_tap(position: Vector2) -> void:
	if Rect2(44, 118, 552, 32).has_point(position):
		_open_text_input("Task", todo_form_title, "todo_title", {})
	elif Rect2(44, 156, 552, 32).has_point(position):
		_open_text_input("Notes", todo_form_notes, "todo_notes", {})
	elif Rect2(44, 202, 120, 32).has_point(position):
		todo_form_reminder_enabled = not todo_form_reminder_enabled
		_request_redraw()
	elif Rect2(178, 202, 180, 32).has_point(position):
		_open_text_input("Date YYYY-MM-DD", todo_form_date, "todo_date", {"keyboard_mode": "datetime"})
	elif Rect2(374, 202, 120, 32).has_point(position):
		_open_text_input("Time HH:MM", todo_form_time, "todo_time", {"keyboard_mode": "datetime"})
	elif Rect2(44, 250, 170, 32).has_point(position):
		_todo_cycle_repeat()
	elif Rect2(230, 250, 48, 32).has_point(position):
		todo_form_repeat_interval = maxi(1, todo_form_repeat_interval - 1)
		_request_redraw()
	elif Rect2(288, 250, 48, 32).has_point(position):
		todo_form_repeat_interval = mini(999, todo_form_repeat_interval + 1)
		_request_redraw()
	elif Rect2(44, 390, 170, 34).has_point(position):
		_todo_save_task_form()
	elif Rect2(232, 390, 170, 34).has_point(position):
		todo_mode = "list_detail"
	_request_redraw()

func _handle_todo_task_detail_tap(position: Vector2) -> void:
	if Rect2(44, 386, 116, 34).has_point(position):
		if str(todo_selected_task.get("status", "active")) == "completed":
			api.request_post("/api/todo/tasks/mark-active", {"id": todo_selected_task_id})
		else:
			api.request_post("/api/todo/tasks/mark-done", {"id": todo_selected_task_id})
		todo_mode = "list_detail"
	elif Rect2(174, 386, 92, 34).has_point(position):
		_todo_open_task_form(true)
	elif Rect2(280, 386, 92, 34).has_point(position):
		todo_mode = "delete_confirm"
	elif Rect2(386, 386, 92, 34).has_point(position):
		todo_mode = "list_detail"
	_request_redraw()

func _reminders_open_add_form() -> void:
	var now := Time.get_datetime_dict_from_system()
	reminders_mode = "add"
	reminders_form_title = ""
	reminders_form_notes = ""
	reminders_form_date = "%04d-%02d-%02d" % [now.year, now.month, now.day]
	reminders_form_time = "%02d:%02d" % [now.hour, now.minute]
	reminders_form_private = false
	api.request_get("/api/privacy/status")

func _calendar_open_add_form() -> void:
	calendar_mode = "add"
	calendar_form_title = ""
	calendar_form_description = ""
	calendar_form_date = calendar_selected_date
	calendar_form_time = "09:00"
	calendar_form_reminder = 0
	calendar_form_snooze = 10
	calendar_form_repeat = "none"
	_request_redraw()

func _calendar_open_edit_form() -> void:
	calendar_mode = "edit"
	calendar_form_title = str(calendar_selected_event.get("title", ""))
	calendar_form_description = str(calendar_selected_event.get("description", ""))
	calendar_form_date = str(calendar_selected_event.get("occurrence_date", calendar_selected_event.get("start_date", calendar_selected_date)))
	calendar_form_time = str(calendar_selected_event.get("start_time", "09:00"))
	calendar_form_reminder = int(calendar_selected_event.get("reminder_minutes_before", 0))
	calendar_form_snooze = 10
	calendar_form_repeat = str(calendar_selected_event.get("repeat_type", "none"))
	_request_redraw()

func _calendar_cycle_reminder() -> void:
	var options := [-1, 0, 5, 15, 60]
	var index := options.find(calendar_form_reminder)
	calendar_form_reminder = int(options[(index + 1) % options.size()])
	_request_redraw()

func _calendar_cycle_snooze() -> void:
	var options := [0, 5, 10, 30]
	var index := options.find(calendar_form_snooze)
	calendar_form_snooze = int(options[(index + 1) % options.size()])
	_request_redraw()

func _calendar_cycle_repeat() -> void:
	var options := ["none", "daily", "weekly", "monthly", "yearly"]
	var index := options.find(calendar_form_repeat)
	calendar_form_repeat = str(options[(index + 1) % options.size()])
	_request_redraw()

func _calendar_save_form() -> void:
	if calendar_form_title.strip_edges() == "":
		calendar_status_text = "Event title is required."
		_request_redraw()
		return
	if not _reminders_date_valid(calendar_form_date) or not _reminders_time_valid(calendar_form_time):
		calendar_status_text = "Use YYYY-MM-DD and HH:MM."
		_request_redraw()
		return
	var payload := {
		"title": calendar_form_title,
		"description": calendar_form_description,
		"start_date": calendar_form_date,
		"start_time": calendar_form_time,
		"reminder_minutes_before": calendar_form_reminder,
		"snooze_minutes": calendar_form_snooze,
		"repeat_type": calendar_form_repeat
	}
	if calendar_mode == "edit":
		payload["id"] = calendar_selected_event_id
		api.request_post("/api/calendar/events/update", payload)
	else:
		api.request_post("/api/calendar/events/create", payload)
	calendar_mode = "details"

func _calendar_reminder_label() -> String:
	if calendar_form_reminder < 0:
		return "Off"
	if calendar_form_reminder == 0:
		return "At time"
	if calendar_form_reminder == 60:
		return "1 hour before"
	return str(calendar_form_reminder) + " min before"

func _calendar_snooze_label() -> String:
	return "Off" if calendar_form_snooze <= 0 else str(calendar_form_snooze) + " min"

func _calendar_repeat_label() -> String:
	return calendar_form_repeat.capitalize()

func _todo_open_list_form() -> void:
	todo_mode = "list_form"
	todo_list_form_name = ""
	todo_list_form_emoji = "📥"
	_request_redraw()

func _todo_open_task_form(editing: bool) -> void:
	todo_mode = "task_form"
	if editing:
		todo_form_title = str(todo_selected_task.get("title", ""))
		todo_form_notes = str(todo_selected_task.get("notes", ""))
		todo_form_date = str(todo_selected_task.get("due_date", ""))
		todo_form_time = str(todo_selected_task.get("due_time", ""))
		todo_form_reminder_enabled = bool(todo_selected_task.get("reminder_enabled", false))
		todo_form_repeat_unit = str(todo_selected_task.get("repeat_unit", "none"))
		todo_form_repeat_interval = maxi(1, int(todo_selected_task.get("repeat_interval", 1)))
	else:
		var now := Time.get_datetime_dict_from_system()
		todo_selected_task_id = 0
		todo_selected_task = {}
		todo_form_title = ""
		todo_form_notes = ""
		todo_form_date = "%04d-%02d-%02d" % [now.year, now.month, now.day]
		todo_form_time = "%02d:%02d" % [now.hour, now.minute]
		todo_form_reminder_enabled = false
		todo_form_repeat_unit = "none"
		todo_form_repeat_interval = 1
	_request_redraw()

func _todo_cycle_repeat() -> void:
	var options := ["none", "hours", "days", "weekly", "monthly", "yearly"]
	var index := options.find(todo_form_repeat_unit)
	todo_form_repeat_unit = str(options[(index + 1) % options.size()])
	if todo_form_repeat_unit == "hours" or todo_form_repeat_unit == "days":
		todo_form_repeat_interval = maxi(1, todo_form_repeat_interval)
	else:
		todo_form_repeat_interval = 1
	_request_redraw()

func _todo_repeat_label() -> String:
	if todo_form_repeat_unit == "hours":
		return "Every " + str(todo_form_repeat_interval) + " hours"
	if todo_form_repeat_unit == "days":
		return "Every " + str(todo_form_repeat_interval) + " days"
	if todo_form_repeat_unit == "weekly":
		return "Weekly"
	if todo_form_repeat_unit == "monthly":
		return "Monthly"
	if todo_form_repeat_unit == "yearly":
		return "Yearly"
	return "None"

func _todo_save_task_form() -> void:
	if todo_form_title.strip_edges() == "":
		todo_status_text = "Task title is required."
		return
	if todo_form_reminder_enabled and (not _reminders_date_valid(todo_form_date) or not _reminders_time_valid(todo_form_time)):
		todo_status_text = "Use YYYY-MM-DD and HH:MM."
		return
	var payload := {
		"list_id": todo_selected_list_id,
		"title": todo_form_title,
		"notes": todo_form_notes,
		"due_date": todo_form_date,
		"due_time": todo_form_time,
		"reminder_enabled": todo_form_reminder_enabled,
		"repeat_unit": todo_form_repeat_unit,
		"repeat_interval": todo_form_repeat_interval,
		"status": str(todo_selected_task.get("status", "active"))
	}
	if todo_selected_task_id > 0:
		payload["id"] = todo_selected_task_id
		api.request_post("/api/todo/tasks/update", payload)
	else:
		api.request_post("/api/todo/tasks/create", payload)
	todo_mode = "list_detail"

func _todo_select_task(task: Dictionary) -> void:
	todo_selected_task = task
	todo_selected_task_id = int(task.get("id", 0))
	_request_redraw()

func _reminders_open_edit_form() -> void:
	reminders_mode = "edit"
	reminders_form_title = str(reminders_selected_item.get("title", ""))
	reminders_form_notes = str(reminders_selected_item.get("notes", ""))
	var due_text := str(reminders_selected_item.get("due_at", ""))
	reminders_form_date = due_text.substr(0, 10)
	reminders_form_time = due_text.substr(11, 5)
	reminders_form_private = bool(reminders_selected_item.get("is_private", false))
	api.request_get("/api/privacy/status")

func _reminders_toggle_private() -> void:
	if bool(privacy_status_data.get("pin_enabled", false)):
		reminders_form_private = not reminders_form_private
		return
	reminders_pending_private_after_pin = true
	reminders_pending_private_form_mode = reminders_mode
	reminders_status_text = "Set a 4-digit PIN to use private reminders."
	_open_privacy_pin_setup_from_reminders()

func _open_privacy_pin_setup_from_reminders() -> void:
	nav.previous_screen = "Reminders"
	nav.current_screen = "Settings"
	transition_active = false
	settings_current_page = "privacy"
	pin_mode = "set"
	pin_input = ""
	settings_status_text = "Set a 4-digit PIN to use private reminders."
	api.request_get("/api/privacy/status")
	_request_redraw()

func _reminders_apply_relative_minutes(minutes: int) -> void:
	var unix := Time.get_unix_time_from_system() + minutes * 60
	var due := Time.get_datetime_dict_from_unix_time(unix)
	reminders_form_date = "%04d-%02d-%02d" % [due.year, due.month, due.day]
	reminders_form_time = "%02d:%02d" % [due.hour, due.minute]

func _reminders_apply_relative_days(days: int) -> void:
	var unix := Time.get_unix_time_from_system() + days * 86400
	var due := Time.get_datetime_dict_from_unix_time(unix)
	reminders_form_date = "%04d-%02d-%02d" % [due.year, due.month, due.day]
	reminders_form_time = "%02d:%02d" % [due.hour, due.minute]

func _reminders_due_at_text() -> String:
	return reminders_form_date + "T" + reminders_form_time + ":00"

func _reminders_save_form() -> void:
	if reminders_form_title.strip_edges() == "":
		reminders_status_text = "Reminder text is required."
		return
	if not _reminders_date_valid(reminders_form_date) or not _reminders_time_valid(reminders_form_time):
		reminders_status_text = "Use YYYY-MM-DD and HH:MM."
		return
	var payload := {"title": reminders_form_title, "notes": reminders_form_notes, "due_at": _reminders_due_at_text(), "is_private": reminders_form_private}
	if reminders_mode == "edit":
		payload["id"] = reminders_selected_id
		api.request_post("/api/reminders/update", payload)
	else:
		api.request_post("/api/reminders/create", payload)

func _reminders_date_valid(value: String) -> bool:
	if value.length() != 10:
		return false
	if value.substr(4, 1) != "-" or value.substr(7, 1) != "-":
		return false
	for index in [0, 1, 2, 3, 5, 6, 8, 9]:
		if "0123456789".find(value.substr(index, 1)) < 0:
			return false
	return true

func _reminders_time_valid(value: String) -> bool:
	if value.length() != 5 or value.substr(2, 1) != ":":
		return false
	for index in [0, 1, 3, 4]:
		if "0123456789".find(value.substr(index, 1)) < 0:
			return false
	var hour := int(value.substr(0, 2))
	var minute := int(value.substr(3, 2))
	return hour >= 0 and hour <= 23 and minute >= 0 and minute <= 59

func _select_reminder(kind: String, index: int) -> void:
	var rows_raw = reminders_data.get(kind, [])
	if rows_raw is Array and index < rows_raw.size():
		reminders_selected_item = rows_raw[index] as Dictionary
		reminders_selected_id = int(reminders_selected_item.get("id", 0))
	_request_redraw()

func _study_page_id(title: String) -> String:
	return title.to_lower().replace(" ", "_")

func _open_study_page(page: String) -> void:
	study_current_page = page
	study_scroll_y = 0.0
	_request_study_page_data()
	_request_redraw()

func _handle_study_pomodoro_tap(position: Vector2) -> void:
	if Rect2(44, 118, 552, 38).has_point(position):
		_open_text_input("Pomodoro topic", study_topic_text, "study_topic", {})
	elif Rect2(44, 166, 120, 34).has_point(position):
		study_planned_minutes = max(5, study_planned_minutes - 5)
		_request_redraw()
	elif Rect2(176, 166, 120, 34).has_point(position):
		study_planned_minutes = min(240, study_planned_minutes + 5)
		_request_redraw()
	elif Rect2(308, 166, 120, 34).has_point(position):
		study_break_minutes = 0 if study_break_minutes != 0 else 5
		_request_redraw()
	elif Rect2(44, 216, 260, 42).has_point(position):
		if study_topic_text.strip_edges() == "":
			study_status_text = "Type a topic first"
		else:
			api.request_post("/api/study/pomodoro/start", {"topic": study_topic_text, "planned_minutes": study_planned_minutes, "break_minutes": study_break_minutes})
	elif Rect2(324, 216, 260, 42).has_point(position):
		api.request_post("/api/study/timer/stop")

func _handle_study_smart_tap(position: Vector2) -> void:
	if Rect2(44, 118, 350, 36).has_point(position):
		_open_text_input("Smart topic", study_topic_text, "study_topic", {})
	elif Rect2(44, 164, 350, 36).has_point(position):
		_open_text_input("Study goal", study_goal_text, "study_goal", {})
	elif Rect2(420, 118, 170, 32).has_point(position):
		if not study_segments.is_empty() and str((study_segments[study_segments.size() - 1] as Dictionary).get("type", "focus")) == "focus":
			study_status_text = "After focus, add a break."
			_request_redraw()
			return
		study_segments.append({"type": "focus", "minutes": 5})
		study_selected_segment_index = study_segments.size() - 1
	elif Rect2(420, 156, 170, 32).has_point(position):
		if not study_segments.is_empty() and str((study_segments[study_segments.size() - 1] as Dictionary).get("type", "focus")) == "break":
			study_status_text = "After break, add focus."
			_request_redraw()
			return
		study_segments.append({"type": "break", "minutes": 5})
		study_selected_segment_index = study_segments.size() - 1
	elif Rect2(420, 194, 170, 32).has_point(position) and study_segments.size() > 1:
		study_segments.remove_at(study_segments.size() - 1)
		study_selected_segment_index = mini(study_selected_segment_index, study_segments.size() - 1)
	elif Rect2(420, 232, 80, 32).has_point(position):
		_study_adjust_selected_segment(-5)
	elif Rect2(510, 232, 80, 32).has_point(position):
		_study_adjust_selected_segment(5)
	elif Rect2(420, 274, 170, 34).has_point(position) and not bool(study_timer_data.get("active", false)):
		var validation := _validate_study_segments()
		if validation != "":
			study_status_text = validation
		else:
			api.request_post("/api/study/smart/start", {"topic": study_topic_text, "goal": study_goal_text, "segments": study_segments})
	elif bool(study_timer_data.get("note_prompt_pending", false)) and Rect2(424, 334, 76, 30).has_point(position):
		_open_text_input("What did you learn?", study_note_text, "study_smart_note", {})
	elif bool(study_timer_data.get("note_prompt_pending", false)) and Rect2(510, 334, 76, 30).has_point(position):
		api.request_post("/api/study/smart/skip-note", {"session_id": study_active_smart_session_id})
	elif bool(study_timer_data.get("active", false)) and Rect2(424, 374, 76, 28).has_point(position):
		api.request_post("/api/study/smart/stop", {"session_id": study_active_smart_session_id})
	elif bool(study_timer_data.get("active", false)) and Rect2(510, 374, 76, 28).has_point(position):
		api.request_post("/api/study/smart/finish", {"session_id": study_active_smart_session_id})
	for index in range(study_segments.size()):
		var rect: Rect2 = _study_segment_row_rect(index)
		if rect.has_point(position):
			study_selected_segment_index = index
			_request_redraw()
			return

func _study_current_segment_is_break() -> bool:
	return bool(study_timer_data.get("active", false)) and str(study_timer_data.get("kind", "focus")) == "break"

func _study_current_segment_is_focus() -> bool:
	return bool(study_timer_data.get("active", false)) and str(study_timer_data.get("kind", "focus")) == "focus"

func _study_segment_row_rect(index: int) -> Rect2:
	return Rect2(56, 220 + float(index) * 30.0 - study_segment_scroll_y, 316, 24)

func _study_adjust_selected_segment(delta_minutes: int) -> void:
	if study_selected_segment_index < 0 or study_selected_segment_index >= study_segments.size():
		return
	var segment: Dictionary = study_segments[study_selected_segment_index] as Dictionary
	segment["minutes"] = max(5, int(segment.get("minutes", 5)) + delta_minutes)
	study_segments[study_selected_segment_index] = segment
	_request_redraw()

func _validate_study_segments() -> String:
	if study_topic_text.strip_edges() == "":
		return "Empty topic/title is invalid."
	if study_segments.is_empty():
		return "Add at least one focus segment."
	for index in range(study_segments.size()):
		var segment: Dictionary = study_segments[index] as Dictionary
		var kind := str(segment.get("type", "focus"))
		var minutes := int(segment.get("minutes", 0))
		if kind == "focus" and minutes < 5:
			return "Focus part cannot be shorter than 5 minutes."
		if kind == "break":
			if minutes < 5:
				return "Break cannot be shorter than 5 minutes."
			if index == 0 or index == study_segments.size() - 1:
				return "If there is a break, there must be focus before and after it."
		if index > 0:
			var previous: Dictionary = study_segments[index - 1] as Dictionary
			if str(previous.get("type", "focus")) == kind:
				return "Segments must alternate focus and break."
	return ""

func _handle_study_flashcards_tap(position: Vector2) -> void:
	if study_flashcard_delete_confirm_open:
		if Rect2(78, 354, 210, 42).has_point(position):
			study_flashcard_delete_confirm_open = false
			study_status_text = "Delete cancelled"
		elif Rect2(352, 354, 210, 42).has_point(position) and study_selected_deck_id > 0:
			study_flashcard_delete_confirm_open = false
			api.request_post("/api/study/settings/delete", {"action": "delete_deck", "target_id": study_selected_deck_id, "confirm_text": "DELETE_DECK"})
			study_selected_deck_id = 0
			study_flashcard_mode = "list"
		_request_redraw()
		return
	if Rect2(44, 118, 170, 38).has_point(position):
		_open_text_input("New Flashcards", "", "study_create_deck", {})
	elif Rect2(232, 118, 170, 38).has_point(position) and study_selected_deck_id <= 0:
		study_status_text = "Select one flashcard set first."
	elif Rect2(232, 118, 170, 38).has_point(position):
		_open_text_input("Card question", "", "study_card_question", {})
	elif Rect2(420, 118, 170, 38).has_point(position) and study_selected_deck_id <= 0:
		study_status_text = "Select one flashcard set first."
	elif Rect2(420, 118, 170, 38).has_point(position):
		study_flashcard_mode = "practice"
		study_flashcard_answer_text = ""
		study_flashcard_revealed_answer = false
		study_flashcard_answer_checked = false
		study_flashcard_feedback_text = ""
		api.request_get("/api/study/flashcards/review/start?deck_id=" + str(study_selected_deck_id) + "&mode=all")
	elif Rect2(44, 164, 170, 34).has_point(position) and study_selected_deck_id <= 0:
		study_status_text = "Select one flashcard set first."
	elif Rect2(44, 164, 170, 34).has_point(position):
		study_flashcard_delete_confirm_open = true
	elif Rect2(44, 278, 170, 30).has_point(position) and study_flashcard_mode == "practice" and study_selected_card.has("id"):
		_open_text_input("Your answer", study_flashcard_answer_text, "study_flashcard_answer_input", {})
	elif Rect2(232, 278, 170, 30).has_point(position) and study_flashcard_mode == "practice" and study_selected_card.has("id"):
		_check_flashcard_answer()
	elif Rect2(420, 278, 170, 30).has_point(position) and study_flashcard_mode == "practice" and study_selected_card.has("id"):
		study_flashcard_revealed_answer = true
		study_flashcard_answer_checked = true
		study_flashcard_feedback_text = "Answer: " + str(study_selected_card.get("answer", ""))
	elif Rect2(44, 316, 160, 30).has_point(position) and study_flashcard_mode == "practice" and study_selected_card.has("id"):
		_submit_flashcard_review("know")
	elif Rect2(220, 316, 160, 30).has_point(position) and study_flashcard_mode == "practice" and study_selected_card.has("id"):
		_submit_flashcard_review("unsure")
	elif Rect2(396, 316, 160, 30).has_point(position) and study_flashcard_mode == "practice" and study_selected_card.has("id"):
		_submit_flashcard_review("dont_know")
	elif Rect2(44, 354, 170, 30).has_point(position) and study_flashcard_mode == "practice" and study_selected_card.has("id"):
		study_flashcard_answer_checked = false
		study_flashcard_revealed_answer = false
		study_flashcard_answer_text = ""
		study_flashcard_feedback_text = ""
		api.request_get("/api/study/flashcards/review/next?deck_id=" + str(study_selected_deck_id))
	elif Rect2(232, 354, 170, 30).has_point(position) and study_flashcard_mode == "practice":
		study_flashcard_mode = "detail"
		study_selected_card = {}
		api.request_get("/api/study/flashcards/deck?deck_id=" + str(study_selected_deck_id))
	elif Rect2(44, 390, 170, 34).has_point(position) and study_flashcard_mode == "finished":
		study_flashcard_mode = "detail"
	elif Rect2(232, 390, 170, 34).has_point(position) and study_flashcard_mode == "finished":
		study_flashcard_mode = "practice"
		api.request_get("/api/study/flashcards/review/start?deck_id=" + str(study_selected_deck_id) + "&mode=all")
	for index in range(_study_list_count("decks")):
		var rect: Rect2 = _study_list_rect(index)
		if rect.has_point(position):
			var decks_raw: Array = study_data.get("decks", [])
			var item: Dictionary = decks_raw[index] as Dictionary
			study_selected_deck_id = int(item.get("id", 0))
			study_flashcard_mode = "detail"
			api.request_get("/api/study/flashcards/deck?deck_id=" + str(study_selected_deck_id))
			_request_redraw()
			return
	for index in range(_study_list_count("cards")):
		var card_rect: Rect2 = _study_list_rect(index)
		if card_rect.has_point(position):
			var cards_raw: Array = study_data.get("cards", [])
			study_selected_card = cards_raw[index] as Dictionary
			study_status_text = "Edit question / Delete question planned"
			_request_redraw()
			return

func _submit_flashcard_review(confidence: String) -> void:
	if not study_flashcard_answer_checked and not study_flashcard_revealed_answer:
		study_status_text = "Type your answer and check it, or reveal the card first."
		_request_redraw()
		return
	api.request_post("/api/study/flashcards/review", {"card_id": study_selected_card.get("id", 0), "typed_answer": study_flashcard_answer_text, "confidence": confidence, "revealed_answer": study_flashcard_revealed_answer})
	study_flashcard_answer_text = ""
	study_flashcard_revealed_answer = false
	study_flashcard_answer_checked = false

func _check_flashcard_answer() -> void:
	var typed := study_flashcard_answer_text.strip_edges().to_lower()
	var expected := str(study_selected_card.get("answer", "")).strip_edges().to_lower()
	study_flashcard_answer_checked = true
	if typed != "" and typed == expected:
		study_flashcard_feedback_text = "Correct"
	else:
		study_flashcard_revealed_answer = true
		study_flashcard_feedback_text = "Wrong. Correct answer: " + str(study_selected_card.get("answer", ""))
	_request_redraw()

func _check_language_answer() -> void:
	var typed := study_language_answer_text.strip_edges().to_lower()
	var expected := str(study_selected_word.get("meaning", "")).strip_edges().to_lower()
	study_language_answer_checked = true
	if typed != "" and typed == expected:
		study_language_feedback_text = "Correct"
		api.request_post("/api/study/languages/review", {"word_id": study_selected_word.get("id", 0), "result": "correct"})
	else:
		study_language_revealed_word = true
		study_language_feedback_text = "Wrong. Correct meaning: " + str(study_selected_word.get("meaning", ""))
		api.request_post("/api/study/languages/review", {"word_id": study_selected_word.get("id", 0), "result": "wrong"})
	_request_redraw()

func _handle_study_quizzes_tap(position: Vector2) -> void:
	if study_quiz_delete_confirm_open:
		if Rect2(78, 354, 210, 42).has_point(position):
			study_quiz_delete_confirm_open = false
			study_status_text = "Delete cancelled"
		elif Rect2(352, 354, 210, 42).has_point(position) and study_selected_quiz_id > 0:
			study_quiz_delete_confirm_open = false
			api.request_post("/api/study/settings/delete", {"action": "delete_quiz", "target_id": study_selected_quiz_id, "confirm_text": "DELETE_QUIZ"})
			study_selected_quiz_id = 0
			study_quiz_mode = "list"
		_request_redraw()
		return
	if Rect2(44, 118, 170, 38).has_point(position):
		_open_text_input("Quiz name", "", "study_create_quiz", {})
	elif Rect2(232, 118, 170, 38).has_point(position) and study_selected_quiz_id <= 0:
		study_status_text = "Select one quiz first."
	elif Rect2(232, 118, 170, 38).has_point(position):
		_open_text_input("Quiz question", "", "study_quiz_question", {})
	elif Rect2(420, 118, 170, 38).has_point(position) and study_selected_quiz_id <= 0:
		study_status_text = "Select one quiz first."
	elif Rect2(420, 118, 170, 38).has_point(position):
		study_quiz_mode = "play"
		study_quiz_answered = false
		study_quiz_feedback_text = ""
		api.request_get("/api/study/quizzes/question/next?quiz_id=" + str(study_selected_quiz_id))
	elif Rect2(44, 164, 170, 34).has_point(position) and study_pending_quiz_question == "" and study_selected_quiz_id <= 0:
		study_status_text = "Select one quiz first."
	elif Rect2(44, 164, 170, 34).has_point(position) and study_pending_quiz_question == "":
		study_quiz_delete_confirm_open = true
	elif Rect2(44, 174, 56, 32).has_point(position):
		study_pending_correct_answer = "A"
	elif Rect2(108, 174, 56, 32).has_point(position):
		study_pending_correct_answer = "B"
	elif Rect2(172, 174, 56, 32).has_point(position):
		study_pending_correct_answer = "C"
	elif Rect2(236, 174, 56, 32).has_point(position):
		study_pending_correct_answer = "D"
	elif Rect2(308, 174, 142, 32).has_point(position) and study_pending_quiz_question != "":
		api.request_post("/api/study/quizzes/questions/create", {"quiz_id": study_selected_quiz_id, "question": study_pending_quiz_question, "answer_a": study_pending_answer_a, "answer_b": study_pending_answer_b, "answer_c": study_pending_answer_c, "answer_d": study_pending_answer_d, "correct_answer": study_pending_correct_answer})
	elif Rect2(44, 238, 260, 32).has_point(position) and study_quiz_mode == "play" and study_selected_question.has("id"):
		_submit_quiz_answer("A")
	elif Rect2(324, 238, 260, 32).has_point(position) and study_quiz_mode == "play" and study_selected_question.has("id"):
		_submit_quiz_answer("B")
	elif Rect2(44, 276, 260, 32).has_point(position) and study_quiz_mode == "play" and study_selected_question.has("id"):
		_submit_quiz_answer("C")
	elif Rect2(324, 276, 260, 32).has_point(position) and study_quiz_mode == "play" and study_selected_question.has("id"):
		_submit_quiz_answer("D")
	elif Rect2(44, 354, 170, 30).has_point(position) and study_quiz_mode == "play" and study_selected_question.has("id"):
		api.request_post("/api/study/quizzes/mark-review", {"question_id": study_selected_question.get("id", 0)})
	elif Rect2(232, 354, 170, 30).has_point(position) and study_quiz_mode == "play" and study_quiz_answered:
		study_quiz_answered = false
		api.request_get("/api/study/quizzes/question/next?quiz_id=" + str(study_selected_quiz_id))
	elif Rect2(420, 354, 170, 30).has_point(position) and study_quiz_mode == "play":
		study_quiz_mode = "detail"
		study_selected_question = {}
		api.request_get("/api/study/quizzes/quiz?quiz_id=" + str(study_selected_quiz_id))
	elif Rect2(44, 390, 170, 30).has_point(position) and study_quiz_mode == "finished":
		study_quiz_mode = "detail"
	elif Rect2(232, 390, 170, 30).has_point(position) and study_quiz_mode == "finished":
		study_quiz_answered = false
		api.request_get("/api/study/quizzes/question/next?quiz_id=" + str(study_selected_quiz_id) + "&mode=wrong")
	elif Rect2(420, 390, 170, 30).has_point(position) and study_quiz_mode == "finished":
		study_quiz_answered = false
		api.request_get("/api/study/quizzes/question/next?quiz_id=" + str(study_selected_quiz_id) + "&mode=marked")
	for index in range(_study_list_count("quizzes")):
		var rect: Rect2 = _study_list_rect(index)
		if rect.has_point(position):
			var quizzes_raw: Array = study_data.get("quizzes", [])
			var item: Dictionary = quizzes_raw[index] as Dictionary
			study_selected_quiz_id = int(item.get("id", 0))
			study_quiz_mode = "detail"
			api.request_get("/api/study/quizzes/quiz?quiz_id=" + str(study_selected_quiz_id))
			_request_redraw()
			return
	for index in range(_study_list_count("questions")):
		var question_rect: Rect2 = _study_list_rect(index)
		if question_rect.has_point(position):
			var questions_raw: Array = study_data.get("questions", [])
			study_selected_question = questions_raw[index] as Dictionary
			study_status_text = "Edit question / Delete question planned"
			_request_redraw()
			return

func _submit_quiz_answer(choice: String) -> void:
	api.request_post("/api/study/quizzes/answer", {"question_id": study_selected_question.get("id", 0), "answer": choice})
	study_quiz_answered = true

func _handle_study_languages_tap(position: Vector2) -> void:
	if study_language_delete_confirm_open:
		if Rect2(78, 354, 210, 42).has_point(position):
			study_language_delete_confirm_open = false
			study_status_text = "Delete cancelled"
		elif Rect2(352, 354, 210, 42).has_point(position) and study_selected_language_list_id > 0:
			study_language_delete_confirm_open = false
			api.request_post("/api/study/settings/delete", {"action": "delete_language_list", "target_id": study_selected_language_list_id, "confirm_text": "DELETE_LANGUAGE_LIST"})
			study_selected_language_list_id = 0
			study_language_mode = "list"
		_request_redraw()
		return
	if Rect2(44, 118, 170, 38).has_point(position):
		_open_text_input("Word list name", "", "study_create_language_list", {})
	elif Rect2(232, 118, 170, 38).has_point(position) and study_selected_language_list_id <= 0:
		study_status_text = "Select one language list first."
	elif Rect2(232, 118, 170, 38).has_point(position):
		_open_text_input("Word", "", "study_language_word", {})
	elif Rect2(420, 118, 170, 38).has_point(position) and study_selected_language_list_id <= 0:
		study_status_text = "Select one language list first."
	elif Rect2(420, 118, 170, 38).has_point(position):
		study_language_mode = "edit"
		api.request_get("/api/study/languages/list?list_id=" + str(study_selected_language_list_id))
	elif Rect2(44, 164, 170, 34).has_point(position) and study_selected_language_list_id <= 0:
		study_status_text = "Select one language list first."
	elif Rect2(44, 164, 170, 34).has_point(position):
		study_language_mode = "practice"
		study_language_answer_text = ""
		study_language_answer_checked = false
		study_language_revealed_word = false
		study_language_feedback_text = ""
		api.request_get("/api/study/languages/practice/next?list_id=" + str(study_selected_language_list_id))
	elif Rect2(232, 164, 170, 34).has_point(position) and study_selected_language_list_id <= 0:
		study_status_text = "Select one language list first."
	elif Rect2(232, 164, 170, 34).has_point(position):
		study_language_delete_confirm_open = true
	elif Rect2(44, 278, 170, 30).has_point(position) and study_language_mode == "practice" and study_selected_word.has("id"):
		_open_text_input("Meaning", study_language_answer_text, "study_language_answer_input", {})
	elif Rect2(232, 278, 170, 30).has_point(position) and study_language_mode == "practice" and study_selected_word.has("id"):
		_check_language_answer()
	elif Rect2(420, 278, 170, 30).has_point(position) and study_language_mode == "practice" and study_selected_word.has("id"):
		study_language_revealed_word = true
		study_language_answer_checked = true
		study_language_feedback_text = "Correct meaning: " + str(study_selected_word.get("meaning", ""))
	elif Rect2(44, 316, 170, 30).has_point(position) and study_language_mode == "practice" and study_selected_word.has("id"):
		api.request_post("/api/study/languages/review", {"word_id": study_selected_word.get("id", 0), "result": "correct"})
		study_language_feedback_text = "Correct"
	elif Rect2(232, 316, 170, 30).has_point(position) and study_language_mode == "practice" and study_selected_word.has("id"):
		api.request_post("/api/study/languages/review", {"word_id": study_selected_word.get("id", 0), "result": "wrong"})
		study_language_feedback_text = "Wrong. Correct meaning: " + str(study_selected_word.get("meaning", ""))
	elif Rect2(44, 354, 170, 30).has_point(position) and study_language_mode == "practice":
		study_language_answer_text = ""
		study_language_answer_checked = false
		study_language_revealed_word = false
		api.request_get("/api/study/languages/practice/next?list_id=" + str(study_selected_language_list_id))
	elif Rect2(232, 354, 170, 30).has_point(position) and study_language_mode == "practice":
		study_language_mode = "list"
		api.request_get("/api/study/languages/lists")
	elif Rect2(44, 390, 170, 30).has_point(position) and study_language_mode == "finished":
		study_language_mode = "list"
		api.request_get("/api/study/languages/lists")
	elif Rect2(44, 390, 170, 30).has_point(position) and study_language_mode == "edit":
		_open_text_input("Word", "", "study_language_word", {})
	elif Rect2(232, 390, 170, 30).has_point(position) and study_language_mode == "edit" and study_selected_language_word_id > 0:
		api.request_post("/api/study/languages/words/delete", {"word_id": study_selected_language_word_id})
	elif Rect2(420, 390, 170, 30).has_point(position) and study_language_mode == "edit":
		study_language_mode = "list"
		api.request_get("/api/study/languages/lists")
	for index in range(_study_list_count("lists")):
		var rect: Rect2 = _study_list_rect(index)
		if rect.has_point(position):
			var lists_raw: Array = study_data.get("lists", [])
			var item: Dictionary = lists_raw[index] as Dictionary
			study_selected_language_list_id = int(item.get("id", 0))
			study_language_mode = "list"
			_request_redraw()
			return
	for index in range(_study_list_count("words")):
		var word_rect: Rect2 = _study_list_rect(index)
		if word_rect.has_point(position):
			var words_raw: Array = study_data.get("words", [])
			var word_item: Dictionary = words_raw[index] as Dictionary
			study_selected_language_word_id = int(word_item.get("id", 0))
			study_selected_word = word_item
			_request_redraw()
			return

func _handle_study_settings_tap(position: Vector2) -> void:
	if study_delete_confirm_open:
		if Rect2(78, 354, 210, 42).has_point(position):
			study_delete_confirm_open = false
			study_status_text = "Delete cancelled"
		elif Rect2(352, 354, 210, 42).has_point(position):
			study_delete_confirm_open = false
			api.request_post("/api/study/settings/delete", {"action": "delete_all_study_data", "confirm_text": "DELETE_STUDY_DATA"})
		_request_redraw()
		return
	if Rect2(44, 390, 260, 42).has_point(position):
		study_delete_confirm_open = true
		study_status_text = "Confirm delete to continue"
	elif Rect2(324, 390, 260, 42).has_point(position):
		study_status_text = "Use Delete all first"

func _study_list_count(key: String) -> int:
	var raw = study_data.get(key, [])
	if raw is Array:
		return raw.size()
	return 0

func _handle_pin_tap(position: Vector2) -> void:
	if Rect2(44, 114 - settings_scroll_y, 264, 38).has_point(position):
		pin_mode = "set"
		pin_input = ""
		_request_redraw()
		return
	if Rect2(332, 114 - settings_scroll_y, 264, 38).has_point(position):
		pin_mode = "verify"
		pin_input = ""
		_request_redraw()
		return
	if Rect2(44, 470 - settings_scroll_y, 264, 38).has_point(position):
		api.request_post("/api/privacy/lock")
		pin_input = ""
		return
	for index in range(12):
		var col: int = index % 3
		var row: int = int(index / 3)
		var rect: Rect2 = Rect2(178.0 + float(col) * 74.0, 292.0 + float(row) * 42.0 - settings_scroll_y, 62.0, 34.0)
		if rect.has_point(position):
			if index < 9:
				_pin_add(str(index + 1))
			elif index == 9:
				pin_input = ""
			elif index == 10:
				_pin_add("0")
			else:
				_pin_submit()
			_request_redraw()
			return

func _pin_add(value: String) -> void:
	if pin_input.length() < 4:
		pin_input += value

func _pin_submit() -> void:
	if pin_input.length() != 4:
		return
	if pin_mode == "set":
		api.request_post("/api/privacy/pin/set", {"pin": pin_input})
	else:
		api.request_post("/api/privacy/pin/verify", {"pin": pin_input})
	pin_input = ""

func _open_text_input(title: String, value: String, target: String, context: Dictionary) -> void:
	text_input_open = true
	text_input_title = title
	text_input_value = value
	text_input_target = target
	text_input_context = context
	text_input_keyboard_mode = str(context.get("keyboard_mode", "text"))
	_request_redraw()

func _close_text_input() -> void:
	text_input_open = false
	text_input_title = ""
	text_input_value = ""
	text_input_target = ""
	text_input_context = {}
	text_input_keyboard_mode = "text"

func _text_input_keys() -> String:
	if text_input_keyboard_mode == "datetime":
		if text_input_target == "reminder_time" or text_input_target == "calendar_time" or text_input_target == "todo_time":
			return "0123456789:"
		return "0123456789-"
	if text_input_keyboard_mode == "number":
		return "0123456789"
	return "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.,?!-/:"

func _text_input_char_allowed(value: String) -> bool:
	if text_input_keyboard_mode == "text":
		return true
	return _text_input_keys().find(value) >= 0

func _handle_text_input_tap(position: Vector2) -> void:
	if Rect2(412, 386, 82, 34).has_point(position):
		_commit_text_input()
		return
	if Rect2(504, 386, 82, 34).has_point(position):
		_close_text_input()
		_request_redraw()
		return
	if Rect2(40, 386, 96, 34).has_point(position) and text_input_keyboard_mode == "text":
		text_input_value += " "
		_request_redraw()
		return
	if Rect2(146, 386, 96, 34).has_point(position):
		if text_input_value.length() > 0:
			text_input_value = text_input_value.substr(0, text_input_value.length() - 1)
		_request_redraw()
		return
	if Rect2(252, 386, 96, 34).has_point(position):
		text_input_value = ""
		_request_redraw()
		return
	var keys := _text_input_keys()
	for index in range(keys.length()):
		var rect: Rect2 = _text_key_rect(index)
		if rect.has_point(position):
			text_input_value += keys.substr(index, 1)
			_request_redraw()
			return

func _commit_text_input() -> void:
	var value: String = text_input_value.strip_edges()
	var target := text_input_target
	var context := text_input_context.duplicate()
	_close_text_input()
	if target == "study_topic":
		study_topic_text = value
	elif target == "study_goal":
		study_goal_text = value
	elif target == "study_smart_note":
		study_note_text = value
		api.request_post("/api/study/smart/note", {"session_id": study_active_smart_session_id, "note_text": value})
	elif target == "study_create_deck":
		api.request_post("/api/study/flashcards/decks/create", {"name": value})
	elif target == "study_card_question":
		study_pending_question = value
		_open_text_input("Card answer", "", "study_card_answer", {})
	elif target == "study_card_answer":
		study_pending_answer = value
		api.request_post("/api/study/flashcards/cards/create", {"deck_id": study_selected_deck_id, "question": study_pending_question, "answer": study_pending_answer})
	elif target == "study_flashcard_answer_input":
		study_flashcard_answer_text = value
	elif target == "study_language_answer_input":
		study_language_answer_text = value
	elif target == "study_create_quiz":
		api.request_post("/api/study/quizzes/create", {"name": value})
	elif target == "study_quiz_question":
		study_pending_quiz_question = value
		_open_text_input("Answer A", "", "study_quiz_answer_a", {})
	elif target == "study_quiz_answer_a":
		study_pending_answer_a = value
		_open_text_input("Answer B", "", "study_quiz_answer_b", {})
	elif target == "study_quiz_answer_b":
		study_pending_answer_b = value
		_open_text_input("Answer C", "", "study_quiz_answer_c", {})
	elif target == "study_quiz_answer_c":
		study_pending_answer_c = value
		_open_text_input("Answer D", "", "study_quiz_answer_d", {})
	elif target == "study_quiz_answer_d":
		study_pending_answer_d = value
		study_status_text = "Choose correct answer A/B/C/D, then Save question"
	elif target == "study_create_language_list":
		api.request_post("/api/study/languages/lists/create", {"name": value, "language": "English"})
	elif target == "study_language_word":
		study_pending_language_word = value
		_open_text_input("Pronunciation", "", "study_language_pronunciation", {})
	elif target == "study_language_pronunciation":
		study_pending_language_pronunciation = value
		_open_text_input("Meaning", "", "study_language_meaning", {})
	elif target == "study_language_meaning":
		api.request_post("/api/study/languages/words/create", {"list_id": study_selected_language_list_id, "word": study_pending_language_word, "pronunciation": study_pending_language_pronunciation, "meaning": value})
	elif target == "reminder_title":
		reminders_form_title = value
	elif target == "reminder_notes":
		reminders_form_notes = value
	elif target == "reminder_date":
		reminders_form_date = value
	elif target == "reminder_time":
		reminders_form_time = value
	elif target == "calendar_title":
		calendar_form_title = value
	elif target == "calendar_description":
		calendar_form_description = value
	elif target == "calendar_date":
		calendar_form_date = value
	elif target == "calendar_time":
		calendar_form_time = value
	elif target == "todo_list_name":
		todo_list_form_name = value
	elif target == "todo_list_emoji":
		todo_list_form_emoji = value
	elif target == "todo_title":
		todo_form_title = value
	elif target == "todo_notes":
		todo_form_notes = value
	elif target == "todo_date":
		todo_form_date = value
	elif target == "todo_time":
		todo_form_time = value
	elif target.begins_with("settings_user_"):
		var section := str(context.get("section", "user"))
		var key := str(context.get("key", target.replace("settings_user_", "")))
		_settings_update(section, key, value.substr(0, 40))
	_request_redraw()

func _settings_update(section: String, key: String, value) -> void:
	var section_data = settings_data.get(section, {})
	if not (section_data is Dictionary):
		section_data = {}
	section_data[key] = value
	settings_data[section] = section_data
	settings_status_text = "Saving"
	api.request_post("/api/settings/update", {"section": section, "key": key, "value": value})
	_request_redraw()

func _settings_update_many(updates: Array) -> void:
	for update_raw in updates:
		var update: Dictionary = update_raw as Dictionary
		var section: String = str(update.get("section", ""))
		var key: String = str(update.get("key", ""))
		var value = update.get("value")
		var section_data = settings_data.get(section, {})
		if not (section_data is Dictionary):
			section_data = {}
		section_data[key] = value
		settings_data[section] = section_data
	settings_status_text = "Saving"
	api.request_post("/api/settings/update-many", {"updates": updates})
	_request_redraw()

func _apply_settings_row(row: Dictionary) -> void:
	var section: String = str(row.get("section", ""))
	var key: String = str(row.get("key", ""))
	var kind: String = str(row.get("kind", "toggle"))
	if section == "" or key == "":
		if str(row.get("action", "")) == "report":
			api.request_post("/api/reports/generate")
		elif str(row.get("action", "")) == "benchmark":
			api.request_post("/api/benchmarks/run")
		elif str(row.get("action", "")) == "user_save":
			settings_status_text = "User profile saved."
			api.request_post("/api/settings/update-many", {"updates": [
				{"section": "user", "key": "first_name", "value": str(_settings_value("user", "first_name", ""))},
				{"section": "user", "key": "last_name", "value": str(_settings_value("user", "last_name", ""))},
				{"section": "user", "key": "preferred_name", "value": str(_settings_value("user", "preferred_name", ""))}
			]})
		_request_redraw()
		return
	var current = _settings_value(section, key, row.get("default"))
	if row.has("set_value"):
		_settings_update(section, key, row.get("set_value"))
	elif kind == "text":
		_open_text_input(str(row.get("title", "Setting")), str(current), "settings_user_" + key, {"section": section, "key": key})
	elif kind == "toggle":
		_settings_update(section, key, not bool(current))
	elif kind == "number":
		var next_value: int = int(current) + int(row.get("step", 10))
		var min_value: int = int(row.get("min", 0))
		var max_value: int = int(row.get("max", 100))
		if next_value > max_value:
			next_value = min_value
		_settings_update(section, key, next_value)
	elif settings_current_page == "appearance" and kind == "choice":
		var appearance_options_raw = row.get("options", [])
		var appearance_options: Array = []
		if appearance_options_raw is Array:
			appearance_options = appearance_options_raw
		_open_settings_dropdown(section, key, appearance_options)
	else:
		var options_raw = row.get("options", [])
		var options: Array = []
		if options_raw is Array:
			options = options_raw
		_settings_update(section, key, _cycle_value(str(current), options))
	if section == "modes" and key == "current_mode" and str(_settings_value(section, key, "")) == "Away":
		api.request_post("/api/privacy/lock")

func _open_settings_dropdown(section: String, key: String, options: Array) -> void:
	settings_dropdown_open = true
	settings_dropdown_section = section
	settings_dropdown_key = key
	settings_dropdown_options = options.duplicate()
	_request_redraw()

func _close_settings_dropdown() -> void:
	settings_dropdown_open = false
	settings_dropdown_section = ""
	settings_dropdown_key = ""
	settings_dropdown_options = []

func _handle_settings_dropdown_tap(position: Vector2) -> void:
	var panel: Rect2 = _settings_dropdown_rect()
	if not panel.has_point(position):
		_close_settings_dropdown()
		_request_redraw()
		return
	for index in range(settings_dropdown_options.size()):
		var rect: Rect2 = _settings_dropdown_option_rect(index)
		if rect.has_point(position):
			var value: String = str(settings_dropdown_options[index])
			_apply_settings_choice(settings_dropdown_section, settings_dropdown_key, value)
			_close_settings_dropdown()
			return

func _apply_settings_choice(section: String, key: String, value: String) -> void:
	if section == "appearance" and key == "preset":
		_apply_appearance_preset(value)
	elif section == "appearance" and key == "time_color":
		_settings_update_many([
			{"section": "appearance", "key": "time_color", "value": value},
			{"section": "appearance", "key": "hour_color", "value": value},
			{"section": "appearance", "key": "minute_color", "value": value},
			{"section": "appearance", "key": "second_color", "value": value}
		])
	elif section == "appearance" and key == "date_color":
		_settings_update_many([
			{"section": "appearance", "key": "date_color", "value": value},
			{"section": "appearance", "key": "day_color", "value": value},
			{"section": "appearance", "key": "month_color", "value": value},
			{"section": "appearance", "key": "year_color", "value": value}
		])
	else:
		_settings_update(section, key, value)

func _apply_appearance_preset(preset_name: String) -> void:
	var preset: Dictionary = _appearance_preset_values(preset_name)
	var updates: Array = [{"section": "appearance", "key": "preset", "value": preset_name}]
	for key in ["eye_color", "mouth_color", "tile_accent_color", "background_color", "led_color", "time_color", "hour_color", "minute_color", "second_color", "date_color", "day_color", "month_color", "year_color"]:
		updates.append({"section": "appearance", "key": key, "value": preset.get(key, "Blue")})
	_settings_update_many(updates)

func _appearance_preset_values(preset_name: String) -> Dictionary:
	var presets: Dictionary = {
		"NeXa Blue": {"eye_color": "Blue", "mouth_color": "Blue", "tile_accent_color": "Blue", "background_color": "Black", "led_color": "Blue", "time_color": "White", "hour_color": "White", "minute_color": "White", "second_color": "Blue", "date_color": "Grey", "day_color": "Grey", "month_color": "Grey", "year_color": "Grey"},
		"Apple Dark": {"eye_color": "White", "mouth_color": "White", "tile_accent_color": "Graphite", "background_color": "Black", "led_color": "White", "time_color": "White", "hour_color": "White", "minute_color": "White", "second_color": "Grey", "date_color": "Grey", "day_color": "Grey", "month_color": "Grey", "year_color": "Grey"},
		"Warm Desk": {"eye_color": "Warm White", "mouth_color": "Warm White", "tile_accent_color": "Gold", "background_color": "Brown", "led_color": "Warm White", "time_color": "Warm White", "hour_color": "Warm White", "minute_color": "Warm White", "second_color": "Gold", "date_color": "Warm White", "day_color": "Warm White", "month_color": "Warm White", "year_color": "Warm White"},
		"Focus Green": {"eye_color": "Green", "mouth_color": "Green", "tile_accent_color": "Green", "background_color": "Graphite", "led_color": "Green", "time_color": "White", "hour_color": "White", "minute_color": "White", "second_color": "Green", "date_color": "Green", "day_color": "Green", "month_color": "Green", "year_color": "Green"},
		"Night Red": {"eye_color": "Red", "mouth_color": "Red", "tile_accent_color": "Red", "background_color": "Black", "led_color": "Red", "time_color": "Red", "hour_color": "Red", "minute_color": "Red", "second_color": "Red", "date_color": "Red", "day_color": "Red", "month_color": "Red", "year_color": "Red"},
		"Soft Pink": {"eye_color": "Pink", "mouth_color": "Pink", "tile_accent_color": "Pink", "background_color": "Graphite", "led_color": "Pink", "time_color": "White", "hour_color": "White", "minute_color": "White", "second_color": "Pink", "date_color": "Pink", "day_color": "Pink", "month_color": "Pink", "year_color": "Pink"},
		"Minimal White": {"eye_color": "White", "mouth_color": "White", "tile_accent_color": "White", "background_color": "Black", "led_color": "White", "time_color": "White", "hour_color": "White", "minute_color": "White", "second_color": "Grey", "date_color": "White", "day_color": "White", "month_color": "White", "year_color": "White"}
	}
	var value = presets.get(preset_name, presets["NeXa Blue"])
	if value is Dictionary:
		return value
	return presets["NeXa Blue"]

func _settings_value(section: String, key: String, fallback):
	var section_data = settings_data.get(section, {})
	if section_data is Dictionary:
		return section_data.get(key, fallback)
	return fallback

func _cycle_value(current: String, options: Array) -> String:
	if options.is_empty():
		return current
	var index: int = options.find(current)
	if index < 0:
		return str(options[0])
	return str(options[(index + 1) % options.size()])

func _settings_enabled_quick_shelf() -> Array:
	var quick_raw = _settings_value("quick_shelf", "enabled_tiles", [])
	if quick_raw is Array:
		return quick_raw.duplicate()
	return []

func _settings_rows_for_page(page: String) -> Array:
	if page == "appearance":
		return [
			{"title": "Preset", "section": "appearance", "key": "preset", "kind": "choice", "options": PRESET_OPTIONS, "default": "NeXa Blue"},
			{"title": "Eye color", "section": "appearance", "key": "eye_color", "kind": "choice", "options": COLOR_OPTIONS, "default": "Blue"},
			{"title": "Mouth color", "section": "appearance", "key": "mouth_color", "kind": "choice", "options": COLOR_OPTIONS, "default": "Blue"},
			{"title": "Tile accent", "section": "appearance", "key": "tile_accent_color", "kind": "choice", "options": COLOR_OPTIONS, "default": "Blue"},
			{"title": "Background", "section": "appearance", "key": "background_color", "kind": "choice", "options": COLOR_OPTIONS, "default": "Black"},
			{"title": "LED color", "section": "appearance", "key": "led_color", "kind": "choice", "options": COLOR_OPTIONS, "default": "Blue"},
			{"title": "Time color", "section": "appearance", "key": "time_color", "kind": "choice", "options": COLOR_OPTIONS, "default": "White"},
			{"title": "Hour color", "section": "appearance", "key": "hour_color", "kind": "choice", "options": COLOR_OPTIONS, "default": "White"},
			{"title": "Minute color", "section": "appearance", "key": "minute_color", "kind": "choice", "options": COLOR_OPTIONS, "default": "White"},
			{"title": "Second color", "section": "appearance", "key": "second_color", "kind": "choice", "options": COLOR_OPTIONS, "default": "Grey"},
			{"title": "Date color", "section": "appearance", "key": "date_color", "kind": "choice", "options": COLOR_OPTIONS, "default": "Grey"},
			{"title": "Day color", "section": "appearance", "key": "day_color", "kind": "choice", "options": COLOR_OPTIONS, "default": "Grey"},
			{"title": "Month color", "section": "appearance", "key": "month_color", "kind": "choice", "options": COLOR_OPTIONS, "default": "Grey"},
			{"title": "Year color", "section": "appearance", "key": "year_color", "kind": "choice", "options": COLOR_OPTIONS, "default": "Grey"}
		]
	if page == "user":
		return [
			{"title": "First name", "section": "user", "key": "first_name", "kind": "text", "default": ""},
			{"title": "Last name", "section": "user", "key": "last_name", "kind": "text", "default": ""},
			{"title": "How should NeXa call you?", "section": "user", "key": "preferred_name", "kind": "text", "default": ""},
			{"title": "Save", "action": "user_save", "subtitle": "User profile saved."}
		]
	if page == "notifications":
		return [
			{"title": "Style", "section": "notifications", "key": "style", "kind": "choice", "options": ["Banner", "Icon only", "Control Center only", "Silent", "LED only", "Face only"], "default": "Banner"},
			{"title": "Show on Face Home", "section": "notifications", "key": "show_on_face_home", "kind": "toggle", "default": true},
			{"title": "Icon only", "section": "notifications", "key": "icon_only", "kind": "toggle", "default": false},
			{"title": "Control Center only", "section": "notifications", "key": "control_center_only", "kind": "toggle", "default": false},
			{"title": "Use sound", "section": "notifications", "key": "use_sound", "kind": "toggle", "default": true},
			{"title": "Use LED", "section": "notifications", "key": "use_led", "kind": "toggle", "default": true},
			{"title": "Face expression", "section": "notifications", "key": "use_face_expression", "kind": "toggle", "default": true},
			{"title": "Use behaviour", "section": "notifications", "key": "use_behaviour", "kind": "toggle", "default": true},
			{"title": "Private notifications", "section": "notifications", "key": "private_notifications_enabled", "kind": "toggle", "default": false},
			{"title": "Private reminders", "section": "notifications", "key": "private_reminders_enabled", "kind": "toggle", "default": false}
		]
	if page == "modes":
		var rows: Array = []
		for mode_name in MODE_OPTIONS:
			rows.append({"title": str(mode_name), "section": "modes", "key": "current_mode", "kind": "choice", "options": MODE_OPTIONS, "default": "Normal", "set_value": str(mode_name), "subtitle": _mode_description(str(mode_name))})
		return rows
	if page == "display":
		return [
			{"title": "Brightness", "section": "display", "key": "brightness_percent", "kind": "number", "default": 65, "step": 10},
			{"title": "Auto brightness", "section": "display", "key": "auto_brightness", "kind": "toggle", "default": false},
			{"title": "Clock on Face", "section": "display", "key": "show_clock_on_face", "kind": "toggle", "default": true},
			{"title": "Date on Face", "section": "display", "key": "show_date_on_face", "kind": "toggle", "default": false},
			{"title": "Text size", "section": "display", "key": "text_size", "kind": "choice", "options": ["Small", "Normal", "Large"], "default": "Normal"},
			{"title": "Reduce motion", "section": "display", "key": "reduce_motion", "kind": "toggle", "default": false},
			{"title": "Screen timeout", "section": "display", "key": "screen_timeout", "kind": "choice", "options": ["planned"], "default": "planned"}
		]
	if page == "sound":
		return [
			{"title": "Volume", "section": "sound", "key": "volume_percent", "kind": "number", "default": 50, "step": 10},
			{"title": "Mute", "section": "sound", "key": "muted", "kind": "toggle", "default": false},
			{"title": "Sound theme", "section": "sound", "key": "sound_theme", "kind": "choice", "options": ["Soft", "Cute", "Minimal", "Sci-fi", "Silent"], "default": "Soft"},
			{"title": "Button sound", "section": "sound", "key": "button_sound", "kind": "toggle", "default": true},
			{"title": "Notification sound", "section": "sound", "key": "notification_sound", "kind": "toggle", "default": true},
			{"title": "Error sound", "section": "sound", "key": "error_sound", "kind": "toggle", "default": true},
			{"title": "Quiet hours", "section": "sound", "key": "quiet_hours", "kind": "choice", "options": ["planned"], "default": "planned"}
		]
	if page == "network":
		return [
			{"title": "Current Wi-Fi", "section": "network", "key": "wifi_connect_actions", "kind": "choice", "options": ["dry_run_planned"], "default": "dry_run_planned"},
			{"title": "Connect planned", "section": "network", "key": "wifi_connect_actions", "kind": "choice", "options": ["dry_run_planned"], "default": "dry_run_planned"},
			{"title": "Remote Wi-Fi", "section": "network", "key": "remote_wifi_enabled", "kind": "toggle", "default": false},
			{"title": "Web panel", "section": "network", "key": "wifi_connect_actions", "kind": "choice", "options": ["dry_run_planned"], "default": "dry_run_planned"}
		]
	if page == "remote":
		return [
			{"title": "Controller", "section": "remote", "key": "controller_enabled", "kind": "toggle", "default": true},
			{"title": "Remote Wi-Fi", "section": "network", "key": "remote_wifi_enabled", "kind": "toggle", "default": false},
			{"title": "Pair remote", "section": "remote", "key": "controller_enabled", "kind": "toggle", "default": true},
			{"title": "Vibration", "section": "remote", "key": "vibration_enabled", "kind": "toggle", "default": false}
		]
	if page == "diagnostics":
		return [
			{"title": "Collect logs", "section": "diagnostics", "key": "collect_logs", "kind": "toggle", "default": true},
			{"title": "Log level", "section": "diagnostics", "key": "log_level", "kind": "choice", "options": ["Normal", "Detailed", "Debug"], "default": "Normal"},
			{"title": "Generate report", "action": "report"},
			{"title": "Run system check", "action": "benchmark"},
			{"title": "Run audio check", "action": "benchmark"},
			{"title": "Run camera check", "action": "benchmark"},
			{"title": "Clear logs", "section": "diagnostics", "key": "log_level", "kind": "choice", "options": ["Normal"], "default": "Normal"}
		]
	if page == "safety" or page == "exit_nexa":
		return [
			{"title": "Exit NeXa", "section": "safety", "key": "confirm_exit", "kind": "toggle", "default": true, "subtitle": "Exit UI planned"},
			{"title": "Restart UI", "section": "safety", "key": "confirm_exit", "kind": "toggle", "default": true, "subtitle": "Planned"},
			{"title": "Restart API", "section": "safety", "key": "confirm_exit", "kind": "toggle", "default": true, "subtitle": "Planned"},
			{"title": "Reboot Raspberry Pi", "section": "safety", "key": "confirm_power_actions", "kind": "toggle", "default": true, "subtitle": "Planned only"},
			{"title": "Power off Raspberry Pi", "section": "safety", "key": "confirm_power_actions", "kind": "toggle", "default": true, "subtitle": "Planned only"}
		]
	if page == "about":
		return [
			{"title": "NeXa ToTem", "section": "modes", "key": "current_mode", "kind": "choice", "options": MODE_OPTIONS, "default": "Normal", "subtitle": "Smart Desk Companion"},
			{"title": "Version", "section": "modes", "key": "current_mode", "kind": "choice", "options": MODE_OPTIONS, "default": "Normal", "subtitle": "Prototype"}
		]
	return []

func _mode_description(mode_name: String) -> String:
	if mode_name == "Quiet":
		return "no distractions"
	if mode_name == "Focus":
		return "study/work mode"
	if mode_name == "Night":
		return "dim and silent"
	if mode_name == "Away":
		return "lock private content"
	if mode_name == "Demo":
		return "show product features"
	if mode_name == "Maintenance":
		return "diagnostics and testing"
	return "full behaviour"

func _handle_diagnostics_action_tap(position: Vector2) -> void:
	if active_tab == "Benchmarks" and Rect2(416, 154, 154, 34).has_point(position):
		api.request_post("/api/benchmarks/run")
	elif active_tab == "Reports" and Rect2(416, 154, 154, 34).has_point(position):
		api.request_post("/api/reports/generate")
	elif active_tab == "Logs" and Rect2(416, 154, 154, 34).has_point(position):
		api.request_get("/api/logs")
	elif active_tab == "Camera" and Rect2(350, 316 - diagnostic_scroll_y, 190, 34).has_point(position):
		if camera_preview_on:
			_stop_camera_preview()
		else:
			camera_preview_on = true
			camera_preview_status = "Starting"
			api.request_post("/api/camera/preview/start")
	elif active_tab == "Camera" and Rect2(350, 356 - diagnostic_scroll_y, 190, 34).has_point(position):
		api.request_post("/api/camera/check/run")
	elif active_tab == "Audio" and Rect2(416, 154, 154, 34).has_point(position):
		api.request_post("/api/audio/check/run")

func _brightness_slider_rect() -> Rect2:
	return Rect2(58, 174, 132, 12)

func _sound_slider_rect() -> Rect2:
	return Rect2(242, 174, 132, 12)

func _begin_slider_drag(position: Vector2) -> bool:
	if nav.current_screen != "Notification Control Center":
		return false
	if _brightness_slider_rect().has_point(position):
		slider_drag_active = true
		slider_drag_kind = "brightness"
		selected_control_detail = "brightness"
		_update_slider_drag(position)
		return true
	if _sound_slider_rect().has_point(position):
		slider_drag_active = true
		slider_drag_kind = "sound"
		selected_control_detail = "sound"
		_update_slider_drag(position)
		return true
	return false

func _update_slider_drag(position: Vector2) -> void:
	var rect: Rect2 = _brightness_slider_rect() if slider_drag_kind == "brightness" else _sound_slider_rect()
	var value: int = int(round(clampf((position.x - rect.position.x) / rect.size.x, 0.0, 1.0) * 100.0))
	if slider_drag_kind == "brightness":
		brightness_percent = value
		control_center_data["brightness_percent"] = brightness_percent
	elif slider_drag_kind == "sound":
		sound_percent = value
		control_center_data["sound_percent"] = sound_percent
	_request_redraw()

func _finish_slider_drag() -> void:
	if slider_drag_kind == "brightness":
		api.request_post("/api/control/brightness", {"brightness_percent": brightness_percent, "auto_brightness": bool(control_center_data.get("brightness_auto", false))})
	elif slider_drag_kind == "sound":
		api.request_post("/api/control/sound", {"sound_percent": sound_percent, "muted": bool(control_center_data.get("muted", false))})
	slider_drag_active = false
	slider_drag_kind = ""

func _begin_scroll_drag(position: Vector2) -> bool:
	if nav.current_screen == "Face Home" and home_message_active and _home_message_text_rect().has_point(position) and _home_message_max_scroll() > 0.0:
		scroll_drag_active = true
		scroll_drag_area = "home_message"
		scroll_drag_last_y = position.y
		return true
	if nav.current_screen == "Messages" and _messages_scroll_rect().has_point(position) and _messages_max_scroll() > 0.0:
		scroll_drag_active = true
		scroll_drag_area = "messages"
		scroll_drag_last_y = position.y
		return true
	if nav.current_screen == "Diagnostics" and _diagnostics_scroll_rect().has_point(position) and _diagnostics_max_scroll() > 0.0:
		scroll_drag_active = true
		scroll_drag_area = "diagnostics"
		scroll_drag_last_y = position.y
		return true
	if nav.current_screen == "Notification Control Center" and _notification_scrollbar_hit_rect().has_point(position) and _notification_max_scroll() > 0.0:
		scroll_drag_active = true
		scroll_drag_area = "notifications"
		scroll_drag_last_y = position.y
		return true
	if nav.current_screen == "Notification Control Center" and _control_scroll_rect().has_point(position) and _control_center_max_scroll() > 0.0:
		scroll_drag_active = true
		scroll_drag_area = "control"
		scroll_drag_last_y = position.y
		return true
	# Settings is a dense clickable grid; drag-scroll starts only from the scrollbar strip
	# so normal tile and row taps are not consumed before _handle_settings_tap runs.
	if nav.current_screen == "Settings" and _settings_scrollbar_hit_rect().has_point(position) and _settings_max_scroll() > 0.0:
		scroll_drag_active = true
		scroll_drag_area = "settings"
		scroll_drag_last_y = position.y
		return true
	# Quick Shelf is a clickable tile grid; drag-scroll starts only from the
	# scrollbar strip so normal tile taps reach _handle_quick_shelf_panel_tap.
	if nav.current_screen == "Quick Shelf" and _quick_shelf_scrollbar_hit_rect().has_point(position) and _quick_shelf_max_scroll() > 0.0:
		scroll_drag_active = true
		scroll_drag_area = "quick_shelf"
		scroll_drag_last_y = position.y
		return true
	if nav.current_screen == "Study" and study_current_page == "smart_study" and _study_segment_scrollbar_hit_rect().has_point(position) and _study_segment_max_scroll() > 0.0:
		scroll_drag_active = true
		scroll_drag_area = "study_segments"
		scroll_drag_last_y = position.y
		return true
	if nav.current_screen == "Reminders" and _reminders_upcoming_scrollbar_hit_rect().has_point(position) and _reminders_max_scroll("upcoming") > 0.0:
		scroll_drag_active = true
		scroll_drag_area = "reminders_upcoming"
		scroll_drag_last_y = position.y
		return true
	if nav.current_screen == "Reminders" and _reminders_past_scrollbar_hit_rect().has_point(position) and _reminders_max_scroll("past") > 0.0:
		scroll_drag_active = true
		scroll_drag_area = "reminders_past"
		scroll_drag_last_y = position.y
		return true
	if nav.current_screen == "To Do" and todo_mode == "lists" and _todo_lists_scrollbar_hit_rect().has_point(position) and _todo_lists_max_scroll() > 0.0:
		scroll_drag_active = true
		scroll_drag_area = "todo_lists"
		scroll_drag_last_y = position.y
		return true
	if nav.current_screen == "To Do" and todo_mode == "list_detail" and _todo_tasks_scrollbar_hit_rect().has_point(position) and _todo_tasks_max_scroll() > 0.0:
		scroll_drag_active = true
		scroll_drag_area = "todo_tasks"
		scroll_drag_last_y = position.y
		return true
	return false

func _update_scroll_drag(position: Vector2) -> void:
	var delta_y: float = scroll_drag_last_y - position.y
	scroll_drag_last_y = position.y
	_apply_scroll(scroll_drag_area, delta_y)

func _handle_scroll_wheel(position: Vector2, amount: float) -> void:
	_reset_user_activity()
	if nav.current_screen == "Face Home" and home_message_active:
		_apply_scroll("home_message", amount)
	elif nav.current_screen == "Messages" and _messages_scroll_rect().has_point(position):
		_apply_scroll("messages", amount)
	elif nav.current_screen == "Diagnostics" and _diagnostics_scroll_rect().has_point(position):
		_apply_scroll("diagnostics", amount)
	elif nav.current_screen == "Notification Control Center" and _notification_scroll_rect().has_point(position):
		_apply_scroll("notifications", amount)
	elif nav.current_screen == "Notification Control Center" and _control_scroll_rect().has_point(position):
		_apply_scroll("control", amount)
	elif nav.current_screen == "Settings" and _settings_scroll_rect().has_point(position):
		_apply_scroll("settings", amount)
	elif nav.current_screen == "Quick Shelf" and _quick_shelf_scroll_rect().has_point(position):
		_apply_scroll("quick_shelf", amount)
	elif nav.current_screen == "Study" and study_current_page == "smart_study" and _study_segment_scroll_rect().has_point(position):
		_apply_scroll("study_segments", amount)
	elif nav.current_screen == "Reminders" and _reminders_upcoming_scroll_rect().has_point(position):
		_apply_scroll("reminders_upcoming", amount)
	elif nav.current_screen == "Reminders" and _reminders_past_scroll_rect().has_point(position):
		_apply_scroll("reminders_past", amount)
	elif nav.current_screen == "To Do" and todo_mode == "lists" and _todo_lists_scroll_rect().has_point(position):
		_apply_scroll("todo_lists", amount)
	elif nav.current_screen == "To Do" and todo_mode == "list_detail" and _todo_tasks_scroll_rect().has_point(position):
		_apply_scroll("todo_tasks", amount)

func _apply_scroll(area: String, amount: float) -> void:
	if area == "diagnostics":
		diagnostic_scroll_y = clampf(diagnostic_scroll_y + amount, 0.0, _diagnostics_max_scroll())
		_request_redraw()
	elif area == "control":
		control_center_scroll_y = clampf(control_center_scroll_y + amount, 0.0, _control_center_max_scroll())
		_request_redraw()
	elif area == "notifications":
		notification_scroll_y = clampf(notification_scroll_y + amount, 0.0, _notification_max_scroll())
		_request_redraw()
	elif area == "settings":
		settings_scroll_y = clampf(settings_scroll_y + amount, 0.0, _settings_max_scroll())
		_request_redraw()
	elif area == "quick_shelf":
		quick_shelf_scroll_y = clampf(quick_shelf_scroll_y + amount, 0.0, _quick_shelf_max_scroll())
		_request_redraw()
	elif area == "study_segments":
		study_segment_scroll_y = clampf(study_segment_scroll_y + amount, 0.0, _study_segment_max_scroll())
		_request_redraw()
	elif area == "reminders_upcoming":
		reminders_upcoming_scroll_y = clampf(reminders_upcoming_scroll_y + amount, 0.0, _reminders_max_scroll("upcoming"))
		_request_redraw()
	elif area == "reminders_past":
		reminders_past_scroll_y = clampf(reminders_past_scroll_y + amount, 0.0, _reminders_max_scroll("past"))
		_request_redraw()
	elif area == "todo_lists":
		todo_scroll_y = clampf(todo_scroll_y + amount, 0.0, _todo_lists_max_scroll())
		_request_redraw()
	elif area == "todo_tasks":
		todo_task_scroll_y = clampf(todo_task_scroll_y + amount, 0.0, _todo_tasks_max_scroll())
		_request_redraw()
	elif area == "home_message":
		home_message_scroll_y = clampf(home_message_scroll_y + amount, 0.0, _home_message_max_scroll())
		_request_redraw()
	elif area == "messages":
		messages_scroll_y = clampf(messages_scroll_y + amount, 0.0, _messages_max_scroll())
		_request_redraw()

func _diagnostics_scroll_rect() -> Rect2:
	return Rect2(24, 138, 592, 318)

func _control_scroll_rect() -> Rect2:
	return Rect2(36, 286, 568, 166)

func _notification_scroll_rect() -> Rect2:
	return Rect2(44, 318, 552, 130)

func _notification_scrollbar_hit_rect() -> Rect2:
	var rect := _notification_scroll_rect()
	return Rect2(rect.position.x + rect.size.x - 22.0, rect.position.y, 22.0, rect.size.y)

func _settings_scroll_rect() -> Rect2:
	return Rect2(24, 84, 592, 372)

func _settings_scrollbar_hit_rect() -> Rect2:
	return Rect2(596, 84, 24, 372)

func _quick_shelf_scroll_rect() -> Rect2:
	return Rect2(24, 120, 592, 324)

func _quick_shelf_scrollbar_hit_rect() -> Rect2:
	return Rect2(596, 120, 24, 324)

func _study_segment_scroll_rect() -> Rect2:
	return Rect2(44, 210, 354, 160)

func _study_segment_scrollbar_hit_rect() -> Rect2:
	return Rect2(384, 210, 20, 160)

func _diagnostics_max_scroll() -> float:
	return maxf(0.0, _diagnostics_content_height() - _diagnostics_scroll_rect().size.y)

func _control_center_max_scroll() -> float:
	return maxf(0.0, _control_center_content_height() - _control_scroll_rect().size.y)

func _notification_content_height() -> float:
	return maxf(_notification_scroll_rect().size.y, float(notifications_data.size()) * 48.0 + 8.0)

func _notification_max_scroll() -> float:
	return maxf(0.0, _notification_content_height() - _notification_scroll_rect().size.y)

func _settings_max_scroll() -> float:
	return maxf(0.0, _settings_content_height() - _settings_scroll_rect().size.y)

func _quick_shelf_max_scroll() -> float:
	return maxf(0.0, _quick_shelf_content_height() - _quick_shelf_scroll_rect().size.y)

func _study_segment_max_scroll() -> float:
	return maxf(0.0, _study_segment_content_height() - _study_segment_scroll_rect().size.y)

func _diagnostics_content_height() -> float:
	if active_tab == "Processes":
		return 362.0
	if active_tab == "Benchmarks":
		return 420.0
	if active_tab == "Camera":
		return 300.0
	if active_tab == "Logs":
		return 420.0
	if active_tab == "Reports":
		return 340.0
	if active_tab == "Overview":
		return 400.0
	if active_tab == "Network":
		return 520.0
	if active_tab == "Study Stats":
		return 360.0
	return 260.0

func _control_center_content_height() -> float:
	return 182.0

func _settings_content_height() -> float:
	if settings_current_page == "home":
		return 754.0
	if settings_current_page == "appearance":
		return 760.0
	if settings_current_page == "user":
		return 340.0
	if settings_current_page == "quick_shelf":
		return 760.0
	if settings_current_page == "privacy":
		return 640.0
	if settings_current_page == "about":
		return 760.0
	return 520.0

func _quick_shelf_content_height() -> float:
	var count: int = max(8, _settings_enabled_quick_shelf().size())
	return 142.0 + float(ceil(float(count) / 2.0)) * 72.0

func _study_segment_content_height() -> float:
	return maxf(_study_segment_scroll_rect().size.y, float(study_segments.size()) * 30.0 + 8.0)

func _reminders_upcoming_scroll_rect() -> Rect2:
	return Rect2(44, 206, 262, 218)

func _reminders_past_scroll_rect() -> Rect2:
	return Rect2(334, 206, 262, 218)

func _reminders_upcoming_scrollbar_hit_rect() -> Rect2:
	return Rect2(294, 206, 18, 218)

func _reminders_past_scrollbar_hit_rect() -> Rect2:
	return Rect2(584, 206, 18, 218)

func _reminders_content_height(kind: String) -> float:
	return maxf(_reminders_upcoming_scroll_rect().size.y, float(_reminders_list_count(kind)) * 42.0 + 8.0)

func _reminders_max_scroll(kind: String) -> float:
	var view := _reminders_upcoming_scroll_rect() if kind == "upcoming" else _reminders_past_scroll_rect()
	return maxf(0.0, _reminders_content_height(kind) - view.size.y)

func _reminders_list_count(kind: String) -> int:
	var raw = reminders_data.get(kind, [])
	if raw is Array:
		return raw.size()
	return 0

func _reminder_row_rect(kind: String, index: int) -> Rect2:
	var x := 48.0 if kind == "upcoming" else 338.0
	var scroll := reminders_upcoming_scroll_y if kind == "upcoming" else reminders_past_scroll_y
	return Rect2(x, 230.0 + float(index) * 42.0 - scroll, 242.0, 34.0)

func _todo_lists_scroll_rect() -> Rect2:
	return Rect2(24, 82, 592, 370)

func _todo_lists_scrollbar_hit_rect() -> Rect2:
	return Rect2(596, 82, 20, 370)

func _todo_tasks_scroll_rect() -> Rect2:
	return Rect2(24, 108, 592, 344)

func _todo_tasks_scrollbar_hit_rect() -> Rect2:
	return Rect2(596, 108, 20, 344)

func _todo_lists_content_height() -> float:
	return maxf(_todo_lists_scroll_rect().size.y, float(_todo_lists().size()) * 78.0 + 12.0)

func _todo_lists_max_scroll() -> float:
	return maxf(0.0, _todo_lists_content_height() - _todo_lists_scroll_rect().size.y)

func _todo_tasks_content_height() -> float:
	return maxf(_todo_tasks_scroll_rect().size.y, 36.0 + float(_todo_active_tasks().size()) * 48.0 + 42.0 + float(_todo_completed_tasks().size()) * 48.0 + 20.0)

func _todo_tasks_max_scroll() -> float:
	return maxf(0.0, _todo_tasks_content_height() - _todo_tasks_scroll_rect().size.y)

func _todo_list_card_rect(index: int) -> Rect2:
	return Rect2(44, 96.0 + float(index) * 78.0 - todo_scroll_y, 552, 64)

func _todo_task_row_rect(index: int, completed: bool) -> Rect2:
	var y := 146.0 + float(index) * 48.0
	if completed:
		y = 186.0 + float(_todo_active_tasks().size()) * 48.0 + float(index) * 48.0
	return Rect2(44, y - todo_task_scroll_y, 552, 40)

func _todo_lists() -> Array:
	var raw = todo_lists_data.get("lists", [])
	return raw if raw is Array else []

func _todo_active_tasks() -> Array:
	var raw = todo_tasks_data.get("active", [])
	return raw if raw is Array else []

func _todo_completed_tasks() -> Array:
	var raw = todo_tasks_data.get("completed", [])
	return raw if raw is Array else []

func _home_clock_rect() -> Rect2:
	return Rect2(482, 22, 56, 24)

func _home_message_text_rect() -> Rect2:
	var reserved_actions := 46.0 if not home_message_actions.is_empty() else 0.0
	return Rect2(HOME_MESSAGE_TEXT_X, HOME_MESSAGE_TEXT_TOP_PADDING, HOME_MESSAGE_TEXT_W, HEIGHT - HOME_MESSAGE_TEXT_TOP_PADDING - HOME_MESSAGE_TEXT_BOTTOM_PADDING - reserved_actions)

func _home_message_action_rect(index: int) -> Rect2:
	# Actions sit at the bottom of the right (text) half
	return Rect2(342.0 + float(index) * 86.0, 424, 80, 30)

func _home_message_close_rect() -> Rect2:
	# Near top-right of text area (text runs x=342..606)
	return Rect2(584, 58, 26, 26)

func _message_indicator_rect() -> Rect2:
	if nav.current_screen == "Face Home":
		return Rect2(546, 22, 30, 28)
	return Rect2(546, 60, 30, 28)

func _notification_indicator_rect() -> Rect2:
	if nav.current_screen == "Face Home":
		return Rect2(584, 22, 30, 28)
	return Rect2(584, 60, 30, 28)

func _messages_scroll_rect() -> Rect2:
	return Rect2(28, 88, 584, 360)

func _message_row_rect(index: int) -> Rect2:
	return Rect2(44, 96.0 + float(index) * 64.0 - messages_scroll_y, 552, 54)

func _messages_content_height() -> float:
	return maxf(_messages_scroll_rect().size.y, float(nexa_messages_data.size()) * 64.0 + 12.0)

func _messages_max_scroll() -> float:
	return maxf(0.0, _messages_content_height() - _messages_scroll_rect().size.y)

func _home_message_lines() -> Array:
	var text := home_message_title + "\n" + home_message_body
	return _wrap_text_to_width(text, 25)

func _home_message_content_height() -> float:
	return float(_home_message_lines().size()) * 24.0 + (42.0 if not home_message_actions.is_empty() else 0.0)

func _home_message_max_scroll() -> float:
	return maxf(0.0, _home_message_content_height() - _home_message_text_rect().size.y)

func _wrap_text_to_width(text: String, max_chars_per_line: int) -> Array:
	var lines: Array = []
	for raw_paragraph in text.split("\n"):
		var paragraph := str(raw_paragraph)
		if paragraph.strip_edges() == "":
			lines.append("")
			continue
		var current := ""
		for raw_word in paragraph.split(" "):
			var word := str(raw_word)
			if current == "":
				current = word
			elif current.length() + 1 + word.length() <= max_chars_per_line:
				current += " " + word
			else:
				lines.append(current)
				current = word
		if current != "":
			lines.append(current)
	return lines

func _start_startup_sequence() -> void:
	startup_sequence_active = true
	startup_sequence_elapsed = 0.0
	startup_sequence_finished = false
	startup_check_status = "pending"
	startup_check_done = false
	startup_greeting_shown = false
	_request_redraw()

func _update_startup_sequence(delta: float) -> void:
	startup_sequence_elapsed += delta
	if startup_sequence_elapsed >= 1.0 and not startup_check_done:
		startup_check_status = "ready"
		startup_check_done = true
	if startup_sequence_elapsed >= STARTUP_SEQUENCE_SECONDS:
		_finish_startup_sequence()
	else:
		_request_redraw()

func _finish_startup_sequence() -> void:
	if startup_sequence_finished:
		return
	startup_sequence_active = false
	startup_sequence_finished = true
	startup_check_status = "ready"
	startup_check_done = true
	if not startup_greeting_shown:
		startup_greeting_shown = true
		_push_nexa_message({
			"id": "startup_greeting",
			"title": _get_startup_greeting_title(),
			"body": "NeXa is ready.",
			"source": "Home",
			"message_type": "greeting",
			"priority": "normal",
			"expression": "happy",
			"led_behavior": "startup_soft",
			"sound_cue": "startup_chime",
			"display_policy": "home_or_indicator",
			"actions": []
		})
	_show_next_home_item_if_available()
	_request_redraw()

func _startup_alpha(start: float, duration: float) -> float:
	return clampf((startup_sequence_elapsed - start) / duration, 0.0, 1.0)

func _startup_ease(start: float, duration: float) -> float:
	return _smoothstep(_startup_alpha(start, duration))

func _smoothstep(value: float) -> float:
	var t := clampf(value, 0.0, 1.0)
	return t * t * (3.0 - 2.0 * t)

func _get_user_first_name() -> String:
	return str(_settings_value("user", "first_name", "")).strip_edges()

func _get_user_preferred_name() -> String:
	return str(_settings_value("user", "preferred_name", "")).strip_edges()

func _get_startup_greeting_title() -> String:
	var preferred_name := _get_user_preferred_name()
	if preferred_name != "":
		return "Hello, " + preferred_name + "."
	var first_name := _get_user_first_name()
	if first_name != "":
		return "Hello, " + first_name + "."
	return "Hello"

func _push_nexa_message(message: Dictionary) -> void:
	var message_id := str(message.get("id", "msg:" + str(nexa_messages_data.size() + 1)))
	if bool(nexa_message_dismissed_ids.get(message_id, false)):
		return
	for raw_message in nexa_messages_data:
		var existing: Dictionary = raw_message as Dictionary
		if str(existing.get("id", "")) == message_id:
			return
	message["id"] = message_id
	if not message.has("display_policy"):
		message["display_policy"] = "home_or_indicator"
	nexa_messages_data.append(message)
	nexa_messages_data.sort_custom(func(a, b): return _message_priority_value(a) > _message_priority_value(b))
	_update_message_indicator_count()
	if nav.current_screen == "Face Home" and not startup_sequence_active and not home_message_active and str(message.get("display_policy", "home_or_indicator")) in ["home_only", "home_or_indicator"]:
		_show_home_message(message)
	else:
		_request_redraw()

func _message_priority_value(message: Dictionary) -> int:
	return int(MESSAGE_PRIORITY_ORDER.get(str(message.get("priority", "normal")), 1))

func _update_message_indicator_count() -> void:
	nexa_message_indicator_count = nexa_messages_data.size()

func _show_home_message(message: Dictionary) -> void:
	home_message_active = true
	home_message_id = str(message.get("id", ""))
	home_message_title = str(message.get("title", "NeXa"))
	home_message_body = str(message.get("body", ""))
	home_message_type = str(message.get("message_type", "info"))
	home_message_priority = str(message.get("priority", "normal"))
	home_message_expression = str(message.get("expression", "focused"))
	home_message_source = str(message.get("source", "NeXa"))
	var actions_raw = message.get("actions", [])
	home_message_actions = actions_raw if actions_raw is Array else []
	home_message_scroll_y = 0.0
	home_message_fade = 0.0
	home_message_visible_elapsed = 0.0
	home_message_auto_dismiss_enabled = _home_message_should_auto_dismiss(home_message_type, home_message_source)
	_start_home_message_enter()
	_apply_home_behavior("notification_soft" if home_message_type != "greeting" else "startup_greeting")
	_request_redraw()

func _home_message_should_auto_dismiss(message_type: String, source: String) -> bool:
	if str(source).begins_with("notification"):
		return false
	return message_type in ["greeting", "info", "study", "system", "diagnostic", "temperature", "status"]

func _update_home_message_visible_timer(delta: float) -> void:
	if nav.current_screen != "Face Home" or not home_message_auto_dismiss_enabled:
		return
	if home_message_enter_active or home_message_exit_active:
		return
	home_message_started_visible = true
	home_message_visible_elapsed += delta
	if home_message_visible_elapsed >= home_message_auto_dismiss_seconds:
		_start_home_message_exit(true)

func _update_home_message_enter(delta: float) -> void:
	if not home_message_enter_active:
		return
	home_message_enter_elapsed += delta
	if home_message_enter_elapsed >= home_message_enter_seconds:
		home_message_enter_elapsed = home_message_enter_seconds
		home_message_enter_active = false
	_request_redraw()

func _home_message_enter_progress() -> float:
	if home_message_enter_seconds <= 0.0:
		return 1.0
	return _smoothstep(clampf(home_message_enter_elapsed / home_message_enter_seconds, 0.0, 1.0))

func _home_message_enter_y_offset() -> float:
	return lerpf(-180.0, 0.0, _home_message_enter_progress())

func _home_message_enter_alpha() -> float:
	return _home_message_enter_progress()

func _close_home_message_preview(remember_hidden: bool = true) -> void:
	if remember_hidden and home_message_id != "":
		if home_message_id.begins_with("notification:"):
			notification_preview_hidden_ids[home_message_id] = true
		else:
			home_message_hidden_ids[home_message_id] = true
	home_message_active = false
	home_message_id = ""
	home_message_title = ""
	home_message_body = ""
	home_message_actions = []
	home_message_scroll_y = 0.0
	home_message_fade = 0.0
	home_message_visible_elapsed = 0.0
	home_message_started_visible = false
	home_message_auto_dismiss_enabled = true
	home_message_enter_elapsed = 0.0
	home_message_enter_active = false
	home_message_exit_active = false
	home_message_exit_elapsed = 0.0
	face_message_position_progress = 0.0
	_apply_home_behavior("idle_calm")
	_update_message_indicator_count()
	_show_next_home_item_if_available()
	_request_redraw()

func _dismiss_home_message() -> void:
	if home_message_id != "":
		nexa_message_dismissed_ids[home_message_id] = true
		for index in range(nexa_messages_data.size() - 1, -1, -1):
			var message: Dictionary = nexa_messages_data[index] as Dictionary
			if str(message.get("id", "")) == home_message_id:
				nexa_messages_data.remove_at(index)
	_close_home_message_preview(true)

func _handle_home_message_tap(position: Vector2) -> void:
	if _handle_home_message_close_tap(position):
		return
	for index in range(home_message_actions.size()):
		if _home_message_action_rect(index).has_point(position):
			_activate_home_message_action(str((home_message_actions[index] as Dictionary).get("id", "")))
			return
	if _home_message_text_rect().has_point(position) and _home_message_max_scroll() <= 0.0:
		return

func _handle_home_message_action_event(event: InputEvent) -> bool:
	if event.is_action_pressed("nexa_back"):
		_start_home_message_exit(true)
		return true
	if event.is_action_pressed("nexa_accept"):
		if not home_message_actions.is_empty():
			_activate_home_message_action(str((home_message_actions[0] as Dictionary).get("id", "")))
		else:
			_start_home_message_exit(true)
		return true
	if event.is_action_pressed("nexa_down"):
		_apply_scroll("home_message", 28.0)
		return true
	if event.is_action_pressed("nexa_up"):
		_apply_scroll("home_message", -28.0)
		return true
	return false

func _handle_home_message_close_tap(position: Vector2) -> bool:
	if _home_message_close_rect().has_point(position):
		_start_home_message_exit(true)
		return true
	return false

func _activate_home_message_action(action_id: String) -> void:
	if action_id == "dismiss" or action_id == "not_now":
		if action_id == "not_now":
			study_break_not_now_segment_id = study_break_game_suggested_for_segment_id
		_start_home_message_exit(true)
	elif action_id == "open_games":
		study_break_game_active = true
		study_break_game_started_at = Time.get_datetime_string_from_system(false, true)
		_close_home_message_preview(true)
		_open_games()
	elif action_id == "open_notifications":
		_close_home_message_preview(true)
		_open_control_center_notifications()
	elif action_id == "done":
		_start_home_message_exit(true)
	else:
		_start_home_message_exit(true)

func _handle_messages_action_event(event: InputEvent) -> bool:
	if event.is_action_pressed("nexa_back") or event.is_action_pressed("nexa_exit"):
		_go_home()
		return true
	if event.is_action_pressed("nexa_down"):
		_apply_scroll("messages", 32.0)
		return true
	if event.is_action_pressed("nexa_up"):
		_apply_scroll("messages", -32.0)
		return true
	return false

func _handle_messages_tap(position: Vector2) -> void:
	if Rect2(520, 22, 92, 34).has_point(position):
		_go_home()
		return
	for index in range(nexa_messages_data.size()):
		var rect := _message_row_rect(index)
		if rect.has_point(position):
			var message: Dictionary = nexa_messages_data[index] as Dictionary
			nav.current_screen = "Face Home"
			transition_active = false
			home_message_hidden_ids.erase(str(message.get("id", "")))
			_show_home_message(message)
			return

## NeXa Messages swipe-delete helpers
func _begin_message_row_swipe(position: Vector2) -> bool:
	if nav.current_screen != "Messages":
		return false
	if not _messages_scroll_rect().has_point(position):
		return false
	for index in range(nexa_messages_data.size()):
		if _message_row_rect(index).has_point(position):
			var message: Dictionary = nexa_messages_data[index] as Dictionary
			messages_swipe_active_id = str(message.get("id", ""))
			messages_swipe_start_x = position.x
			messages_swipe_start_y = position.y
			messages_swipe_row_index = index
			return messages_swipe_active_id != ""
	return false

func _finish_message_row_swipe(position: Vector2) -> void:
	var active_id := messages_swipe_active_id
	messages_swipe_active_id = ""
	messages_swipe_row_index = -1
	if active_id == "":
		return
	var dx := position.x - messages_swipe_start_x
	var dy := position.y - messages_swipe_start_y
	if absf(dx) > 60.0 and absf(dx) > absf(dy):
		# Horizontal swipe: dismiss the message
		_dismiss_nexa_message_by_id(active_id)
		return
	if absf(dy) > 60.0 and absf(dy) > absf(dx):
		# Vertical swipe: scroll the list
		_apply_scroll("messages", -dy)
		return
	# Short movement: treat as tap, open message
	for index in range(nexa_messages_data.size()):
		var message: Dictionary = nexa_messages_data[index] as Dictionary
		if str(message.get("id", "")) == active_id:
			if _message_row_rect(index).has_point(position) and absf(dx) < 18.0 and absf(dy) < 18.0:
				nav.current_screen = "Face Home"
				transition_active = false
				home_message_hidden_ids.erase(str(message.get("id", "")))
				_show_home_message(message)
			return

func _dismiss_nexa_message_by_id(message_id: String) -> void:
	if message_id == "":
		return
	nexa_message_dismissed_ids[message_id] = true
	for index in range(nexa_messages_data.size() - 1, -1, -1):
		var message: Dictionary = nexa_messages_data[index] as Dictionary
		if str(message.get("id", "")) == message_id:
			nexa_messages_data.remove_at(index)
	_update_message_indicator_count()
	_request_redraw()

## Home message enter / exit animation helpers
func _start_home_message_enter() -> void:
	home_message_enter_elapsed = 0.0
	home_message_enter_active = true
	home_message_exit_active = false
	home_message_exit_elapsed = 0.0
	face_message_position_progress = 0.0
	home_message_started_visible = nav.current_screen == "Face Home"

func _start_home_message_exit(remember_hidden: bool = true) -> void:
	if home_message_exit_active:
		return
	home_message_exit_active = true
	home_message_exit_elapsed = 0.0
	home_message_exit_remember_hidden = remember_hidden
	home_message_enter_active = false

func _update_home_message_exit_anim(delta: float) -> void:
	home_message_exit_elapsed += delta
	if home_message_exit_elapsed >= home_message_exit_seconds:
		home_message_exit_elapsed = home_message_exit_seconds
		home_message_exit_active = false
		_finish_home_message_exit()
	else:
		_request_redraw()

func _finish_home_message_exit() -> void:
	_close_home_message_preview(home_message_exit_remember_hidden)

func _home_message_transition_progress() -> float:
	if home_message_exit_active:
		return _smoothstep(clampf(home_message_exit_elapsed / home_message_exit_seconds, 0.0, 1.0))
	return _home_message_enter_progress()

func _home_message_text_y_offset() -> float:
	if home_message_exit_active:
		var t := _smoothstep(clampf(home_message_exit_elapsed / home_message_exit_seconds, 0.0, 1.0))
		return lerpf(0.0, -180.0, t)
	return lerpf(-180.0, 0.0, _home_message_enter_progress())

func _home_message_text_alpha() -> float:
	if home_message_exit_active:
		var t := _smoothstep(clampf(home_message_exit_elapsed / home_message_exit_seconds, 0.0, 1.0))
		return lerpf(1.0, 0.0, t)
	return _home_message_enter_progress()

func _home_message_face_center() -> Vector2:
	var t: float
	if home_message_exit_active:
		t = 1.0 - _smoothstep(clampf(home_message_exit_elapsed / home_message_exit_seconds, 0.0, 1.0))
	else:
		t = _home_message_enter_progress()
	return HOME_MESSAGE_FACE_IDLE_CENTER.lerp(HOME_MESSAGE_FACE_CENTER, t)

func _home_message_face_scale() -> float:
	var t: float
	if home_message_exit_active:
		t = 1.0 - _smoothstep(clampf(home_message_exit_elapsed / home_message_exit_seconds, 0.0, 1.0))
	else:
		t = _home_message_enter_progress()
	return lerpf(HOME_MESSAGE_FACE_IDLE_SCALE, HOME_MESSAGE_FACE_SCALE, t)

## Transition face helper: smoothly moves face off-screen as panels slide in/out
func _home_face_transition_center(base_center: Vector2) -> Vector2:
	if not transition_active:
		return base_center
	var t := _ease_transition(transition_progress)
	var cx := base_center.x
	var cy := base_center.y
	match transition_direction:
		"menu_open":
			cx = lerpf(WIDTH * 0.5, HOME_FACE_OFFSCREEN_LEFT_X, t)
		"menu_close":
			cx = lerpf(HOME_FACE_OFFSCREEN_LEFT_X, WIDTH * 0.5, t)
		"clock_open":
			cx = lerpf(WIDTH * 0.5, HOME_FACE_OFFSCREEN_RIGHT_X, t)
		"clock_close":
			cx = lerpf(HOME_FACE_OFFSCREEN_RIGHT_X, WIDTH * 0.5, t)
		"control_open":
			cy = lerpf(245.0, HOME_FACE_OFFSCREEN_DOWN_Y, t)
		"control_close":
			cy = lerpf(HOME_FACE_OFFSCREEN_DOWN_Y, 245.0, t)
		"quick_open":
			cy = lerpf(245.0, HOME_FACE_OFFSCREEN_UP_Y, t)
		"quick_close":
			cy = lerpf(HOME_FACE_OFFSCREEN_UP_Y, 245.0, t)
	return Vector2(cx, cy)

func _handle_top_indicator_tap(position: Vector2) -> bool:
	if nav.current_screen == "Games":
		return false
	if _message_indicator_rect().has_point(position) and nexa_message_indicator_count > 0:
		_open_messages_center()
		return true
	if _notification_indicator_rect().has_point(position) and notification_indicator_count > 0:
		_open_control_center_notifications()
		return true
	return false

func _show_next_home_item_if_available() -> void:
	if startup_sequence_active or nav.current_screen != "Face Home" or home_message_active:
		return
	var best_message := {}
	for raw_message in nexa_messages_data:
		var message: Dictionary = raw_message as Dictionary
		var message_id := str(message.get("id", ""))
		var display_policy := str(message.get("display_policy", "home_or_indicator"))
		if bool(home_message_hidden_ids.get(message_id, false)):
			continue
		if display_policy not in ["home_only", "home_or_indicator"]:
			continue
		if best_message.is_empty() or _message_priority_value(message) > _message_priority_value(best_message):
			best_message = message
	if not best_message.is_empty():
		_show_home_message(best_message)
		return
	var notification := _next_home_notification_preview()
	if not notification.is_empty():
		_show_home_message(notification)

func _next_home_notification_preview() -> Dictionary:
	if notifications_data.is_empty():
		return {}
	var best_notification := {}
	var best_priority := -1
	for raw_notification in notifications_data:
		var notification: Dictionary = raw_notification as Dictionary
		var preview_id := "notification:" + str(notification.get("id", ""))
		if bool(notification_preview_hidden_ids.get(preview_id, false)):
			continue
		var priority := _message_priority_value({"priority": "reminder"})
		if priority > best_priority:
			best_priority = priority
			best_notification = notification
	if best_notification.is_empty():
		return {}
	return {
		"id": "notification:" + str(best_notification.get("id", "")),
		"title": str(best_notification.get("title", "Notification")),
		"body": (str(best_notification.get("body", "")) + "\n" + str(best_notification.get("subtitle", ""))).strip_edges(),
		"source": "notification:" + str(best_notification.get("type", "notification")),
		"message_type": str(best_notification.get("type", "notification")),
		"priority": "reminder",
		"expression": "focused",
		"display_policy": "home_or_indicator",
		"actions": [{"id": "open_notifications", "label": "Open"}, {"id": "dismiss", "label": "Dismiss"}]
	}

func _apply_home_behavior(behavior_id: String) -> void:
	behavior_last_applied_id = behavior_id
	if behavior_id == "startup_greeting":
		current_face_expression = "happy"
		current_led_behavior = "startup_soft"
		current_sound_cue = "startup_chime"
		face_mouth_style = "small_smile"
	elif behavior_id == "notification_soft":
		current_face_expression = "focused"
		current_led_behavior = "notification_blue"
		current_sound_cue = "notification_chime"
		face_mouth_style = "neutral"
	elif behavior_id == "warning_soft":
		current_face_expression = "concerned"
		current_led_behavior = "warning_amber"
		current_sound_cue = "warning_soft"
		face_mouth_style = "concerned"
	elif behavior_id == "private_locked":
		current_face_expression = "locked"
		current_led_behavior = "private_lock"
		current_sound_cue = "none"
		face_mouth_style = "neutral"
	else:
		current_face_expression = "calm"
		current_led_behavior = "idle_soft"
		current_sound_cue = "none"
		face_mouth_style = "neutral"
	face_expression = current_face_expression

func _update_face_behavior(delta: float) -> void:
	face_idle_elapsed += delta
	if face_blink_active:
		face_blink_progress += delta / 0.18
		if face_blink_progress >= 1.0:
			face_blink_active = false
			face_blink_progress = 0.0
			face_idle_elapsed = 0.0
			face_next_blink_seconds = 8.0 + fmod(elapsed * 1.37, 4.0)
			_request_redraw()
	elif face_idle_elapsed >= face_next_blink_seconds:
		face_blink_active = true
		face_blink_progress = 0.0
		_request_redraw()

func _update_inactivity(delta: float) -> void:
	if text_input_open or nav.current_screen in INACTIVITY_EXEMPT_SCREENS:
		inactivity_elapsed = 0.0
		return
	if nav.current_screen == "Face Home":
		inactivity_elapsed = 0.0
		return
	inactivity_elapsed += delta
	if inactivity_elapsed >= inactivity_timeout_seconds:
		inactivity_elapsed = 0.0
		_go_home()

func _reset_user_activity() -> void:
	inactivity_elapsed = 0.0
	last_seen_user_at = elapsed
	if clock_shown_for_absence and nav.current_screen == "Clock":
		clock_shown_for_absence = false

func _update_presence_face_clock(delta: float) -> void:
	hardware_presence_active = hardware_connected and not hardware_stale and bool(hardware_state_data.get("presence", false))
	if hardware_presence_active:
		presence_absence_seconds = 0.0
		last_seen_user_at = elapsed
		if clock_shown_for_absence and nav.current_screen == "Clock":
			clock_shown_for_absence = false
			_go_home()
		return
	presence_absence_seconds += delta
	if nav.current_screen != "Face Home" or home_message_active or text_input_open or transition_active:
		return
	if presence_absence_seconds >= presence_show_clock_after_seconds:
		clock_shown_for_absence = true
		_open_clock()

func _sync_notification_policy_after_rebuild() -> void:
	notification_indicator_count = notifications_data.size()
	reminders_due_modal_open = nav.current_screen == "Face Home" and reminders_due_modal_open
	calendar_due_modal_open = nav.current_screen == "Face Home" and calendar_due_modal_open
	todo_due_modal_open = nav.current_screen == "Face Home" and todo_due_modal_open
	_show_next_home_item_if_available()

func _handle_study_break_game_policy(payload: Dictionary) -> void:
	var active := bool(payload.get("active", false))
	var kind := str(payload.get("kind", payload.get("current_segment_type", "")))
	var segment_raw = payload.get("segment", {})
	var segment_id := 0
	if segment_raw is Dictionary:
		segment_id = int((segment_raw as Dictionary).get("id", 0))
	if segment_id > 0:
		study_break_last_segment_id = segment_id
	var planned := int(payload.get("planned_seconds", 0))
	var remaining := int(payload.get("remaining_seconds", planned))
	var break_elapsed: int = max(0, planned - remaining)
	if active and kind == "break" and segment_id > 0 and break_elapsed >= 30 and study_break_game_suggested_for_segment_id != segment_id and study_break_not_now_segment_id != segment_id:
		study_break_game_suggested_for_segment_id = segment_id
		_push_nexa_message({
			"id": "study_break_game:" + str(segment_id),
			"title": "Break time",
			"body": "Want to play a quick game during your break?",
			"source": "Study",
			"message_type": "study",
			"priority": "normal",
			"expression": "focused",
			"led_behavior": "notification_blue",
			"sound_cue": "notification_chime",
			"display_policy": "home_or_indicator",
			"actions": [{"id": "open_games", "label": "Yes"}, {"id": "not_now", "label": "Not now"}]
		})
	if study_break_game_active and active and kind == "focus":
		study_break_game_active = false
		study_break_return_pending = true
		if nav.current_screen == "Games":
			_open_study("smart_study")
		_push_nexa_message({
			"id": "study_break_done:" + str(segment_id),
			"title": "Break is over.",
			"body": "Focus time starts now.",
			"source": "Study",
			"message_type": "study",
			"priority": "important",
			"expression": "focused",
			"display_policy": "home_or_indicator",
			"actions": []
		})

func _games_card_rect(index: int) -> Rect2:
	return Rect2(44.0 + float(index % 2) * 278.0, 126.0 + float(int(index / 2)) * 112.0 - games_library_scroll_y, 252.0, 88.0)

func _games_exit_rect() -> Rect2:
	return Rect2(520, 22, 92, 34)

func _ttt_back_rect() -> Rect2:
	return Rect2(28, 24, 84, 32)

func _ttt_exit_rect() -> Rect2:
	return Rect2(528, 24, 84, 32)

func _ttt_menu_button_rect(index: int) -> Rect2:
	return Rect2(160, 238.0 + float(index) * 52.0, 320, 38)

func _ttt_board_rect() -> Rect2:
	return Rect2(185, 112, 270, 270)

func _ttt_cell_rect(index: int) -> Rect2:
	var board := _ttt_board_rect()
	var size := board.size.x / 3.0
	return Rect2(board.position.x + float(index % 3) * size + 4.0, board.position.y + float(int(index / 3)) * size + 4.0, size - 8.0, size - 8.0)

func _ttt_new_game_rect() -> Rect2:
	return Rect2(244, 408, 152, 34)

func _ttt_result_button_rect(index: int) -> Rect2:
	return Rect2(116.0 + float(index) * 140.0, 338, 128, 36)

func _ttt_exit_confirm_button_rect(index: int) -> Rect2:
	return Rect2(150.0 + float(index) * 180.0, 330, 150, 38)

func _open_games() -> void:
	nav.previous_screen = nav.current_screen
	nav.current_screen = "Games"
	transition_active = false
	games_mode = "library"
	games_focus_index = 0
	games_help_open = false
	games_library_scroll_y = 0.0
	_request_redraw()

func _open_tic_tac_toe_menu() -> void:
	games_mode = "tic_tac_toe_menu"
	tic_tac_toe_menu_focus_index = 0
	games_help_open = false
	_request_redraw()

func _start_tic_tac_toe(mode: String) -> void:
	tic_tac_toe_mode = mode
	games_mode = "tic_tac_toe_game"
	_reset_tic_tac_toe()

func _reset_tic_tac_toe() -> void:
	_ttt_reset()
	tic_tac_toe_result_focus_index = 0
	_request_redraw()

func _exit_games_to_face_home() -> void:
	games_help_open = false
	games_mode = "library"
	tic_tac_toe_nexa_thinking = false
	_go_home()

func _back_from_game_screen() -> void:
	if games_help_open:
		games_help_open = false
	elif games_mode == "library":
		_go_home()
	elif games_mode == "tic_tac_toe_menu":
		games_mode = "library"
		games_focus_index = 0
	elif games_mode == "tic_tac_toe_game":
		games_mode = "tic_tac_toe_menu"
		tic_tac_toe_nexa_thinking = false
	elif games_mode == "tic_tac_toe_result":
		games_mode = "tic_tac_toe_menu"
	elif games_mode == "exit_confirm":
		games_mode = games_exit_confirm_return
	else:
		games_mode = "library"
	_request_redraw()

func _games_exit_pressed() -> void:
	if games_mode == "tic_tac_toe_game" and _ttt_has_moves() and not tic_tac_toe_game_over:
		games_exit_confirm_return = "tic_tac_toe_game"
		games_mode = "exit_confirm"
	else:
		_exit_games_to_face_home()
	_request_redraw()

func _handle_games_action_event(event: InputEvent) -> bool:
	if event.is_action_pressed("nexa_exit"):
		_games_exit_pressed()
		return true
	if event.is_action_pressed("nexa_back"):
		_back_from_game_screen()
		return true
	if event.is_action_pressed("nexa_accept"):
		_games_accept_focused()
		return true
	if event.is_action_pressed("nexa_left"):
		_games_move_focus("left")
		return true
	if event.is_action_pressed("nexa_right"):
		_games_move_focus("right")
		return true
	if event.is_action_pressed("nexa_up"):
		_games_move_focus("up")
		return true
	if event.is_action_pressed("nexa_down"):
		_games_move_focus("down")
		return true
	return false

func _games_move_focus(direction: String) -> void:
	if games_mode == "library":
		if direction == "left" and games_focus_index > 0:
			games_focus_index -= 1
		elif direction == "right" and games_focus_index < 4:
			games_focus_index += 1
		elif direction == "up":
			games_focus_index = max(0, games_focus_index - 2)
		elif direction == "down":
			games_focus_index = min(4, games_focus_index + 2)
	elif games_mode == "tic_tac_toe_menu":
		if direction == "up":
			tic_tac_toe_menu_focus_index = max(0, tic_tac_toe_menu_focus_index - 1)
		elif direction == "down":
			tic_tac_toe_menu_focus_index = min(2, tic_tac_toe_menu_focus_index + 1)
	elif games_mode == "tic_tac_toe_game":
		if tic_tac_toe_nexa_thinking:
			return
		if direction == "left" and tic_tac_toe_selected_cell not in [0, 3, 6]:
			tic_tac_toe_selected_cell -= 1
		elif direction == "right" and tic_tac_toe_selected_cell not in [2, 5, 8]:
			tic_tac_toe_selected_cell += 1
		elif direction == "up" and tic_tac_toe_selected_cell not in [0, 1, 2]:
			tic_tac_toe_selected_cell -= 3
		elif direction == "down" and tic_tac_toe_selected_cell not in [6, 7, 8]:
			tic_tac_toe_selected_cell += 3
	elif games_mode == "tic_tac_toe_result":
		if direction == "left" or direction == "up":
			tic_tac_toe_result_focus_index = max(0, tic_tac_toe_result_focus_index - 1)
		elif direction == "right" or direction == "down":
			tic_tac_toe_result_focus_index = min(2, tic_tac_toe_result_focus_index + 1)
	_request_redraw()

func _games_accept_focused() -> void:
	if games_help_open:
		games_help_open = false
	elif games_mode == "library":
		if games_focus_index == 0:
			_open_tic_tac_toe_menu()
		elif games_focus_index == 4:
			_exit_games_to_face_home()
	elif games_mode == "tic_tac_toe_menu":
		if tic_tac_toe_menu_focus_index == 0:
			_start_tic_tac_toe("someone")
		elif tic_tac_toe_menu_focus_index == 1:
			_start_tic_tac_toe("nexa")
		else:
			games_help_open = true
	elif games_mode == "tic_tac_toe_game":
		_ttt_play_selected_cell()
	elif games_mode == "tic_tac_toe_result":
		_ttt_activate_result_button(tic_tac_toe_result_focus_index)
	elif games_mode == "exit_confirm":
		games_mode = games_exit_confirm_return
	_request_redraw()

func _handle_games_tap(position: Vector2) -> void:
	if games_mode == "exit_confirm":
		for index in range(2):
			if _ttt_exit_confirm_button_rect(index).has_point(position):
				if index == 0:
					games_mode = games_exit_confirm_return
				else:
					_exit_games_to_face_home()
				_request_redraw()
				return
	if games_help_open:
		if Rect2(190, 338, 260, 38).has_point(position) or _ttt_back_rect().has_point(position):
			games_help_open = false
			_request_redraw()
		return
	if games_mode == "library":
		if _games_exit_rect().has_point(position):
			_exit_games_to_face_home()
			return
		for index in range(4):
			if _games_card_rect(index).has_point(position):
				games_focus_index = index
				if index == 0:
					_open_tic_tac_toe_menu()
				_request_redraw()
				return
	elif games_mode == "tic_tac_toe_menu":
		if _ttt_back_rect().has_point(position):
			_back_from_game_screen()
			return
		if _ttt_exit_rect().has_point(position):
			_exit_games_to_face_home()
			return
		for index in range(3):
			if _ttt_menu_button_rect(index).has_point(position):
				tic_tac_toe_menu_focus_index = index
				_games_accept_focused()
				return
	elif games_mode == "tic_tac_toe_game":
		if _ttt_back_rect().has_point(position):
			_back_from_game_screen()
			return
		if _ttt_exit_rect().has_point(position):
			_games_exit_pressed()
			return
		if _ttt_new_game_rect().has_point(position):
			_reset_tic_tac_toe()
			return
		for index in range(9):
			if _ttt_cell_rect(index).has_point(position):
				tic_tac_toe_selected_cell = index
				_ttt_play_selected_cell()
				return
	elif games_mode == "tic_tac_toe_result":
		for index in range(3):
			if _ttt_result_button_rect(index).has_point(position):
				tic_tac_toe_result_focus_index = index
				_ttt_activate_result_button(index)
				return

func _ttt_reset() -> void:
	tic_tac_toe_board = [TTT_EMPTY, TTT_EMPTY, TTT_EMPTY, TTT_EMPTY, TTT_EMPTY, TTT_EMPTY, TTT_EMPTY, TTT_EMPTY, TTT_EMPTY]
	tic_tac_toe_current_player = TTT_PLAYER_X
	tic_tac_toe_selected_cell = 4
	tic_tac_toe_result = ""
	tic_tac_toe_game_over = false
	tic_tac_toe_nexa_thinking = false
	tic_tac_toe_thinking_elapsed = 0.0
	tic_tac_toe_status_text = "Your turn" if tic_tac_toe_mode == "nexa" else "Player X turn"

func _ttt_can_play(index: int) -> bool:
	return index >= 0 and index < 9 and not tic_tac_toe_game_over and not tic_tac_toe_nexa_thinking and str(tic_tac_toe_board[index]) == TTT_EMPTY

func _ttt_play(index: int) -> bool:
	if not _ttt_can_play(index):
		tic_tac_toe_status_text = "Choose an empty cell."
		return false
	tic_tac_toe_board[index] = tic_tac_toe_current_player
	_ttt_after_move()
	return true

func _ttt_get_winner() -> String:
	return _ttt_winner_for_board(tic_tac_toe_board)

func _ttt_is_draw() -> bool:
	return _ttt_get_winner() == "" and _ttt_available_moves().is_empty()

func _ttt_available_moves() -> Array:
	var moves: Array = []
	for index in range(9):
		if str(tic_tac_toe_board[index]) == TTT_EMPTY:
			moves.append(index)
	return moves

func _ttt_switch_turn() -> void:
	tic_tac_toe_current_player = TTT_PLAYER_O if tic_tac_toe_current_player == TTT_PLAYER_X else TTT_PLAYER_X

func _ttt_choose_nexa_move() -> int:
	var winning_move := _ttt_find_winning_move(TTT_PLAYER_O)
	if winning_move != -1:
		return winning_move
	var blocking_move := _ttt_find_winning_move(TTT_PLAYER_X)
	if blocking_move != -1:
		return blocking_move
	if str(tic_tac_toe_board[4]) == TTT_EMPTY:
		return 4
	for corner in [0, 2, 6, 8]:
		if str(tic_tac_toe_board[corner]) == TTT_EMPTY:
			return corner
	var moves := _ttt_available_moves()
	if moves.is_empty():
		return -1
	return int(moves[0])

func _ttt_find_winning_move(player: String) -> int:
	for move in _ttt_available_moves():
		var test_board := tic_tac_toe_board.duplicate()
		test_board[int(move)] = player
		if _ttt_winner_for_board(test_board) == player:
			return int(move)
	return -1

func _ttt_winner_for_board(test_board: Array) -> String:
	for raw_line in TTT_WIN_LINES:
		var line: Array = raw_line as Array
		var a := int(line[0])
		var b := int(line[1])
		var c := int(line[2])
		var value := str(test_board[a])
		if value != TTT_EMPTY and value == str(test_board[b]) and value == str(test_board[c]):
			return value
	return ""

func _ttt_play_selected_cell() -> void:
	_ttt_play(tic_tac_toe_selected_cell)
	_request_redraw()

func _ttt_after_move() -> void:
	var winner := _ttt_get_winner()
	if winner != "":
		tic_tac_toe_result = winner
		tic_tac_toe_game_over = true
		games_mode = "tic_tac_toe_result"
		tic_tac_toe_result_focus_index = 0
		tic_tac_toe_status_text = _ttt_result_title()
		return
	if _ttt_is_draw():
		tic_tac_toe_result = "draw"
		tic_tac_toe_game_over = true
		games_mode = "tic_tac_toe_result"
		tic_tac_toe_result_focus_index = 0
		tic_tac_toe_status_text = "Draw"
		return
	if tic_tac_toe_mode == "nexa" and tic_tac_toe_current_player == TTT_PLAYER_X:
		tic_tac_toe_current_player = TTT_PLAYER_O
		tic_tac_toe_nexa_thinking = true
		tic_tac_toe_thinking_elapsed = 0.0
		tic_tac_toe_status_text = "NeXa is thinking..."
	else:
		_ttt_switch_turn()
		tic_tac_toe_status_text = "Player " + tic_tac_toe_current_player + " turn"

func _ttt_finish_nexa_turn() -> void:
	tic_tac_toe_nexa_thinking = false
	tic_tac_toe_thinking_elapsed = 0.0
	var move := _ttt_choose_nexa_move()
	if move >= 0:
		tic_tac_toe_board[move] = TTT_PLAYER_O
	var winner := _ttt_get_winner()
	if winner != "":
		tic_tac_toe_result = winner
		tic_tac_toe_game_over = true
		games_mode = "tic_tac_toe_result"
		tic_tac_toe_status_text = _ttt_result_title()
	elif _ttt_is_draw():
		tic_tac_toe_result = "draw"
		tic_tac_toe_game_over = true
		games_mode = "tic_tac_toe_result"
		tic_tac_toe_status_text = "Draw"
	else:
		tic_tac_toe_current_player = TTT_PLAYER_X
		tic_tac_toe_status_text = "Your turn"
	_request_redraw()

func _ttt_activate_result_button(index: int) -> void:
	if index == 0:
		games_mode = "tic_tac_toe_game"
		_reset_tic_tac_toe()
	elif index == 1:
		games_mode = "tic_tac_toe_menu"
	else:
		_exit_games_to_face_home()
	_request_redraw()

func _ttt_has_moves() -> bool:
	return _ttt_available_moves().size() < 9

func _ttt_result_title() -> String:
	if tic_tac_toe_result == "draw":
		return "Draw"
	if tic_tac_toe_mode == "nexa":
		return "You win" if tic_tac_toe_result == TTT_PLAYER_X else "NeXa wins"
	return "Player " + tic_tac_toe_result + " wins"

func _open_menu() -> void:
	hardware_menu_focus_index = 0
	_navigate_to("Menu", "menu_open")

func _open_clock() -> void:
	_navigate_to("Clock", "clock_open")

func _open_control_center() -> void:
	_navigate_to("Notification Control Center", "control_open")
	control_center_refresh_pending = true
	# Control Center opens from cached data first. API refresh happens after transition to avoid UI lag.

func _open_control_center_notifications() -> void:
	_open_control_center()
	selected_control_detail = ""
	notification_scroll_y = 0.0

func _open_messages_center() -> void:
	nav.previous_screen = nav.current_screen
	nav.current_screen = "Messages"
	transition_active = false
	messages_scroll_y = 0.0
	_request_redraw()

func _open_quick_shelf() -> void:
	_navigate_to("Quick Shelf", "quick_open")
	quick_shelf_scroll_y = 0.0
	if settings_data.is_empty():
		api.request_get("/api/settings")

func _open_environment() -> void:
	nav.previous_screen = nav.current_screen
	nav.current_screen = "Environment"
	transition_active = false
	api.request_get("/api/hardware/state")
	_request_redraw()

func _open_study(page: String = "home") -> void:
	nav.previous_screen = nav.current_screen
	nav.current_screen = "Study"
	transition_active = false
	study_current_page = page
	study_scroll_y = 0.0
	_request_study_page_data()
	_request_redraw()

func _open_reminders() -> void:
	nav.previous_screen = nav.current_screen
	nav.current_screen = "Reminders"
	transition_active = false
	reminders_mode = "list"
	api.request_get("/api/reminders/list")
	api.request_get("/api/reminders/due")
	_request_redraw()

func _open_calendar() -> void:
	nav.previous_screen = nav.current_screen
	nav.current_screen = "Calendar"
	transition_active = false
	if calendar_year <= 0 or calendar_month <= 0:
		var now := Time.get_datetime_dict_from_system()
		calendar_year = int(now.year)
		calendar_month = int(now.month)
		calendar_selected_date = "%04d-%02d-%02d" % [now.year, now.month, now.day]
	calendar_mode = "details"
	_request_calendar_month()
	_request_calendar_day()
	api.request_get("/api/calendar/due")
	_request_redraw()

func _open_todo() -> void:
	nav.previous_screen = nav.current_screen
	nav.current_screen = "To Do"
	transition_active = false
	todo_mode = "lists"
	todo_scroll_y = 0.0
	api.request_get("/api/todo/lists")
	api.request_get("/api/todo/due")
	_request_redraw()

func _open_todo_list(list_id: int) -> void:
	nav.previous_screen = nav.current_screen
	nav.current_screen = "To Do"
	transition_active = false
	todo_mode = "list_detail"
	todo_selected_list_id = int(list_id)
	todo_task_scroll_y = 0.0
	api.request_get("/api/todo/tasks?list_id=" + str(todo_selected_list_id))
	api.request_get("/api/todo/due")
	_request_redraw()

func _request_calendar_month() -> void:
	api.request_get("/api/calendar/month?year=" + str(calendar_year) + "&month=" + str(calendar_month) + "&selected_date=" + calendar_selected_date)

func _request_calendar_day() -> void:
	api.request_get("/api/calendar/day?date=" + calendar_selected_date)

func _calendar_change_month(delta: int) -> void:
	calendar_month += delta
	if calendar_month < 1:
		calendar_month = 12
		calendar_year -= 1
	elif calendar_month > 12:
		calendar_month = 1
		calendar_year += 1
	calendar_selected_event_id = 0
	calendar_selected_event = {}
	_request_calendar_month()
	_request_redraw()

func _open_diagnostics() -> void:
	nav.previous_screen = nav.current_screen
	nav.current_screen = "Diagnostics"
	transition_active = false
	active_tab = "Overview"
	active_tab_data = {}
	api.request_get("/api/overview")
	_request_redraw()

func _open_settings() -> void:
	nav.previous_screen = nav.current_screen
	nav.current_screen = "Settings"
	transition_active = false
	settings_current_page = "home"
	settings_scroll_y = 0.0
	api.request_get("/api/settings")
	_request_redraw()

func _open_settings_placeholder() -> void:
	_open_settings()

func _open_placeholder(title: String) -> void:
	nav.placeholder_title = title
	_navigate_to(title, "diagnostics")

func _go_home() -> void:
	if nav.current_screen == "Face Home":
		return
	if nav.current_screen == "Diagnostics" and active_tab == "Camera":
		_stop_camera_preview()
	if nav.current_screen == "Settings":
		settings_current_page = "home"
	var direction := "diagnostics"
	if nav.current_screen == "Menu":
		direction = "menu_close"
	elif nav.current_screen == "Clock":
		direction = "clock_close"
	elif nav.current_screen == "Notification Control Center":
		direction = "control_close"
	elif nav.current_screen == "Quick Shelf":
		direction = "quick_close"
	elif nav.current_screen == "Study":
		study_current_page = "home"
	elif nav.current_screen == "Reminders":
		reminders_mode = "list"
	elif nav.current_screen == "Calendar":
		calendar_mode = "details"
	elif nav.current_screen == "Environment":
		pass
	elif nav.current_screen == "To Do":
		todo_mode = "lists"
	elif nav.current_screen == "Games":
		games_mode = "library"
		games_help_open = false
		tic_tac_toe_nexa_thinking = false
	elif nav.current_screen == "Messages":
		messages_scroll_y = 0.0
	if direction == "diagnostics":
		nav.previous_screen = nav.current_screen
		nav.current_screen = "Face Home"
		transition_active = false
		_request_redraw()
	else:
		_navigate_to("Face Home", direction)

func _navigate_to(screen_name: String, direction: String) -> void:
	if nav.current_screen == screen_name:
		return
	transition_overlay = nav.current_screen if direction.ends_with("_close") else screen_name
	transition_direction = direction
	transition_progress = 0.0
	transition_duration = CLOSE_TRANSITION_SECONDS if direction.ends_with("_close") else TRANSITION_SECONDS
	transition_closing = direction.ends_with("_close")
	transition_active = true
	nav.previous_screen = nav.current_screen
	if not transition_closing:
		nav.current_screen = screen_name
	_request_redraw()

func _request_redraw() -> void:
	redraw_requested = true

func _update_api_polling(delta: float) -> void:
	hardware_poll_elapsed += delta
	api_poll_accumulator += delta
	study_timer_poll_accumulator += delta
	reminders_poll_accumulator += delta
	calendar_poll_accumulator += delta
	todo_poll_accumulator += delta
	if api.in_flight:
		return
	if transition_active:
		return
	if hardware_poll_elapsed >= hardware_poll_interval_seconds:
		hardware_poll_elapsed = 0.0
		api.request_get("/api/hardware/state")
		return
	var reminders_interval := 1.0 if reminders_due_modal_open else 5.0
	if reminders_poll_accumulator >= reminders_interval:
		reminders_poll_accumulator = 0.0
		api.request_get("/api/reminders/due")
		return
	var calendar_interval := 5.0 if calendar_due_modal_open else 30.0
	if calendar_poll_accumulator >= calendar_interval:
		calendar_poll_accumulator = 0.0
		api.request_get("/api/calendar/due")
		return
	var todo_interval := 5.0 if todo_due_modal_open else 30.0
	if todo_poll_accumulator >= todo_interval:
		todo_poll_accumulator = 0.0
		api.request_get("/api/todo/due")
		return
	if (nav.current_screen == "Face Home" or nav.current_screen == "Study") and study_timer_poll_accumulator >= 1.0:
		study_timer_poll_accumulator = 0.0
		api.request_get("/api/study/smart/status")
		return
	if nav.current_screen == "Notification Control Center" and control_center_refresh_pending:
		control_center_refresh_pending = false
		api_poll_accumulator = 0.0
		api.request_get("/api/control-center")
	elif nav.current_screen == "Notification Control Center" and selected_control_detail == "wifi" and network_detail_pending:
		network_detail_pending = false
		api_poll_accumulator = 0.0
		api.request_get("/api/network")
	elif nav.current_screen == "Notification Control Center" and api_poll_accumulator >= 3.0:
		api_poll_accumulator = 0.0
		api.request_get("/api/control-center")
	elif nav.current_screen == "Diagnostics":
		var interval: float = 5.0
		if active_tab == "Processes":
			interval = 1.0
		elif active_tab == "System":
			interval = 2.0
		elif active_tab == "Camera":
			interval = 2.0 if not camera_preview_on else 1.0
		if api_poll_accumulator >= interval:
			api_poll_accumulator = 0.0
			_request_active_diagnostics_tab()
	if nav.current_screen == "Diagnostics" and active_tab == "Camera" and camera_preview_on and not api.frame_in_flight:
		camera_frame_poll_accumulator += delta
		if camera_frame_poll_accumulator >= 0.12:
			camera_frame_poll_accumulator = 0.0
			api.request_frame("/api/camera/preview/frame")

func _request_active_diagnostics_tab() -> void:
	var endpoint: String = "/api/overview"
	if active_tab == "System":
		endpoint = "/api/system"
	elif active_tab == "Processes":
		endpoint = "/api/processes"
	elif active_tab == "Camera":
		endpoint = "/api/camera"
	elif active_tab == "Audio":
		endpoint = "/api/audio"
	elif active_tab == "Network":
		endpoint = "/api/network"
	elif active_tab == "Logs":
		endpoint = "/api/logs"
	elif active_tab == "Reports":
		endpoint = "/api/reports"
	elif active_tab == "Benchmarks":
		endpoint = "/api/benchmarks/status"
	elif active_tab == "Study Stats":
		endpoint = "/api/study/stats"
	api.request_get(endpoint)

func _request_study_page_data() -> void:
	if study_current_page == "home" or study_current_page == "stats":
		api.request_get("/api/study/stats")
	elif study_current_page == "history":
		api.request_get("/api/study/history")
	elif study_current_page == "settings":
		api.request_get("/api/study/settings/stats")
	elif study_current_page == "pomodoro" or study_current_page == "smart_study":
		api.request_get("/api/study/smart/status")
	elif study_current_page == "flashcards":
		api.request_get("/api/study/flashcards/decks")
	elif study_current_page == "quizzes":
		api.request_get("/api/study/quizzes")
	elif study_current_page == "languages":
		api.request_get("/api/study/languages/lists")

func _stop_camera_preview() -> void:
	if camera_preview_on:
		camera_preview_on = false
		camera_preview_status = "Off"
		camera_frame_texture = null
		api.request_post("/api/camera/preview/stop")

func _on_api_data_received(endpoint: String, payload: Dictionary) -> void:
	api_online = true
	api_status_text = "API online"
	if endpoint == "/api/control-center":
		control_center_data = payload
		brightness_percent = int(payload.get("brightness_percent", brightness_percent))
		if payload.get("sound_percent", null) != null:
			sound_percent = int(payload.get("sound_percent", sound_percent))
		quiet_mode_local = bool(payload.get("quiet_mode", quiet_mode_local))
		remote_network_local = str(payload.get("remote_network_state", remote_network_local))
	elif endpoint == "/api/hardware/state":
		_handle_hardware_state_payload(payload)
	elif endpoint.begins_with("/api/calendar/"):
		_handle_calendar_api(endpoint, payload)
	elif endpoint.begins_with("/api/todo/"):
		_handle_todo_api(endpoint, payload)
	elif endpoint.begins_with("/api/reminders/"):
		_handle_reminders_api(endpoint, payload)
	elif endpoint == "/api/overview":
		overview_live_data = payload
		active_tab_data = payload
	elif endpoint == "/api/network":
		network_detail_data = payload
		if nav.current_screen == "Diagnostics" and active_tab == "Network":
			active_tab_data = payload
	elif endpoint == "/api/study/timer/status":
		study_timer_data = payload
		if nav.current_screen == "Study" and study_current_page == "pomodoro":
			study_data = payload
	elif endpoint == "/api/study/smart/status":
		study_timer_data = payload
		var smart_session_raw = payload.get("session", {})
		if smart_session_raw is Dictionary:
			study_active_smart_session_id = int(smart_session_raw.get("id", study_active_smart_session_id))
		_handle_study_break_game_policy(payload)
		if nav.current_screen == "Study" and study_current_page == "smart_study":
			study_data = payload
	elif endpoint.begins_with("/api/study/"):
		study_status_text = str(payload.get("message", payload.get("status", "ok")))
		if endpoint == "/api/study/stats" or endpoint == "/api/study/overview" or endpoint == "/api/study/settings/stats":
			study_data = payload
			if nav.current_screen == "Diagnostics" and active_tab == "Study Stats":
				active_tab_data = payload
		elif endpoint == "/api/study/history":
			study_data = payload
		elif endpoint == "/api/study/flashcards/decks":
			study_data = payload
		elif endpoint.begins_with("/api/study/flashcards/deck"):
			study_data = payload
		elif endpoint == "/api/study/flashcards/decks/create":
			var deck_raw = payload.get("deck", {})
			if deck_raw is Dictionary:
				study_selected_deck_id = int(deck_raw.get("id", 0))
				study_flashcard_mode = "detail"
			api.request_get("/api/study/flashcards/decks")
		elif endpoint == "/api/study/flashcards/cards/create" or endpoint == "/api/study/flashcards/cards/update" or endpoint == "/api/study/flashcards/cards/delete":
			api.request_get("/api/study/flashcards/deck?deck_id=" + str(study_selected_deck_id))
		elif endpoint == "/api/study/flashcards/review":
			if payload.get("status", "") == "ok":
				study_status_text = "Correct" if bool(payload.get("was_correct", false)) else "Wrong. Correct answer: " + str(payload.get("correct_answer", ""))
				study_flashcard_feedback_text = study_status_text
				api.request_get("/api/study/flashcards/review/next?deck_id=" + str(study_selected_deck_id))
		elif endpoint.begins_with("/api/study/flashcards/review/next") or endpoint.begins_with("/api/study/flashcards/review/start"):
			var card_raw = payload.get("card", {})
			study_selected_card = card_raw if card_raw is Dictionary else {}
		if study_selected_card.is_empty() and study_flashcard_mode == "practice":
			study_flashcard_mode = "finished"
		elif endpoint == "/api/study/quizzes":
			study_data = payload
		elif endpoint.begins_with("/api/study/quizzes/quiz"):
			study_data = payload
		elif endpoint == "/api/study/quizzes/create":
			var quiz_raw = payload.get("quiz", {})
			if quiz_raw is Dictionary:
				study_selected_quiz_id = int(quiz_raw.get("id", 0))
				study_quiz_mode = "detail"
			api.request_get("/api/study/quizzes")
		elif endpoint == "/api/study/quizzes/questions/create" or endpoint == "/api/study/quizzes/questions/update" or endpoint == "/api/study/quizzes/questions/delete":
			study_pending_quiz_question = ""
			api.request_get("/api/study/quizzes/quiz?quiz_id=" + str(study_selected_quiz_id))
		elif endpoint == "/api/study/quizzes/answer":
			study_status_text = "Correct" if bool(payload.get("correct", false)) else "Wrong. Correct answer: " + str(payload.get("correct_answer", "")) + ". " + str(payload.get("correct_answer_text", ""))
			study_quiz_feedback_text = study_status_text
		elif endpoint.begins_with("/api/study/quizzes/question/next"):
			var question_raw = payload.get("question", {})
			study_selected_question = question_raw if question_raw is Dictionary else {}
			if study_selected_question.is_empty() and study_quiz_mode == "play":
				study_quiz_mode = "finished"
		elif endpoint == "/api/study/quizzes/mark-review":
			var marked_question_raw = payload.get("question", {})
			study_selected_question = marked_question_raw if marked_question_raw is Dictionary else study_selected_question
		elif endpoint == "/api/study/languages/lists":
			study_data = payload
		elif endpoint == "/api/study/languages/lists/create":
			var list_raw = payload.get("list", {})
			if list_raw is Dictionary:
				study_selected_language_list_id = int(list_raw.get("id", 0))
			api.request_get("/api/study/languages/lists")
		elif endpoint == "/api/study/languages/words/create":
			if study_language_mode == "edit":
				api.request_get("/api/study/languages/list?list_id=" + str(study_selected_language_list_id))
			else:
				api.request_get("/api/study/languages/lists")
		elif endpoint == "/api/study/languages/words/delete":
			study_selected_language_word_id = 0
			api.request_get("/api/study/languages/list?list_id=" + str(study_selected_language_list_id))
		elif endpoint == "/api/study/languages/review":
			var reviewed_word_raw = payload.get("word", {})
			study_selected_word = reviewed_word_raw if reviewed_word_raw is Dictionary else study_selected_word
		elif endpoint.begins_with("/api/study/languages/list"):
			study_data = payload
		elif endpoint.begins_with("/api/study/languages/word/next") or endpoint.begins_with("/api/study/languages/practice/next"):
			var word_raw = payload.get("word", {})
			study_selected_word = word_raw if word_raw is Dictionary else {}
			if study_selected_word.is_empty() and study_language_mode == "practice":
				study_language_mode = "finished"
		elif endpoint == "/api/study/pomodoro/start" or endpoint == "/api/study/timer/stop":
			api.request_get("/api/study/timer/status")
		elif endpoint == "/api/study/smart/start":
			study_active_smart_session_id = int(payload.get("session_id", 0))
			api.request_get("/api/study/smart/status")
		elif endpoint == "/api/study/smart/stop" or endpoint == "/api/study/smart/finish":
			api.request_get("/api/study/smart/status")
		elif endpoint == "/api/study/settings/delete":
			study_selected_deck_id = 0
			study_selected_quiz_id = 0
			if nav.current_screen == "Study" and study_current_page == "flashcards":
				api.request_get("/api/study/flashcards/decks")
			elif nav.current_screen == "Study" and study_current_page == "quizzes":
				api.request_get("/api/study/quizzes")
			else:
				api.request_get("/api/study/settings/stats")
	elif endpoint == "/api/settings" or endpoint == "/api/settings/update" or endpoint == "/api/settings/reset-section" or endpoint == "/api/privacy/pin/set":
		var settings_raw = payload.get("settings", {})
		if settings_raw is Dictionary:
			settings_data = settings_raw
			settings_status_text = "Saved"
		if endpoint == "/api/privacy/pin/set":
			if reminders_pending_private_after_pin:
				reminders_form_private = true
				reminders_pending_private_after_pin = false
				reminders_status_text = "Private reminder enabled."
				settings_status_text = "Private reminder enabled."
				nav.current_screen = "Reminders"
				reminders_mode = reminders_pending_private_form_mode if reminders_pending_private_form_mode != "" else "add"
				reminders_pending_private_form_mode = ""
			api.request_get("/api/privacy/status")
	elif endpoint == "/api/privacy/status" or endpoint == "/api/privacy/pin/verify" or endpoint == "/api/privacy/lock":
		privacy_status_data = payload
		settings_status_text = str(payload.get("message", "Saved"))
	else:
		active_tab_data = payload
		if endpoint == "/api/camera":
			var preview_raw = payload.get("preview", {})
			if preview_raw is Dictionary:
				camera_preview_on = bool(preview_raw.get("enabled", camera_preview_on))
				var camera_mode: String = str(preview_raw.get("mode", "off"))
				if camera_mode == "unavailable":
					camera_preview_status = "Live unavailable"
				elif bool(preview_raw.get("frame_available", false)):
					camera_preview_status = "On"
				elif camera_preview_on:
					camera_preview_status = "No frame yet" if preview_raw.get("error", null) == null else str(preview_raw.get("error"))
				else:
					camera_preview_status = "Off"
		if endpoint == "/api/camera/preview/start" or endpoint == "/api/camera/preview/status":
			camera_preview_on = bool(payload.get("enabled", camera_preview_on))
			var preview_mode: String = str(payload.get("mode", "off"))
			if preview_mode == "unavailable":
				camera_preview_status = "Live unavailable"
			else:
				camera_preview_status = "On" if bool(payload.get("frame_available", false)) else ("Starting" if camera_preview_on else "Off")
		if endpoint == "/api/camera/preview/stop":
			camera_preview_on = false
			camera_preview_status = "Off"
	_request_redraw()

func _handle_reminders_api(endpoint: String, payload: Dictionary) -> void:
	reminders_status_text = str(payload.get("message", payload.get("status", "ok")))
	if endpoint == "/api/reminders/list" or endpoint == "/api/reminders/overview":
		reminders_data = payload
		_reminders_restore_selected_from_data()
	elif endpoint == "/api/reminders/due":
		reminders_due_data = payload
		var due_raw = payload.get("due", [])
		var due_count := int(payload.get("count", 0))
		reminders_due_modal_open = due_count > 0 and due_raw is Array and not due_raw.is_empty()
		_rebuild_notifications_from_reminders()
		if notifications_data.is_empty():
			reminders_due_modal_open = false
		if reminders_due_modal_open:
			var first: Dictionary = _first_due_notification_item()
			reminders_pending_due_id = int(first.get("id", 0))
			if str(first.get("triggered_at", "")) == "":
				api.request_post("/api/reminders/mark-triggered", {"id": reminders_pending_due_id})
	elif endpoint in ["/api/reminders/create", "/api/reminders/update", "/api/reminders/delete", "/api/reminders/dismiss", "/api/reminders/snooze", "/api/reminders/mark-triggered"]:
		if endpoint == "/api/reminders/dismiss" or endpoint == "/api/reminders/snooze":
			reminders_due_modal_open = false
			_rebuild_notifications_from_reminders()
		reminders_mode = "list"
		api.request_get("/api/reminders/list")
		api.request_get("/api/reminders/due")
	_request_redraw()

func _handle_calendar_api(endpoint: String, payload: Dictionary) -> void:
	calendar_status_text = str(payload.get("message", payload.get("status", "ok")))
	if endpoint.begins_with("/api/calendar/month"):
		calendar_data = payload
	elif endpoint.begins_with("/api/calendar/day"):
		calendar_day_data = payload
		_calendar_restore_selected_from_day()
	elif endpoint == "/api/calendar/due":
		calendar_due_data = payload
		var due_raw = payload.get("due", [])
		calendar_due_modal_open = due_raw is Array and not due_raw.is_empty()
		_rebuild_notifications_from_reminders()
		if calendar_due_modal_open:
			var first := _first_calendar_due_item()
			calendar_pending_due_event_id = int(first.get("id", 0))
			calendar_pending_due_occurrence = str(first.get("occurrence_start", ""))
	elif endpoint in ["/api/calendar/events/create", "/api/calendar/events/update", "/api/calendar/events/delete", "/api/calendar/dismiss", "/api/calendar/snooze"]:
		if endpoint == "/api/calendar/dismiss" or endpoint == "/api/calendar/snooze":
			calendar_due_modal_open = false
			_rebuild_notifications_from_reminders()
		calendar_mode = "details"
		_request_calendar_month()
		_request_calendar_day()
		api.request_get("/api/calendar/due")
	_request_redraw()

func _handle_todo_api(endpoint: String, payload: Dictionary) -> void:
	todo_status_text = str(payload.get("message", payload.get("status", "ok")))
	if endpoint == "/api/todo/lists" or endpoint == "/api/todo/overview":
		todo_lists_data = payload
		if todo_selected_list_id <= 0 and not _todo_lists().is_empty():
			var first: Dictionary = _todo_lists()[0] as Dictionary
			todo_selected_list_id = int(first.get("id", 0))
	elif endpoint.begins_with("/api/todo/tasks?"):
		todo_tasks_data = payload
		_todo_restore_selected_from_tasks()
	elif endpoint == "/api/todo/due":
		todo_due_data = payload
		var due_raw = payload.get("due", [])
		todo_due_modal_open = due_raw is Array and not due_raw.is_empty()
		_rebuild_notifications_from_reminders()
		if todo_due_modal_open:
			var first := _first_todo_due_item()
			todo_pending_due_task_id = int(first.get("task_id", first.get("id", 0)))
	elif endpoint in ["/api/todo/lists/create", "/api/todo/lists/update", "/api/todo/lists/delete"]:
		var list_raw = payload.get("list", {})
		if list_raw is Dictionary:
			todo_selected_list_id = int(list_raw.get("id", todo_selected_list_id))
		api.request_get("/api/todo/lists")
	elif endpoint in ["/api/todo/tasks/create", "/api/todo/tasks/update", "/api/todo/tasks/delete", "/api/todo/tasks/mark-done", "/api/todo/tasks/mark-active", "/api/todo/dismiss", "/api/todo/snooze"]:
		if endpoint == "/api/todo/dismiss" or endpoint == "/api/todo/snooze" or endpoint == "/api/todo/tasks/mark-done":
			todo_due_modal_open = false
			_rebuild_notifications_from_reminders()
		api.request_get("/api/todo/tasks?list_id=" + str(todo_selected_list_id))
		api.request_get("/api/todo/due")
	_request_redraw()

func _first_todo_due_item() -> Dictionary:
	var due_raw = todo_due_data.get("due", [])
	if due_raw is Array and not due_raw.is_empty():
		return due_raw[0] as Dictionary
	return {}

func _todo_restore_selected_from_tasks() -> void:
	if todo_selected_task_id <= 0:
		return
	for raw_task in _todo_active_tasks() + _todo_completed_tasks():
		var task: Dictionary = raw_task as Dictionary
		if int(task.get("id", 0)) == todo_selected_task_id:
			todo_selected_task = task
			return
	todo_selected_task_id = 0
	todo_selected_task = {}

func _first_calendar_due_item() -> Dictionary:
	var due_raw = calendar_due_data.get("due", [])
	if due_raw is Array and not due_raw.is_empty():
		return due_raw[0] as Dictionary
	return {}

func _calendar_restore_selected_from_day() -> void:
	if calendar_selected_event_id <= 0:
		return
	for raw_event in _calendar_day_events():
		var event: Dictionary = raw_event as Dictionary
		if int(event.get("id", 0)) == calendar_selected_event_id:
			calendar_selected_event = event
			return
	calendar_selected_event_id = 0
	calendar_selected_event = {}

func _first_due_notification_item() -> Dictionary:
	for raw_notification in notifications_data:
		var notification: Dictionary = raw_notification as Dictionary
		if str(notification.get("type", "")) == "reminder":
			var source_raw = notification.get("source_item", {})
			if source_raw is Dictionary:
				return source_raw as Dictionary
			return {}
	var due_raw = reminders_due_data.get("due", [])
	if due_raw is Array and not due_raw.is_empty():
		return due_raw[0] as Dictionary
	return {}

func _rebuild_notifications_from_reminders() -> void:
	var next_notifications: Array = []
	var due_raw = reminders_due_data.get("due", [])
	if due_raw is Array:
		for raw_item in due_raw:
			var item: Dictionary = raw_item as Dictionary
			var source_id := int(item.get("id", 0))
			if source_id <= 0:
				continue
			var notification_id := "reminder:" + str(source_id)
			if bool(notification_dismissed_ids.get(notification_id, false)):
				continue
			var locked := bool(item.get("requires_pin", false))
			var title := "Private reminder locked" if locked else "Reminder"
			var body := "Private reminder locked" if locked else str(item.get("title", "Reminder"))
			var due_text := _format_due_label(str(item.get("due_at", "")))
			var subtitle := "Enter PIN to view" if locked else ("Due " + due_text)
			next_notifications.append({
				"id": notification_id,
				"type": "reminder",
				"title": title,
				"body": body,
				"subtitle": subtitle,
				"requires_pin": locked,
				"source_id": source_id,
				"source_item": item,
				"created_at": str(item.get("triggered_at", item.get("due_at", ""))),
				"dismissed_local": false
			})
	var calendar_due_raw = calendar_due_data.get("due", [])
	if calendar_due_raw is Array:
		for raw_calendar_item in calendar_due_raw:
			var calendar_item: Dictionary = raw_calendar_item as Dictionary
			var event_id := int(calendar_item.get("id", 0))
			if event_id <= 0:
				continue
			var occurrence := str(calendar_item.get("occurrence_start", ""))
			var notification_id := "calendar:" + str(event_id) + ":" + occurrence
			if bool(notification_dismissed_ids.get(notification_id, false)):
				continue
			next_notifications.append({
				"id": notification_id,
				"type": "calendar",
				"title": "Calendar",
				"body": str(calendar_item.get("title", "Calendar event")),
				"subtitle": "Starts at " + str(calendar_item.get("start_time", "")),
				"requires_pin": false,
				"source_id": event_id,
				"source_date": str(calendar_item.get("occurrence_date", calendar_item.get("start_date", ""))),
				"occurrence_start": occurrence,
				"source_item": calendar_item,
				"created_at": occurrence,
				"dismissed_local": false
			})
	var todo_due_raw = todo_due_data.get("due", [])
	if todo_due_raw is Array:
		for raw_todo_item in todo_due_raw:
			var todo_item: Dictionary = raw_todo_item as Dictionary
			var task_id := int(todo_item.get("task_id", todo_item.get("id", 0)))
			if task_id <= 0:
				continue
			var due_at := str(todo_item.get("due_at", ""))
			var todo_notification_id := "todo:" + str(task_id) + ":" + due_at
			if bool(notification_dismissed_ids.get(todo_notification_id, false)):
				continue
			next_notifications.append({
				"id": todo_notification_id,
				"type": "todo",
				"title": "To Do",
				"body": str(todo_item.get("title", "Task")),
				"subtitle": str(todo_item.get("list_emoji", "📥")) + " " + str(todo_item.get("list_name", "List")) + " • " + _format_due_label(due_at),
				"requires_pin": false,
				"source_id": task_id,
				"list_id": int(todo_item.get("list_id", 0)),
				"source_item": todo_item,
				"created_at": due_at,
				"dismissed_local": false
			})
	notifications_data = next_notifications
	notification_scroll_y = clampf(notification_scroll_y, 0.0, _notification_max_scroll())
	if notification_detail_modal_open and not notification_selected.is_empty():
		var selected_id := str(notification_selected.get("id", ""))
		if _notification_by_id(selected_id).is_empty():
			notification_detail_modal_open = false
			notification_selected = {}
	if notifications_data.is_empty():
		reminders_pending_due_id = 0
	_sync_notification_policy_after_rebuild()

func _format_due_label(value: String) -> String:
	if value.length() >= 16:
		return value.substr(0, 10) + " " + value.substr(11, 5)
	return value

func _notification_by_id(notification_id: String) -> Dictionary:
	for raw_notification in notifications_data:
		var notification: Dictionary = raw_notification as Dictionary
		if str(notification.get("id", "")) == notification_id:
			return notification
	return {}

func _local_remove_notification(notification_id: String, remember_dismissed: bool = true) -> void:
	if remember_dismissed:
		notification_dismissed_ids[notification_id] = true
	for index in range(notifications_data.size() - 1, -1, -1):
		var item: Dictionary = notifications_data[index] as Dictionary
		if str(item.get("id", "")) == notification_id:
			notifications_data.remove_at(index)
	if str(notification_selected.get("id", "")) == notification_id:
		notification_selected = {}
		notification_detail_modal_open = false
	if notification_id == "reminder:" + str(reminders_pending_due_id):
		reminders_due_modal_open = false
		reminders_pending_due_id = 0
	if notification_id == "calendar:" + str(calendar_pending_due_event_id) + ":" + calendar_pending_due_occurrence:
		calendar_due_modal_open = false
		calendar_pending_due_event_id = 0
		calendar_pending_due_occurrence = ""
	if notification_id.begins_with("todo:" + str(todo_pending_due_task_id) + ":"):
		todo_due_modal_open = false
		todo_pending_due_task_id = 0
	notification_indicator_count = notifications_data.size()
	_request_redraw()

func _dismiss_notification(notification: Dictionary) -> void:
	var notification_id := str(notification.get("id", ""))
	if notification_id == "":
		return
	_local_remove_notification(notification_id)
	if str(notification.get("type", "")) == "reminder":
		api.request_post("/api/reminders/dismiss", {"id": int(notification.get("source_id", 0))})
	elif str(notification.get("type", "")) == "calendar":
		api.request_post("/api/calendar/dismiss", {"event_id": int(notification.get("source_id", 0)), "occurrence_start": str(notification.get("occurrence_start", ""))})
	elif str(notification.get("type", "")) == "todo":
		api.request_post("/api/todo/dismiss", {"task_id": int(notification.get("source_id", 0))})

func _dismiss_pending_due_notification() -> void:
	var notification_id := "reminder:" + str(reminders_pending_due_id)
	var notification := _notification_by_id(notification_id)
	if notification.is_empty():
		_local_remove_notification(notification_id)
		api.request_post("/api/reminders/dismiss", {"id": reminders_pending_due_id})
	else:
		_dismiss_notification(notification)

func _dismiss_pending_calendar_notification() -> void:
	var notification_id := "calendar:" + str(calendar_pending_due_event_id) + ":" + calendar_pending_due_occurrence
	var notification := _notification_by_id(notification_id)
	if notification.is_empty():
		_local_remove_notification(notification_id)
		api.request_post("/api/calendar/dismiss", {"event_id": calendar_pending_due_event_id, "occurrence_start": calendar_pending_due_occurrence})
	else:
		_dismiss_notification(notification)

func _dismiss_pending_todo_notification() -> void:
	var notification := _todo_pending_notification()
	if notification.is_empty():
		api.request_post("/api/todo/tasks/mark-done", {"id": todo_pending_due_task_id})
	else:
		_local_remove_notification(str(notification.get("id", "")), true)
		api.request_post("/api/todo/tasks/mark-done", {"id": todo_pending_due_task_id})
	todo_due_modal_open = false

func _todo_pending_notification() -> Dictionary:
	for raw_notification in notifications_data:
		var notification: Dictionary = raw_notification as Dictionary
		if str(notification.get("type", "")) == "todo" and int(notification.get("source_id", 0)) == todo_pending_due_task_id:
			return notification
	return {}

func _handle_due_notification_modal_tap(position: Vector2) -> bool:
	if todo_due_modal_open and not _first_todo_due_item().is_empty():
		if Rect2(164, 324, 96, 34).has_point(position):
			_dismiss_pending_todo_notification()
			return true
		if Rect2(272, 324, 112, 34).has_point(position):
			var notification := _todo_pending_notification()
			if not notification.is_empty():
				_local_remove_notification(str(notification.get("id", "")), false)
			api.request_post("/api/todo/snooze", {"task_id": todo_pending_due_task_id, "minutes": 10})
			todo_due_modal_open = false
			return true
		if Rect2(396, 324, 96, 34).has_point(position):
			var first := _first_todo_due_item()
			todo_due_modal_open = false
			todo_selected_list_id = int(first.get("list_id", 0))
			todo_selected_task_id = todo_pending_due_task_id
			_open_todo_list(todo_selected_list_id)
			todo_mode = "task_detail"
			return true
		return false
	if calendar_due_modal_open and not _first_calendar_due_item().is_empty():
		if Rect2(164, 324, 96, 34).has_point(position):
			_dismiss_pending_calendar_notification()
			return true
		if Rect2(272, 324, 112, 34).has_point(position):
			api.request_post("/api/calendar/snooze", {"event_id": calendar_pending_due_event_id, "minutes": 10})
			_local_remove_notification("calendar:" + str(calendar_pending_due_event_id) + ":" + calendar_pending_due_occurrence, false)
			calendar_due_modal_open = false
			return true
		if Rect2(396, 324, 96, 34).has_point(position):
			calendar_due_modal_open = false
			calendar_selected_event_id = calendar_pending_due_event_id
			var first := _first_calendar_due_item()
			calendar_selected_date = str(first.get("occurrence_date", calendar_selected_date))
			_open_calendar()
			return true
		return false
	if not reminders_due_modal_open:
		return false
	if Rect2(164, 324, 96, 34).has_point(position):
		_dismiss_pending_due_notification()
		return true
	if Rect2(272, 324, 112, 34).has_point(position):
		api.request_post("/api/reminders/snooze", {"id": reminders_pending_due_id, "minutes": 5})
		_local_remove_notification("reminder:" + str(reminders_pending_due_id), false)
		reminders_due_modal_open = false
		return true
	if Rect2(396, 324, 96, 34).has_point(position):
		reminders_due_modal_open = false
		reminders_selected_id = reminders_pending_due_id
		_open_reminders()
		return true
	return false

func _handle_due_reminder_modal_tap(position: Vector2) -> bool:
	return _handle_due_notification_modal_tap(position)

func _reminders_restore_selected_from_data() -> void:
	if reminders_selected_id <= 0:
		return
	for kind in ["upcoming", "past"]:
		var rows_raw = reminders_data.get(kind, [])
		if rows_raw is Array:
			for index in range(rows_raw.size()):
				var item: Dictionary = rows_raw[index] as Dictionary
				if int(item.get("id", 0)) == reminders_selected_id:
					reminders_selected_item = item
					return
	reminders_selected_id = 0
	reminders_selected_item = {}

func _on_api_offline(endpoint: String) -> void:
	api_online = false
	api_status_text = "API offline"
	if endpoint == "/api/hardware/state":
		hardware_connected = false
		hardware_stale = true
	if endpoint == "/api/camera/preview/frame" and camera_preview_on:
		camera_preview_status = "No frame yet"
	_request_redraw()

func _handle_hardware_state_payload(payload: Dictionary) -> void:
	var state_raw = payload.get("state", {})
	if not (state_raw is Dictionary):
		hardware_connected = false
		hardware_stale = true
		return
	hardware_state_data = state_raw as Dictionary
	hardware_connected = bool(hardware_state_data.get("connected", false))
	hardware_stale = bool(hardware_state_data.get("stale", true))
	hardware_last_seen_at = str(hardware_state_data.get("last_seen_at", ""))
	_handle_hardware_joystick()

func _handle_hardware_joystick() -> void:
	var joystick := str(hardware_state_data.get("joystick", "UNKNOWN")).to_upper()
	if joystick == "CENTER" or joystick == "UNKNOWN":
		hardware_last_joystick = joystick
		return
	var cooldown := joystick_select_cooldown_seconds if joystick == "SELECT" else joystick_repeat_delay_seconds
	if elapsed - hardware_last_joystick_action_at < cooldown:
		hardware_last_joystick = joystick
		return
	hardware_last_joystick_action_at = elapsed
	hardware_last_joystick = joystick
	# This maps ESP joystick values to the current UI helpers without faking key events.
	if nav.current_screen == "Face Home":
		if joystick == "LEFT":
			_open_menu()
		elif joystick == "RIGHT":
			_open_clock()
		elif joystick == "DOWN":
			_open_control_center()
		elif joystick == "UP":
			_open_quick_shelf()
		elif joystick == "SELECT" and home_message_active:
			if not home_message_actions.is_empty():
				_activate_home_message_action(str((home_message_actions[0] as Dictionary).get("id", "")))
	elif nav.current_screen == "Clock" and joystick != "CENTER":
		_go_home()
	elif nav.current_screen == "Menu":
		if joystick == "LEFT":
			hardware_menu_focus_index = maxi(0, hardware_menu_focus_index - 1)
		elif joystick == "RIGHT":
			hardware_menu_focus_index = mini(MENU_TILES.size() - 1, hardware_menu_focus_index + 1)
		elif joystick == "UP":
			hardware_menu_focus_index = maxi(0, hardware_menu_focus_index - 2)
		elif joystick == "DOWN":
			hardware_menu_focus_index = mini(MENU_TILES.size() - 1, hardware_menu_focus_index + 2)
		elif joystick == "SELECT":
			_activate_menu_tile(hardware_menu_focus_index)
		_request_redraw()

func _activate_menu_tile(index: int) -> void:
	if index < 0 or index >= MENU_TILES.size():
		return
	var tile: Dictionary = MENU_TILES[index] as Dictionary
	if tile["title"] == "Time":
		_open_clock()
	elif tile["title"] == "Study":
		_open_study("home")
	elif tile["title"] == "Environment":
		_open_environment()
	elif tile["title"] == "Reminders":
		_open_reminders()
	elif tile["title"] == "Calendar":
		_open_calendar()
	elif tile["title"] == "To Do":
		_open_todo()
	elif tile["title"] == "Games":
		_open_games()
	elif tile["title"] == "Diagnostics":
		_open_diagnostics()
	elif tile["title"] == "Settings":
		_open_settings()
	else:
		_open_placeholder(str(tile["title"]) + " placeholder")

func _on_camera_frame_received(_endpoint: String, body: PackedByteArray) -> void:
	var image := Image.new()
	var error: int = image.load_jpg_from_buffer(body)
	if error != OK:
		error = image.load_png_from_buffer(body)
	if error == OK:
		camera_frame_texture = ImageTexture.create_from_image(image)
		camera_preview_status = "On"
	else:
		camera_preview_status = "No frame yet"
	_request_redraw()

func _draw() -> void:
	draw_rect(Rect2(Vector2.ZERO, Vector2(WIDTH, HEIGHT)), _theme_background_color(), true)
	if startup_sequence_active:
		_draw_startup_sequence()
		return
	if transition_active:
		_draw_transition()
	else:
		_draw_screen(nav.current_screen, Vector2.ZERO)
	_draw_top_bar_indicators()
	_draw_global_overlays()

func _draw_global_overlays() -> void:
	if nav.current_screen == "Face Home" and false:
		_draw_due_reminder_modal()

func _draw_transition() -> void:
	var t: float = _ease_transition(transition_progress)
	var overlay_offset := Vector2.ZERO
	match transition_direction:
		"menu_open":
			overlay_offset = Vector2(WIDTH * (1.0 - t), 0.0)
		"menu_close":
			overlay_offset = Vector2(WIDTH * t, 0.0)
		"clock_open":
			overlay_offset = Vector2(-WIDTH * (1.0 - t), 0.0)
		"clock_close":
			overlay_offset = Vector2(-WIDTH * t, 0.0)
		"control_open":
			overlay_offset = Vector2(0.0, -HEIGHT * (1.0 - t))
		"control_close":
			overlay_offset = Vector2(0.0, -HEIGHT * t)
		"quick_open":
			overlay_offset = Vector2(0.0, HEIGHT * (1.0 - t))
		"quick_close":
			overlay_offset = Vector2(0.0, HEIGHT * t)
		_:
			overlay_offset = Vector2(0.0, 12.0 * (1.0 - t))
	# Draw home face with transition-driven center so it exits toward the opposite side
	var face_center := _home_face_transition_center(Vector2(WIDTH * 0.5, 245.0))
	_draw_face_home_during_transition(face_center)
	_draw_overlay_screen(transition_overlay, overlay_offset)

func _ease_transition(value: float) -> float:
	var t: float = clampf(value, 0.0, 1.0)
	if transition_direction.ends_with("_close"):
		return t * t * t
	var inv: float = 1.0 - t
	return 1.0 - inv * inv * inv * inv

func _draw_screen(screen_name: String, offset: Vector2) -> void:
	draw_set_transform(offset, 0.0, Vector2.ONE)
	match screen_name:
		"Face Home":
			_draw_face_home()
		"Menu":
			_draw_face_home()
			_draw_menu()
		"Clock":
			_draw_face_home()
			_draw_clock()
		"Notification Control Center":
			_draw_face_home()
			_draw_control_center()
		"Quick Shelf":
			_draw_face_home()
			_draw_quick_shelf()
		"Diagnostics":
			_draw_diagnostics()
		"Environment":
			_draw_environment()
		"Settings":
			_draw_settings()
		"Study":
			_draw_study()
		"Reminders":
			_draw_reminders()
		"Calendar":
			_draw_calendar()
		"To Do":
			_draw_todo()
		"Games":
			_draw_games()
		"Messages":
			_draw_messages_center()
		_:
			_draw_placeholder(nav.placeholder_title if nav.placeholder_title != "" else screen_name)
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)

func _draw_overlay_screen(screen_name: String, offset: Vector2) -> void:
	draw_set_transform(offset, 0.0, Vector2.ONE)
	match screen_name:
		"Menu":
			_draw_menu()
		"Clock":
			_draw_clock()
		"Notification Control Center":
			_draw_control_center()
		"Quick Shelf":
			_draw_quick_shelf()
		"Environment":
			_draw_environment()
		"Reminders":
			_draw_reminders()
		"Calendar":
			_draw_calendar()
		"To Do":
			_draw_todo()
		"Games":
			_draw_games()
		"Messages":
			_draw_messages_center()
		_:
			_draw_placeholder(screen_name)
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)

func _font():
	return get_theme_default_font()

func _draw_text(text: String, position: Vector2, size: int = 18, color: Color = ThemeScript.TEXT) -> void:
	draw_string(_font(), position, text, HORIZONTAL_ALIGNMENT_LEFT, -1.0, size, color)

func _short_text(text: String, max_chars: int) -> String:
	if text.length() <= max_chars:
		return text
	return text.substr(0, max_chars - 1) + "…"

func _draw_centered_text(text: String, center_x: float, baseline_y: float, size: int, color: Color = ThemeScript.TEXT) -> void:
	var text_size: Vector2 = _font().get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1.0, size)
	_draw_text(text, Vector2(center_x - text_size.x * 0.5, baseline_y), size, color)

func _draw_card(rect: Rect2, color: Color = ThemeScript.TILE, radius: float = 26.0, shadow: bool = true) -> void:
	if shadow:
		_draw_rounded_rect(Rect2(rect.position + Vector2(0.0, 3.0), rect.size), Color(0.0, 0.0, 0.0, 0.22), radius)
	_draw_rounded_rect(rect, color, radius)
	_draw_rounded_outline(rect, Color(1.0, 1.0, 1.0, 0.075), radius)

func _draw_soft_panel(rect: Rect2, radius: float = 30.0) -> void:
	_draw_card(rect, ThemeScript.PANEL, radius, true)

func _draw_pill(rect: Rect2, color: Color = ThemeScript.PANEL_SOFT, active: bool = false) -> void:
	var fill: Color = ThemeScript.BLUE_SOFT if active else color
	var radius: float = minf(rect.size.y * 0.5, 20.0)
	_draw_rounded_rect(rect, fill, radius)
	_draw_rounded_outline(rect, Color(0.34, 0.62, 1.0, 0.35) if active else Color(1.0, 1.0, 1.0, 0.07), radius)

func _draw_tile(rect: Rect2, active: bool = false) -> void:
	var fill: Color = _settings_color(str(_settings_value("appearance", "tile_accent_color", "Blue")), Color(0.11, 0.32, 0.66, 1.0)) if active else Color(0.09, 0.102, 0.125, 1.0)
	_draw_card(rect, fill, 22.0, false)
	if active:
		_draw_rounded_rect(Rect2(rect.position + Vector2(0.0, 12.0), Vector2(4.0, rect.size.y - 24.0)), _settings_color(str(_settings_value("appearance", "tile_accent_color", "Blue")), ThemeScript.BLUE), 2.0)

func _draw_slider_bar(rect: Rect2, percent_value, active: bool = false) -> void:
	var percent: float = 0.0
	if percent_value != null:
		percent = clampf(float(percent_value) / 100.0, 0.0, 1.0)
	_draw_rounded_rect(rect, Color(1.0, 1.0, 1.0, 0.08), rect.size.y * 0.5)
	_draw_rounded_rect(Rect2(rect.position, Vector2(rect.size.x * percent, rect.size.y)), ThemeScript.BLUE if active else Color(0.36, 0.62, 0.96, 0.9), rect.size.y * 0.5)

func _draw_rounded_rect(rect: Rect2, color: Color, radius: float) -> void:
	var r: float = minf(radius, minf(rect.size.x, rect.size.y) * 0.5)
	var x: float = rect.position.x
	var y: float = rect.position.y
	var w: float = rect.size.x
	var h: float = rect.size.y
	draw_rect(Rect2(x + r, y, w - r * 2.0, h), color, true)
	draw_rect(Rect2(x, y + r, w, h - r * 2.0), color, true)
	draw_circle(Vector2(x + r, y + r), r, color)
	draw_circle(Vector2(x + w - r, y + r), r, color)
	draw_circle(Vector2(x + r, y + h - r), r, color)
	draw_circle(Vector2(x + w - r, y + h - r), r, color)

func _draw_rounded_outline(rect: Rect2, color: Color, radius: float) -> void:
	var r: float = minf(radius, minf(rect.size.x, rect.size.y) * 0.5)
	var x: float = rect.position.x
	var y: float = rect.position.y
	var w: float = rect.size.x
	var h: float = rect.size.y
	draw_line(Vector2(x + r, y), Vector2(x + w - r, y), color, 1.0)
	draw_line(Vector2(x + r, y + h), Vector2(x + w - r, y + h), color, 1.0)
	draw_line(Vector2(x, y + r), Vector2(x, y + h - r), color, 1.0)
	draw_line(Vector2(x + w, y + r), Vector2(x + w, y + h - r), color, 1.0)

func _draw_scrollbar(view_rect: Rect2, scroll_y: float, content_height: float) -> void:
	if content_height <= view_rect.size.y:
		return
	var track_rect: Rect2 = Rect2(view_rect.position.x + view_rect.size.x - 10.0, view_rect.position.y + 12.0, 3.0, view_rect.size.y - 24.0)
	var max_scroll: float = maxf(1.0, content_height - view_rect.size.y)
	var thumb_height: float = maxf(24.0, track_rect.size.y * view_rect.size.y / content_height)
	var thumb_y: float = track_rect.position.y + (track_rect.size.y - thumb_height) * clampf(scroll_y / max_scroll, 0.0, 1.0)
	_draw_rounded_rect(track_rect, Color(1.0, 1.0, 1.0, 0.055), 2.0)
	_draw_rounded_rect(Rect2(track_rect.position.x - 1.0, thumb_y, 5.0, thumb_height), Color(0.40, 0.55, 0.72, 0.75), 3.0)

func _draw_card_if_visible(rect: Rect2, view_rect: Rect2, color: Color, radius: float = 18.0) -> void:
	if not _rect_visible(rect, view_rect):
		return
	_draw_card(rect, color, radius, false)

func _draw_text_if_visible(text: String, position: Vector2, view_rect: Rect2, size: int, color: Color) -> void:
	if position.y < view_rect.position.y + 8.0 or position.y > view_rect.position.y + view_rect.size.y - 8.0:
		return
	_draw_text(text, position, size, color)

func _rect_visible(rect: Rect2, view_rect: Rect2) -> bool:
	return rect.position.y + rect.size.y >= view_rect.position.y and rect.position.y <= view_rect.position.y + view_rect.size.y

func _draw_face_home() -> void:
	if home_message_active:
		_draw_home_message_mode()
	else:
		face.draw_face(self, Vector2(WIDTH, HEIGHT), elapsed, _settings_color(str(_settings_value("appearance", "eye_color", "Blue")), Color(0.18, 0.58, 1.0, 1.0)), _settings_color(str(_settings_value("appearance", "mouth_color", "Blue")), Color(0.18, 0.58, 1.0, 0.95)))
		_draw_study_timer_overlay()

func _draw_face_home_during_transition(face_center: Vector2) -> void:
	# Used by _draw_transition: draws home face at a transition-adjusted center.
	# The face renderer uses transition center in transition draw — face is not drawn over completed non-Home screens.
	if home_message_active:
		_draw_home_message_mode()
	else:
		var eye_color := _settings_color(str(_settings_value("appearance", "eye_color", "Blue")), Color(0.18, 0.58, 1.0, 1.0))
		var mouth_color := _settings_color(str(_settings_value("appearance", "mouth_color", "Blue")), Color(0.18, 0.58, 1.0, 0.95))
		face.draw_face_at(self, face_center, HOME_MESSAGE_FACE_IDLE_SCALE, elapsed, eye_color, mouth_color)
		_draw_study_timer_overlay()

func _draw_startup_sequence() -> void:
	draw_rect(Rect2(0, 0, WIDTH, HEIGHT), Color(0.0, 0.0, 0.0, 1.0), true)
	_draw_startup_brand()
	_draw_startup_face()
	var status_alpha := _startup_alpha(4.20, 0.35)
	if status_alpha > 0.0:
		var status := "Systems ready" if startup_check_done else "Starting local systems..."
		_draw_centered_text(status, WIDTH * 0.5, 430.0, 12, Color(0.54, 0.60, 0.68, 0.45 * status_alpha))

func _draw_startup_brand() -> void:
	var move_t := _startup_ease(2.45, 1.75)
	var brand_y := lerpf(190.0, 96.0, move_t)
	var dev_y := lerpf(238.0, 136.0, move_t)
	var nexa_alpha := _startup_alpha(0.45, 1.00)
	var totem_alpha := _startup_alpha(1.15, 0.95)
	var dev_alpha := _startup_alpha(1.75, 0.95)
	var nexa_size := 46
	var totem_size := 36
	var nexa_text := "NeXa"
	var totem_text := "ToTem"
	var nexa_w := _font().get_string_size(nexa_text, HORIZONTAL_ALIGNMENT_LEFT, -1.0, nexa_size).x
	var total_w := nexa_w + 12.0 + _font().get_string_size(totem_text, HORIZONTAL_ALIGNMENT_LEFT, -1.0, totem_size).x
	var start_x := WIDTH * 0.5 - total_w * 0.5
	_draw_text(nexa_text, Vector2(start_x, brand_y), nexa_size, Color(0.94, 0.93, 0.88, nexa_alpha))
	_draw_text(totem_text, Vector2(start_x + nexa_w + 12.0, brand_y - 2.0), totem_size, Color(0.62, 0.66, 0.72, totem_alpha))
	_draw_centered_text("DevDul", WIDTH * 0.5, dev_y, 15, Color(0.48, 0.53, 0.60, dev_alpha))

func _draw_startup_face() -> void:
	var slide_t := _startup_ease(2.45, 1.75)
	if slide_t <= 0.0:
		return
	var eye_color := _settings_color(str(_settings_value("appearance", "eye_color", "Blue")), Color(0.18, 0.58, 1.0, 1.0))
	var mouth_color := _settings_color(str(_settings_value("appearance", "mouth_color", "Blue")), Color(0.18, 0.58, 1.0, 0.95))
	var center_y := lerpf(590.0, 285.0, slide_t)
	face.draw_face_at(self, Vector2(320.0, center_y), 0.82, elapsed, eye_color, mouth_color)

func _draw_reminder_top_badge() -> void:
	var count := notifications_data.size()
	if count <= 0:
		return
	_draw_pill(Rect2(466, 30, 54, 24), Color(0.16, 0.10, 0.05, 0.94), true)
	_draw_centered_text("!" + str(count), 493.0, 47.0, 11, ThemeScript.TEXT)

func _draw_home_message_mode() -> void:
	# Layout: face LEFT side (x=0..320), text RIGHT side (x=342..606). No container, no border.
	draw_rect(Rect2(0, 0, WIDTH, HEIGHT), Color(0.0, 0.0, 0.0, 1.0), true)
	var eye_color := _settings_color(str(_settings_value("appearance", "eye_color", "Blue")), Color(0.18, 0.58, 1.0, 1.0))
	var mouth_color := _settings_color(str(_settings_value("appearance", "mouth_color", "Blue")), Color(0.18, 0.58, 1.0, 0.95))
	# Face smoothly lerps from idle center to right-side message center
	var face_center := _home_message_face_center()
	var face_scale := _home_message_face_scale()
	face.draw_face_at(self, face_center, face_scale, elapsed, eye_color, mouth_color)
	# Text enters from top (-180 offset -> 0) and exits upward (0 -> -180)
	var text_rect := _home_message_text_rect()
	var lines := _home_message_lines()
	var content_height := _home_message_content_height()
	var text_y_off := _home_message_text_y_offset()
	var text_alpha := _home_message_text_alpha()
	var y := text_rect.position.y
	if lines.size() <= 5:
		y = text_rect.position.y + maxf(0.0, (text_rect.size.y - content_height) * 0.5)
	else:
		y -= home_message_scroll_y
	for index in range(lines.size()):
		var line := str(lines[index])
		var size := FONT_SIZE_MESSAGE_TITLE if index == 0 else FONT_SIZE_MESSAGE_BODY
		var color := ThemeScript.TEXT if index == 0 else ThemeScript.TEXT_MUTED
		color.a *= text_alpha
		var baseline := y + text_y_off + float(index) * 24.0 + float(size)
		if baseline >= text_rect.position.y - 30.0 and baseline <= text_rect.position.y + text_rect.size.y + 30.0:
			_draw_text(line, Vector2(text_rect.position.x, baseline), size, color)
	if _home_message_max_scroll() > 0.0:
		var thumb_h := maxf(26.0, text_rect.size.y * text_rect.size.y / _home_message_content_height())
		var thumb_y := text_rect.position.y + (text_rect.size.y - thumb_h) * clampf(home_message_scroll_y / _home_message_max_scroll(), 0.0, 1.0)
		_draw_rounded_rect(Rect2(text_rect.position.x + text_rect.size.x + 8.0, thumb_y, 3, thumb_h), Color(1.0, 1.0, 1.0, 0.14 * text_alpha), 2.0)
	# Actions sit at bottom of text (left) side
	for index in range(home_message_actions.size()):
		var action: Dictionary = home_message_actions[index] as Dictionary
		var action_rect := _home_message_action_rect(index)
		action_rect.position.y += text_y_off
		_draw_button(action_rect, str(action.get("label", "Open")), index == 0)
	# Close X near top-right of text area, moves with text animation
	var close_rect := _home_message_close_rect()
	close_rect.position.y += text_y_off
	_draw_circular_close_button(close_rect)

func _draw_top_bar_indicators() -> void:
	if nav.current_screen == "Games":
		return
	_update_message_indicator_count()
	notification_indicator_count = notifications_data.size()
	_draw_hardware_status_indicator()
	if nav.current_screen == "Face Home":
		_draw_home_clock()
	if nav.current_screen == "Face Home" and not home_message_active and nexa_message_indicator_count <= 0 and notification_indicator_count <= 0:
		return
	if nexa_message_indicator_count > 0:
		_draw_message_indicator(_message_indicator_rect(), nexa_message_indicator_count)
	if notification_indicator_count > 0:
		_draw_notification_indicator(_notification_indicator_rect(), notification_indicator_count)

func _hardware_status_label() -> String:
	if hardware_connected and not hardware_stale:
		return "Local network connected"
	return "Local network disconnected"

func _hardware_status_color() -> Color:
	if hardware_connected and not hardware_stale:
		return Color(0.32, 0.86, 0.52, 0.92)
	return Color(0.96, 0.34, 0.34, 0.90)

func _draw_hardware_status_indicator() -> void:
	var color := _hardware_status_color()
	draw_circle(Vector2(17.0, 19.0), 4.0, color)
	_draw_text(_hardware_status_label(), Vector2(28.0, 23.0), 11, Color(color.r, color.g, color.b, 0.92))

func _draw_message_indicator(rect: Rect2, count: int) -> void:
	var color := Color(0.34, 0.62, 1.0, 0.92)
	_draw_rounded_outline(Rect2(rect.position.x + 3.0, rect.position.y + 5.0, 20.0, 15.0), color, 5.0)
	draw_line(Vector2(rect.position.x + 10.0, rect.position.y + 20.0), Vector2(rect.position.x + 7.0, rect.position.y + 24.0), color, 1.0)
	draw_circle(Vector2(rect.position.x + 13.0, rect.position.y + 12.5), 2.0, color)
	_draw_indicator_badge(rect, count, color)

func _draw_notification_indicator(rect: Rect2, count: int) -> void:
	var color := Color(0.92, 0.94, 0.96, 0.86)
	draw_line(Vector2(rect.position.x + 10.0, rect.position.y + 19.0), Vector2(rect.position.x + 20.0, rect.position.y + 19.0), color, 1.4)
	draw_line(Vector2(rect.position.x + 11.0, rect.position.y + 19.0), Vector2(rect.position.x + 11.0, rect.position.y + 11.0), color, 1.4)
	draw_line(Vector2(rect.position.x + 19.0, rect.position.y + 19.0), Vector2(rect.position.x + 19.0, rect.position.y + 11.0), color, 1.4)
	draw_circle(Vector2(rect.position.x + 15.0, rect.position.y + 10.0), 4.0, color)
	draw_circle(Vector2(rect.position.x + 15.0, rect.position.y + 22.0), 2.0, color)
	_draw_indicator_badge(rect, count, color)

func _draw_indicator_badge(rect: Rect2, count: int, color: Color) -> void:
	var label := "9+" if count > 9 else str(count)
	var badge := Rect2(rect.position.x + 14.0, rect.position.y - 1.0, 20.0, 14.0)
	_draw_rounded_rect(badge, Color(color.r, color.g, color.b, 0.95), 7.0)
	_draw_centered_text(label, badge.position.x + badge.size.x * 0.5, badge.position.y + 10.5, 8, Color(0.02, 0.025, 0.032, 1.0))

func _draw_home_clock() -> void:
	var now := Time.get_datetime_dict_from_system()
	var label := "%02d:%02d" % [int(now.hour), int(now.minute)]
	var rect := _home_clock_rect()
	_draw_text(label, Vector2(rect.position.x + 5.0, rect.position.y + 17.0), 14, Color(0.58, 0.66, 0.78, 0.78))

func _draw_circular_close_button(rect: Rect2) -> void:
	var center := rect.position + rect.size * 0.5
	draw_circle(center, rect.size.x * 0.5, Color(0.05, 0.06, 0.075, 0.72))
	draw_arc(center, rect.size.x * 0.5 - 0.5, 0.0, TAU, 24, Color(0.72, 0.76, 0.82, 0.45), 1.0)
	draw_line(center + Vector2(-4.5, -4.5), center + Vector2(4.5, 4.5), Color(0.82, 0.85, 0.90, 0.85), 1.3)
	draw_line(center + Vector2(4.5, -4.5), center + Vector2(-4.5, 4.5), Color(0.82, 0.85, 0.90, 0.85), 1.3)

func _draw_due_reminder_modal() -> void:
	if notifications_data.is_empty():
		return
	var notification: Dictionary = notifications_data[0] as Dictionary
	var rect := Rect2(128, 188, 384, 190)
	_draw_rounded_rect(rect, Color(0.045, 0.052, 0.064, 0.98), 22.0)
	_draw_rounded_outline(rect, Color(1.0, 1.0, 1.0, 0.10), 22.0)
	var modal_title := "Calendar" if str(notification.get("type", "")) == "calendar" else ("To Do Reminder" if str(notification.get("type", "")) == "todo" else "Reminder")
	_draw_centered_text(modal_title, 320.0, 224.0, 18, ThemeScript.TEXT)
	var title := str(notification.get("body", "Reminder"))
	_draw_centered_text(_short_text(title, 38), 320.0, 258.0, 15, ThemeScript.TEXT)
	_draw_centered_text(_short_text(str(notification.get("subtitle", "")), 38), 320.0, 282.0, 11, ThemeScript.TEXT_MUTED)
	_draw_button(Rect2(164, 324, 96, 34), "Done" if modal_title == "Calendar" or modal_title == "To Do Reminder" else "Dismiss", false)
	_draw_button(Rect2(272, 324, 112, 34), "Snooze 10m" if modal_title == "Calendar" or modal_title == "To Do Reminder" else "Snooze +5m", false)
	_draw_button(Rect2(396, 324, 96, 34), "Open", false)

func _draw_study_timer_overlay() -> void:
	if not bool(study_timer_data.get("active", false)):
		return
	var remaining: int = int(study_timer_data.get("remaining_seconds", 0))
	var planned: int = max(1, int(study_timer_data.get("planned_seconds", 1)))
	var percent: float = float(remaining) / float(planned)
	var color := Color(0.20, 0.78, 0.36, 0.94)
	if percent <= 0.05:
		color = Color(1.0, 0.22, 0.22, 0.94)
	elif percent <= 0.30:
		color = Color(1.0, 0.76, 0.20, 0.94)
	elif percent <= 0.50:
		color = Color(0.18, 0.58, 1.0, 0.94)
	var kind := str(study_timer_data.get("kind", "focus")).capitalize()
	var label: String = kind + ": %02d:%02d" % [int(remaining / 60), remaining % 60]
	_draw_text(label, Vector2(28, 48), 12, color)

func _settings_color(name: String, fallback: Color) -> Color:
	var colors: Dictionary = {
		"Blue": Color(0.18, 0.58, 1.0, 1.0),
		"Sky Blue": Color(0.42, 0.72, 1.0, 1.0),
		"Cyan": Color(0.1, 0.82, 0.92, 1.0),
		"White": Color(0.93, 0.96, 1.0, 1.0),
		"Warm White": Color(1.0, 0.88, 0.68, 1.0),
		"Yellow": Color(1.0, 0.86, 0.24, 1.0),
		"Orange": Color(1.0, 0.48, 0.18, 1.0),
		"Red": Color(1.0, 0.22, 0.22, 1.0),
		"Pink": Color(1.0, 0.45, 0.74, 1.0),
		"Purple": Color(0.64, 0.42, 1.0, 1.0),
		"Green": Color(0.24, 0.78, 0.36, 1.0),
		"Mint": Color(0.42, 0.92, 0.72, 1.0),
		"Brown": Color(0.58, 0.38, 0.24, 1.0),
		"Gold": Color(1.0, 0.68, 0.22, 1.0),
		"Grey": Color(0.58, 0.62, 0.68, 1.0),
		"Graphite": Color(0.24, 0.26, 0.30, 1.0),
		"Black": Color(0.04, 0.045, 0.052, 1.0)
	}
	var value = colors.get(name, fallback)
	if value is Color:
		return value
	return fallback

func _theme_background_color() -> Color:
	var name: String = str(_settings_value("appearance", "background_color", "Black"))
	if name == "Black":
		return ThemeScript.BACKGROUND
	var base: Color = _settings_color(name, ThemeScript.BACKGROUND)
	return Color(base.r * 0.16, base.g * 0.16, base.b * 0.16, 1.0)

func _draw_menu() -> void:
	draw_rect(Rect2(Vector2.ZERO, Vector2(WIDTH, HEIGHT)), _theme_background_color(), true)
	_draw_text("Menu", Vector2(32, 52), 27, ThemeScript.TEXT)
	for index in range(MENU_TILES.size()):
		var rect: Rect2 = _menu_tile_rect(index)
		var tile: Dictionary = MENU_TILES[index] as Dictionary
		var active := index == hardware_menu_focus_index
		_draw_tile(rect, active)
		_draw_text(str(tile["icon"]), rect.position + Vector2(18, 45), 22, ThemeScript.BLUE if active else ThemeScript.TEXT)
		_draw_text(str(tile["title"]), rect.position + Vector2(58, 30), 17, ThemeScript.TEXT)
		_draw_text(str(tile["subtitle"]), rect.position + Vector2(58, 52), 11, ThemeScript.TEXT_MUTED)

func _menu_tile_rect(index: int) -> Rect2:
	var column: int = index % 2
	var row: int = int(index / 2)
	return Rect2(28.0 + float(column) * 300.0, 92.0 + float(row) * 76.0, 284.0, 72.0)

func _draw_clock() -> void:
	draw_rect(Rect2(Vector2.ZERO, Vector2(WIDTH, HEIGHT)), _theme_background_color(), true)
	var now: Dictionary = Time.get_datetime_dict_from_system()
	var hour_text: String = "%02d" % now.hour
	var minute_text: String = "%02d" % now.minute
	var second_text: String = "%02d" % now.second
	var day_text: String = "%02d" % now.day
	var month_text: String = "%02d" % now.month
	var year_text: String = "%04d" % now.year
	var hour_color: Color = _settings_color(str(_settings_value("appearance", "hour_color", "White")), Color(0.93, 0.96, 1.0, 1.0))
	var minute_color: Color = _settings_color(str(_settings_value("appearance", "minute_color", "White")), Color(0.93, 0.96, 1.0, 1.0))
	var second_color: Color = _settings_color(str(_settings_value("appearance", "second_color", "Grey")), Color(0.58, 0.62, 0.68, 1.0))
	var day_color: Color = _settings_color(str(_settings_value("appearance", "day_color", "Grey")), Color(0.58, 0.62, 0.68, 1.0))
	var month_color: Color = _settings_color(str(_settings_value("appearance", "month_color", "Grey")), Color(0.58, 0.62, 0.68, 1.0))
	var year_color: Color = _settings_color(str(_settings_value("appearance", "year_color", "Grey")), Color(0.58, 0.62, 0.68, 1.0))
	_draw_centered_segments([
		{"text": hour_text, "size": 76, "color": hour_color},
		{"text": " : ", "size": 52, "color": Color(0.58, 0.70, 0.88, 0.76)},
		{"text": minute_text, "size": 76, "color": minute_color},
		{"text": " : ", "size": 42, "color": Color(0.58, 0.70, 0.88, 0.64)},
		{"text": second_text, "size": 46, "color": second_color}
	], WIDTH * 0.5, 226.0)
	_draw_centered_segments([
		{"text": day_text, "size": 22, "color": day_color},
		{"text": " / ", "size": 18, "color": Color(0.44, 0.54, 0.68, 0.72)},
		{"text": month_text, "size": 22, "color": month_color},
		{"text": " / ", "size": 18, "color": Color(0.44, 0.54, 0.68, 0.72)},
		{"text": year_text, "size": 22, "color": year_color}
	], WIDTH * 0.5, 280.0)
	draw_circle(Vector2(320, 332), 8.0, Color(0.18, 0.58, 1.0, 0.82))
	# Future clock settings: show time on face, show date on face, auto show clock screen.
	# Future timing settings: show clock every X minutes, show clock duration seconds.

func _draw_centered_segments(segments: Array, center_x: float, baseline_y: float) -> void:
	var total_width := 0.0
	for raw_segment in segments:
		var segment: Dictionary = raw_segment as Dictionary
		total_width += _font().get_string_size(str(segment.get("text", "")), HORIZONTAL_ALIGNMENT_LEFT, -1.0, int(segment.get("size", 18))).x
	var cursor_x: float = center_x - total_width * 0.5
	for raw_segment in segments:
		var segment: Dictionary = raw_segment as Dictionary
		var text: String = str(segment.get("text", ""))
		var size: int = int(segment.get("size", 18))
		var color: Color = segment.get("color", ThemeScript.TEXT)
		_draw_text(text, Vector2(cursor_x, baseline_y), size, color)
		cursor_x += _font().get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1.0, size).x

func _draw_environment() -> void:
	draw_rect(Rect2(Vector2.ZERO, Vector2(WIDTH, HEIGHT)), _theme_background_color(), true)
	_draw_text("Environment", Vector2(44, 58), 27, ThemeScript.TEXT)
	_draw_button(Rect2(520, 22, 92, 34), "Home", false)
	if not hardware_connected or hardware_stale or hardware_state_data.is_empty():
		_draw_soft_panel(Rect2(64, 144, 512, 184), 28.0)
		_draw_centered_text("Waiting for ESP8266 sensor data...", 320.0, 210.0, 18, ThemeScript.TEXT)
		var message := "Sensor data is stale." if hardware_stale and hardware_last_seen_at != "" else "Local network disconnected"
		_draw_centered_text(message, 320.0, 242.0, 13, Color(0.96, 0.42, 0.42, 0.92))
		_draw_centered_text("Waiting for live update...", 320.0, 270.0, 12, ThemeScript.TEXT_MUTED)
		return
	var air_status := str(hardware_state_data.get("air_status", "UNKNOWN"))
	var accent := Color(0.30, 0.88, 0.52, 0.95)
	if air_status == "VENTILATE":
		accent = Color(1.0, 0.66, 0.24, 0.95)
	var cards: Array = [
		{"title": "Temperature", "value": _hardware_value("temperature_c", "°C")},
		{"title": "Humidity", "value": _hardware_value("humidity_percent", "%")},
		{"title": "Pressure", "value": _hardware_value("pressure_hpa", " hPa")},
		{"title": "Gas resistance", "value": _hardware_value("gas_kohms", " kΩ")},
		{"title": "Air status", "value": air_status.capitalize()},
		{"title": "Advice", "value": str(hardware_state_data.get("advice", "Waiting for live data"))}
	]
	for index in range(cards.size()):
		var rect := Rect2(44.0 + float(index % 2) * 276.0, 112.0 + float(int(index / 2)) * 80.0, 252.0, 64.0)
		var item: Dictionary = cards[index] as Dictionary
		_draw_tile(rect, false)
		_draw_text(str(item["title"]), rect.position + Vector2(14, 22), 11, ThemeScript.TEXT_MUTED)
		_draw_text(_short_text(str(item["value"]), 26), rect.position + Vector2(14, 48), 18 if index < 4 else 15, accent if index >= 4 else ThemeScript.TEXT)
	_draw_text("Last seen " + hardware_last_seen_at, Vector2(48, 392), 11, ThemeScript.TEXT_MUTED)

func _hardware_value(key: String, suffix: String) -> String:
	var value = hardware_state_data.get(key, null)
	if value == null:
		return "Waiting"
	return str(value) + suffix

func _draw_control_center() -> void:
	if CONTROL_CENTER_SAFE_MODE:
		_draw_control_center_safe()
		return
	_draw_soft_panel(Rect2(20, 20, 600, 440), 30.0)
	_draw_text("Control Center", Vector2(44, 64), 26, ThemeScript.TEXT)
	_draw_pill(Rect2(44, 82, 104, 26), Color(0.10, 0.16, 0.12, 1.0), false)
	_draw_text("System OK", Vector2(60, 100), 12, ThemeScript.OK)
	var controls: Array = [
		{"title": "Brightness", "value": str(brightness_percent) + "%"},
		{"title": "Sound", "value": str(sound_percent) + "%"},
		{"title": "Quiet Mode", "value": "On" if bool(control_center_data.get("quiet_mode", false)) else "Off"},
		{"title": "Wi-Fi", "value": str(control_center_data.get("connected_ssid", "Unknown"))},
		{"title": "Remote", "value": str(control_center_data.get("remote_network_state", "planned"))},
		{"title": "Diagnostics", "value": "Open"}
	]
	for index in range(controls.size()):
		var rect: Rect2 = Rect2(44.0 + float(index % 3) * 184.0, 124.0 + float(int(index / 3)) * 76.0, 164.0, 62.0)
		var item: Dictionary = controls[index] as Dictionary
		var active: bool = item["title"] == "Diagnostics" or (item["title"] == "Quiet Mode" and bool(control_center_data.get("quiet_mode", false))) or (item["title"] == "Remote" and control_center_data.get("remote_network_state", "planned") == "on")
		_draw_tile(rect, active)
		_draw_text(str(item["title"]), rect.position + Vector2(14, 27), 15, ThemeScript.TEXT)
		_draw_text(str(item["value"]), rect.position + Vector2(14, 48), 11, ThemeScript.TEXT_MUTED)
		if item["title"] == "Brightness":
			_draw_slider_bar(Rect2(rect.position.x + 14.0, rect.position.y + 50.0, 132.0, 5.0), brightness_percent, active)
		elif item["title"] == "Sound":
			_draw_slider_bar(Rect2(rect.position.x + 14.0, rect.position.y + 50.0, 132.0, 5.0), sound_percent, active)
	_draw_control_detail()
	_draw_notifications_section()
	if notification_detail_modal_open:
		_draw_notification_detail_modal()
	var control_view: Rect2 = _control_scroll_rect()
	_draw_scrollbar(control_view, control_center_scroll_y, _control_center_content_height())

func _draw_control_center_safe() -> void:
	# Pi-safe Control Center: fixed visible content, no scroll pass, no shadows,
	# no detail card during slide transition, and only cheap rounded rectangles.
	_draw_rounded_rect(Rect2(20, 20, 600, 440), Color(0.055, 0.062, 0.075, 1.0), 26.0)
	_draw_rounded_outline(Rect2(20, 20, 600, 440), Color(1.0, 1.0, 1.0, 0.07), 26.0)
	_draw_text("Control Center", Vector2(44, 62), 25, ThemeScript.TEXT)
	_draw_text(api_status_text if not api_online else "System OK", Vector2(46, 88), 11, ThemeScript.TEXT_MUTED)
	var controls: Array = [
		{"title": "Brightness", "value": str(brightness_percent) + "%"},
		{"title": "Sound", "value": str(sound_percent) + "%"},
		{"title": "Quiet Mode", "value": "On" if quiet_mode_local else "Off"},
		{"title": "Wi-Fi", "value": str(control_center_data.get("connected_ssid", "Unknown"))},
		{"title": "Remote", "value": remote_network_local},
		{"title": "Diagnostics", "value": "Open"}
	]
	for index in range(controls.size()):
		var rect: Rect2 = Rect2(44.0 + float(index % 3) * 184.0, 118.0 + float(int(index / 3)) * 80.0, 164.0, 66.0)
		var item: Dictionary = controls[index] as Dictionary
		var active: bool = selected_control_detail == str(item["title"]).to_lower() or (item["title"] == "Wi-Fi" and selected_control_detail == "wifi") or item["title"] == "Diagnostics" or (item["title"] == "Quiet Mode" and quiet_mode_local) or (item["title"] == "Remote" and remote_network_local == "on")
		var fill: Color = Color(0.10, 0.29, 0.58, 1.0) if active else Color(0.085, 0.095, 0.112, 1.0)
		_draw_rounded_rect(rect, fill, 18.0)
		_draw_rounded_outline(rect, Color(1.0, 1.0, 1.0, 0.08), 18.0)
		_draw_text(str(item["title"]), rect.position + Vector2(14, 25), 14, ThemeScript.TEXT)
		_draw_text(str(item["value"]), rect.position + Vector2(14, 44), 11, ThemeScript.TEXT_MUTED)
		if item["title"] == "Brightness":
			_draw_slider_bar(Rect2(rect.position.x + 14.0, rect.position.y + 52.0, 132.0, 5.0), brightness_percent, active)
		elif item["title"] == "Sound":
			_draw_slider_bar(Rect2(rect.position.x + 14.0, rect.position.y + 52.0, 132.0, 5.0), sound_percent, active)
	if not transition_active:
		if selected_control_detail == "wifi":
			_draw_wifi_detail_safe()
		else:
			_draw_control_detail_safe()
			_draw_notifications_section_safe()
	if notification_detail_modal_open:
		_draw_notification_detail_modal()

func _draw_control_detail_safe() -> void:
	if selected_control_detail == "":
		return
	var rect: Rect2 = Rect2(44, 420, 552, 28)
	_draw_rounded_rect(rect, Color(0.075, 0.085, 0.105, 1.0), 14.0)
	var label := "Ready"
	if selected_control_detail == "brightness":
		label = "Brightness " + str(brightness_percent) + "% · Auto planned"
	elif selected_control_detail == "sound":
		label = "Sound " + str(sound_percent) + "% · " + str(control_center_data.get("speaker_name", "Unknown"))
	elif selected_control_detail == "wifi":
		label = "Wi-Fi " + str(control_center_data.get("connected_ssid", "Unknown")) + " · Connect planned"
	elif selected_control_detail == "remote":
		label = "Remote " + remote_network_local + " · dry-run"
	_draw_text(label, rect.position + Vector2(14, 19), 11, ThemeScript.TEXT_MUTED)

func _draw_wifi_detail_safe() -> void:
	var rect: Rect2 = Rect2(44, 292, 552, 156)
	_draw_rounded_rect(rect, Color(0.075, 0.085, 0.105, 1.0), 18.0)
	_draw_rounded_outline(rect, Color(1.0, 1.0, 1.0, 0.07), 18.0)
	var connected_value: String = str(network_detail_data.get("connected_ssid", control_center_data.get("connected_ssid", "Pending")))
	if connected_value == "" or connected_value == "<null>":
		connected_value = "Unknown"
	_draw_text("Wi-Fi details", rect.position + Vector2(14, 24), 14, ThemeScript.TEXT)
	_draw_text("Connected: " + connected_value, rect.position + Vector2(14, 45), 11, ThemeScript.TEXT_MUTED)
	_draw_text("Saved", rect.position + Vector2(14, 72), 12, ThemeScript.TEXT)
	_draw_text("Available", rect.position + Vector2(282, 72), 12, ThemeScript.TEXT)
	var saved_raw = network_detail_data.get("saved_networks", [])
	var saved: Array = []
	if saved_raw is Array:
		saved = saved_raw
	var available_raw = network_detail_data.get("available_networks", [])
	var available: Array = []
	if available_raw is Array:
		available = available_raw
	for index in range(3):
		var saved_label: String = "Pending" if network_detail_pending else "None found"
		if index < saved.size():
			saved_label = _short_text(str(saved[index]), 22)
		var available_label: String = "Pending" if network_detail_pending else "Unavailable"
		if index < available.size():
			available_label = _short_text(str(available[index]), 22)
		_draw_text(saved_label, rect.position + Vector2(14, 93 + index * 16), 10, ThemeScript.TEXT_MUTED)
		_draw_text(available_label, rect.position + Vector2(282, 93 + index * 16), 10, ThemeScript.TEXT_MUTED)
	_draw_text("Action: Connect planned · dry-run", rect.position + Vector2(14, 143), 10, ThemeScript.TEXT_DIM)

func _draw_notifications_section_safe() -> void:
	_draw_text("Notifications", Vector2(46, 300), 18, ThemeScript.TEXT)
	var list_rect := _notification_scroll_rect()
	_draw_rounded_rect(list_rect, Color(0.060, 0.068, 0.082, 0.96), 12.0)
	if notifications_data.is_empty():
		_draw_centered_text("No notifications", list_rect.position.x + list_rect.size.x * 0.5, list_rect.position.y + list_rect.size.y * 0.5 + 5.0, 13, ThemeScript.TEXT_MUTED)
		return
	for index in range(notifications_data.size()):
		var rect := _notification_row_rect(index)
		if _notification_row_visible(rect):
			_draw_notification_row(rect, notifications_data[index] as Dictionary, index)
	_draw_scrollbar(list_rect, notification_scroll_y, _notification_content_height())

func _draw_notifications_section() -> void:
	_draw_text("Notifications", Vector2(46, 292), 20, ThemeScript.TEXT)
	var list_rect := _notification_scroll_rect()
	_draw_rounded_rect(list_rect, Color(0.060, 0.068, 0.082, 0.96), 12.0)
	if notifications_data.is_empty():
		_draw_centered_text("No notifications", list_rect.position.x + list_rect.size.x * 0.5, list_rect.position.y + list_rect.size.y * 0.5 + 5.0, 13, ThemeScript.TEXT_MUTED)
		return
	for index in range(notifications_data.size()):
		var rect := _notification_row_rect(index)
		if _notification_row_visible(rect):
			_draw_notification_row(rect, notifications_data[index] as Dictionary, index)
	_draw_scrollbar(list_rect, notification_scroll_y, _notification_content_height())

func _notification_row_rect(index: int) -> Rect2:
	return Rect2(52, 326 + float(index) * 48.0 - notification_scroll_y, 536, 40)

func _notification_row_visible(rect: Rect2) -> bool:
	var view_rect := _notification_scroll_rect()
	return rect.position.y >= view_rect.position.y + 4.0 and rect.position.y + rect.size.y <= view_rect.position.y + view_rect.size.y - 4.0

func _notification_delete_rect(index: int) -> Rect2:
	var row := _notification_row_rect(index)
	return Rect2(row.position.x + row.size.x - 42.0, row.position.y + 8.0, 28.0, 24.0)

func _draw_notification_row(rect: Rect2, notification: Dictionary, index: int) -> void:
	_draw_rounded_rect(rect, Color(0.078, 0.087, 0.104, 1.0), 16.0)
	_draw_rounded_outline(rect, Color(1.0, 1.0, 1.0, 0.06), 16.0)
	var accent := ThemeScript.WARNING if bool(notification.get("requires_pin", false)) else ThemeScript.BLUE
	_draw_pill(Rect2(rect.position.x + 12.0, rect.position.y + 8.0, 76.0, 22.0), Color(0.08, 0.12, 0.18, 0.92), false)
	_draw_text(_short_text(str(notification.get("title", "Reminder")), 12), rect.position + Vector2(24, 25), 10, accent)
	_draw_text(_short_text(str(notification.get("body", "")), 32), rect.position + Vector2(104, 20), 12, ThemeScript.TEXT)
	_draw_text(_short_text(str(notification.get("subtitle", "")), 34), rect.position + Vector2(104, 35), 9, ThemeScript.TEXT_MUTED)
	var delete_rect := _notification_delete_rect(index)
	_draw_rounded_rect(delete_rect, Color(0.18, 0.08, 0.08, 0.92), 10.0)
	_draw_centered_text("X", delete_rect.position.x + delete_rect.size.x * 0.5, delete_rect.position.y + 17.0, 11, ThemeScript.TEXT)

func _draw_notification_detail_modal() -> void:
	if notification_selected.is_empty():
		return
	var rect := Rect2(84, 150, 472, 230)
	_draw_rounded_rect(rect, Color(0.045, 0.052, 0.064, 0.99), 22.0)
	_draw_rounded_outline(rect, Color(1.0, 1.0, 1.0, 0.12), 22.0)
	var locked := bool(notification_selected.get("requires_pin", false))
	var title := "Private reminder locked" if locked else str(notification_selected.get("title", "Reminder"))
	var body := "Private reminder locked" if locked else str(notification_selected.get("body", "Reminder"))
	var subtitle := "Enter PIN to view" if locked else str(notification_selected.get("subtitle", ""))
	_draw_centered_text(_short_text(title, 42), 320.0, 190.0, 18, ThemeScript.TEXT)
	_draw_centered_text(_short_text(body, 54), 320.0, 232.0, 15, ThemeScript.TEXT)
	_draw_centered_text(_short_text(subtitle, 54), 320.0, 260.0, 11, ThemeScript.TEXT_MUTED)
	_draw_button(Rect2(104, 354, 120, 34), "Close", false)
	_draw_button(Rect2(260, 354, 120, 34), "Done" if str(notification_selected.get("type", "")) == "todo" else "Dismiss", false)
	_draw_button(Rect2(416, 354, 120, 34), "Open", false)

func _draw_notification_safe(rect: Rect2, label: String, message: String) -> void:
	_draw_rounded_rect(rect, Color(0.078, 0.087, 0.104, 1.0), 16.0)
	_draw_text(label, rect.position + Vector2(14, 25), 11, ThemeScript.TEXT_MUTED)
	_draw_text(_short_text(message, 42), rect.position + Vector2(148, 25), 12, ThemeScript.TEXT)

func _reminders_latest_due_label() -> String:
	var due_raw = reminders_due_data.get("due", [])
	if due_raw is Array and not due_raw.is_empty():
		var item: Dictionary = due_raw[0] as Dictionary
		return _short_text(str(item.get("title", "Reminder")), 30)
	return "Next " + str(reminders_data.get("next_due_at", "none"))

func _draw_control_detail() -> void:
	if selected_control_detail == "":
		return
	var rect: Rect2 = Rect2(222, 76, 374, 42)
	_draw_card(rect, Color(0.075, 0.085, 0.105, 0.98), 17.0, false)
	var label: String = selected_control_detail + " details"
	if selected_control_detail == "wifi":
		label = "Connected: " + str(control_center_data.get("connected_ssid", "Unknown")) + " · Connect planned"
	elif selected_control_detail == "remote":
		label = "Remote: " + remote_network_local + " · dry-run"
	elif selected_control_detail == "sound":
		label = "Speaker: " + str(control_center_data.get("speaker_name", "Unknown"))
		_draw_text("Volume " + str(sound_percent) + "% · Muted " + str(control_center_data.get("muted", "Unknown")), rect.position + Vector2(14, 34), 10, ThemeScript.TEXT_DIM)
	elif selected_control_detail == "brightness":
		label = "Brightness: " + str(brightness_percent) + "% · Auto planned"
	_draw_text(label, rect.position + Vector2(14, 22), 12, ThemeScript.TEXT_MUTED)

func _draw_notification(rect: Rect2, label: String, message: String, view_rect: Rect2) -> void:
	if rect.position.y + rect.size.y < view_rect.position.y or rect.position.y > view_rect.position.y + view_rect.size.y:
		return
	_draw_card(rect, Color(0.09, 0.10, 0.12, 0.96), 20.0, false)
	_draw_pill(Rect2(rect.position.x + 12.0, rect.position.y + 8.0, 82.0, 22.0), Color(0.08, 0.12, 0.18, 0.92), label == "Private")
	_draw_text(label, rect.position + Vector2(26, 25), 11, ThemeScript.TEXT_MUTED)
	_draw_text(message, rect.position + Vector2(116, 25), 14, ThemeScript.TEXT)

func _draw_diagnostics() -> void:
	draw_rect(Rect2(Vector2.ZERO, Vector2(WIDTH, HEIGHT)), _theme_background_color(), true)
	_draw_text("Diagnostics", Vector2(26, 40), 26, ThemeScript.TEXT)
	_draw_pill(Rect2(536, 22, 78, 34), Color(0.10, 0.11, 0.13, 0.94), false)
	_draw_text("Home", Vector2(557, 43), 12, ThemeScript.TEXT_MUTED)
	for index in range(DIAGNOSTIC_TABS.size()):
		var rect: Rect2 = _diagnostic_tab_rect(index)
		var tab_name: String = str(DIAGNOSTIC_TABS[index])
		var active: bool = tab_name == active_tab
		_draw_pill(rect, Color(0.095, 0.105, 0.125, 0.96), active)
		_draw_centered_text(tab_name, rect.position.x + rect.size.x * 0.5, rect.position.y + 22.0, 11, ThemeScript.TEXT if active else ThemeScript.TEXT_MUTED)
	_draw_soft_panel(Rect2(24, 138, 592, 318), 30.0)
	_draw_diagnostics_tab_content()
	_draw_scrollbar(_diagnostics_scroll_rect(), diagnostic_scroll_y, _diagnostics_content_height())

func _diagnostic_tab_rect(index: int) -> Rect2:
	return Rect2(24.0 + float(index % 5) * 118.0, 64.0 + float(int(index / 5)) * 36.0, 108.0, 28.0)

func _draw_diagnostics_tab_content() -> void:
	var view_rect: Rect2 = _diagnostics_scroll_rect()
	var offset_y: float = diagnostic_scroll_y
	_draw_text_if_visible(active_tab, Vector2(50, 174 - offset_y), view_rect, 21, ThemeScript.TEXT)
	if active_tab == "Overview":
		_draw_overview_cards(offset_y, view_rect)
	elif active_tab == "Processes":
		_draw_process_rows(offset_y, view_rect)
	elif active_tab == "Benchmarks":
		_draw_benchmark_rows(offset_y, view_rect)
	elif active_tab == "Camera":
		_draw_camera_rows(offset_y, view_rect)
	elif active_tab == "Audio":
		_draw_audio_rows(offset_y, view_rect)
	elif active_tab == "Reports":
		_draw_reports_rows(offset_y, view_rect)
	elif active_tab == "Logs":
		_draw_logs_rows(offset_y, view_rect)
	elif active_tab == "Network":
		_draw_network_rows(offset_y, view_rect)
	elif active_tab == "Study Stats":
		_draw_diagnostics_study_stats(offset_y, view_rect)
	else:
		_draw_info_row(52, 226 - offset_y, active_tab, "No saved report", "Waiting", view_rect)

func _draw_overview_cards(offset_y: float, view_rect: Rect2) -> void:
	var gpu_body := "Not supported"
	if bool(overview_live_data.get("gpu_usage_supported", false)) and overview_live_data.get("gpu_usage_percent", null) != null:
		gpu_body = str(overview_live_data.get("gpu_usage_percent")) + "%"
	elif str(overview_live_data.get("gpu_usage_status", "not_supported")) != "not_supported":
		gpu_body = "Unknown"
	var cards: Array = [
		{"title": "System", "body": str(overview_live_data.get("overall_status", active_tab_data.get("overall_status", "Pending"))), "pill": "OK" if overview_live_data.get("system_ok", false) else "Pending"},
		{"title": "Wi-Fi", "body": str(overview_live_data.get("connected_ssid", "Unknown")), "pill": "Live"},
		{"title": "Remote Wi-Fi", "body": str(overview_live_data.get("remote_network_state", "planned")), "pill": "Dry"},
		{"title": "Remote", "body": str(overview_live_data.get("remote_connected", "unknown")), "pill": "Later"},
		{"title": "CPU Temp", "body": str(overview_live_data.get("cpu_temperature_c", "Unknown")) + " C", "pill": "Live"},
		{"title": "CPU Use", "body": str(overview_live_data.get("cpu_usage_percent", "Pending")) + "%", "pill": "Live"},
		{"title": "RAM", "body": str(overview_live_data.get("ram_usage_percent", "Unknown")) + "%", "pill": "Live"},
		{"title": "GPU", "body": gpu_body, "pill": "No"},
		{"title": "Speaker", "body": str(overview_live_data.get("speaker_status", "Pending")), "pill": "Live"},
		{"title": "Camera", "body": "Ready" if bool(overview_live_data.get("camera_ready", false)) else "Unknown", "pill": "Live"}
	]
	for index in range(cards.size()):
		var rect: Rect2 = Rect2(48.0 + float(index % 2) * 272.0, 194.0 + float(int(index / 2)) * 50.0 - offset_y, 250.0, 42.0)
		var item: Dictionary = cards[index] as Dictionary
		if not _rect_visible(rect, view_rect):
			continue
		_draw_card_if_visible(rect, view_rect, Color(0.085, 0.095, 0.115, 0.96), 18.0)
		_draw_text_if_visible(str(item["title"]), rect.position + Vector2(12, 18), view_rect, 12, ThemeScript.TEXT)
		_draw_text_if_visible(str(item["body"]), rect.position + Vector2(12, 34), view_rect, 10, ThemeScript.TEXT_MUTED)
		_draw_pill(Rect2(rect.position.x + 180.0, rect.position.y + 10.0, 54.0, 22.0), Color(0.08, 0.13, 0.11, 0.92), item["pill"] == "OK")
		_draw_centered_text(str(item["pill"]), rect.position.x + 207.0, rect.position.y + 26.0, 10, ThemeScript.OK if item["pill"] == "OK" else ThemeScript.TEXT_MUTED)

func _draw_process_rows(offset_y: float, view_rect: Rect2) -> void:
	var y := 208.0 - offset_y
	_draw_text_if_visible("Service", Vector2(54, y), view_rect, 11, ThemeScript.TEXT_DIM)
	_draw_text_if_visible("Status", Vector2(328, y), view_rect, 11, ThemeScript.TEXT_DIM)
	_draw_text_if_visible("CPU", Vector2(430, y), view_rect, 11, ThemeScript.TEXT_DIM)
	_draw_text_if_visible("RAM", Vector2(506, y), view_rect, 11, ThemeScript.TEXT_DIM)
	y += 18.0
	var rows_raw = active_tab_data.get("processes", diagnostics_data.sample_process_rows())
	var rows: Array = diagnostics_data.sample_process_rows()
	if rows_raw is Array:
		rows = rows_raw
	for raw_row in rows:
		var row: Dictionary = raw_row as Dictionary
		var row_rect: Rect2 = Rect2(48, y - 14.0, 544, 32)
		_draw_card_if_visible(row_rect, view_rect, Color(0.075, 0.085, 0.102, 0.94), 16.0)
		_draw_text_if_visible(str(row.get("display_name", row.get("name", "Service"))), Vector2(62, y + 7.0), view_rect, 12, ThemeScript.TEXT)
		_draw_text_if_visible(str(row.get("status", "Pending")), Vector2(328, y + 7.0), view_rect, 11, ThemeScript.TEXT_MUTED)
		_draw_text_if_visible(str(row.get("cpu_percent", row.get("cpu", "--"))) + "%", Vector2(430, y + 7.0), view_rect, 11, ThemeScript.TEXT_MUTED)
		_draw_text_if_visible(str(row.get("memory_rss_mb", row.get("ram", "--"))) + " MB", Vector2(506, y + 7.0), view_rect, 11, ThemeScript.TEXT_MUTED)
		y += 36.0

func _draw_benchmark_rows(offset_y: float, view_rect: Rect2) -> void:
	var top_card: Rect2 = Rect2(50, 206 - offset_y, 540, 54)
	_draw_card_if_visible(top_card, view_rect, Color(0.085, 0.095, 0.115, 0.96), 22.0)
	_draw_text_if_visible("Benchmark status", Vector2(66, 228 - offset_y), view_rect, 16, ThemeScript.TEXT)
	_draw_text_if_visible(str(active_tab_data.get("status", "idle")), Vector2(66, 248 - offset_y), view_rect, 12, ThemeScript.TEXT_MUTED)
	_draw_button(Rect2(416, 154, 154, 34), "Run benchmark", false)
	var result_raw = active_tab_data.get("result", {})
	var result: Dictionary = {}
	if result_raw is Dictionary:
		result = result_raw
	var rows_raw = result.get("results", [])
	var rows: Array = []
	if rows_raw is Array:
		rows = rows_raw
	if rows.is_empty():
		var state: String = str(active_tab_data.get("status", "idle"))
		_draw_info_row(54, 292 - offset_y, "Benchmarks", "Running..." if state in ["pending", "running"] else "Not run yet", state, view_rect)
	else:
		for index in range(rows.size()):
			var item: Dictionary = rows[index] as Dictionary
			_draw_info_row(54, 292 + index * 34 - offset_y, str(item.get("name", "Check")), str(item.get("duration_ms", "0")) + " ms", str(item.get("status", "ok")), view_rect)

func _draw_network_rows(offset_y: float, view_rect: Rect2) -> void:
	_draw_info_row(54, 224 - offset_y, "Wi-Fi", str(active_tab_data.get("connected_ssid", "Unknown")), "Live", view_rect)
	_draw_info_row(54, 260 - offset_y, "Enabled", str(active_tab_data.get("wifi_enabled", "Unknown")), "Live", view_rect)
	_draw_info_row(54, 296 - offset_y, "Remote Wi-Fi", str(active_tab_data.get("remote_network_state", "planned")), "Dry", view_rect)
	_draw_info_row(54, 332 - offset_y, "Remote", str(active_tab_data.get("remote_connected", active_tab_data.get("pilot_connected", "unknown"))), "Later", view_rect)
	_draw_text_if_visible("Saved networks", Vector2(58, 380 - offset_y), view_rect, 13, ThemeScript.TEXT)
	var saved_raw = active_tab_data.get("saved_networks", [])
	var saved: Array = []
	if saved_raw is Array:
		saved = saved_raw
	if saved.is_empty():
		_draw_info_row(54, 418 - offset_y, "Saved", "No saved networks", "Dry", view_rect)
	else:
		for index in range(mini(saved.size(), 3)):
			_draw_info_row(54, 418 + index * 34 - offset_y, "Saved", str(saved[index]), "Dry", view_rect)
	_draw_text_if_visible("Available networks", Vector2(58, 540 - offset_y), view_rect, 13, ThemeScript.TEXT)
	var available_raw = active_tab_data.get("available_networks", [])
	var available: Array = []
	if available_raw is Array:
		available = available_raw
	if available.is_empty():
		_draw_info_row(54, 578 - offset_y, "Available", "No available networks", "Dry", view_rect)
	else:
		for index in range(mini(available.size(), 4)):
			_draw_info_row(54, 578 + index * 34 - offset_y, "Available", str(available[index]), "Dry", view_rect)
	_draw_info_row(54, 730 - offset_y, "Connect", "planned only", "Dry", view_rect)

func _draw_camera_rows(offset_y: float, view_rect: Rect2) -> void:
	var preview: Rect2 = Rect2(44, 196 - offset_y, 270, 160)
	_draw_card_if_visible(preview, view_rect, Color(0.045, 0.052, 0.064, 1.0), 22.0)
	if camera_frame_texture != null and _rect_visible(preview, view_rect):
		draw_texture_rect(camera_frame_texture, Rect2(preview.position + Vector2(10, 10), preview.size - Vector2(20, 20)), false)
	else:
		_draw_text_if_visible("Preview", preview.position + Vector2(18, 58), view_rect, 16, ThemeScript.TEXT)
		_draw_text_if_visible(camera_preview_status, preview.position + Vector2(18, 88), view_rect, 12, ThemeScript.TEXT_MUTED)
	_draw_info_row_compact(330, 208 - offset_y, 248, "Detected", str(active_tab_data.get("camera_detected", "Unknown")), "Live", view_rect)
	_draw_info_row_compact(330, 244 - offset_y, 248, "Ready", str(active_tab_data.get("camera_ready", "Unknown")), "Live", view_rect)
	_draw_info_row_compact(330, 280 - offset_y, 248, "Name", str(active_tab_data.get("camera_name", "Unknown")), "Live", view_rect)
	var preview_button: Rect2 = Rect2(350, 316 - offset_y, 190, 34)
	var run_button: Rect2 = Rect2(350, 356 - offset_y, 190, 34)
	if _rect_visible(preview_button, view_rect):
		_draw_button(preview_button, "Preview On" if camera_preview_on else "Preview Off", camera_preview_on)
	if _rect_visible(run_button, view_rect):
		_draw_button(run_button, "Run camera", false)

func _draw_audio_rows(offset_y: float, view_rect: Rect2) -> void:
	_draw_button(Rect2(416, 154, 154, 34), "Run audio", false)
	_draw_info_row(54, 224 - offset_y, "Speaker", str(active_tab_data.get("speaker_status", "Unknown")), "Live", view_rect)
	_draw_info_row(54, 260 - offset_y, "Name", str(active_tab_data.get("speaker_name", "Unknown")), "Live", view_rect)
	_draw_info_row(54, 296 - offset_y, "Volume", str(active_tab_data.get("volume_percent", "Unknown")), "Live", view_rect)
	_draw_info_row(54, 332 - offset_y, "Muted", str(active_tab_data.get("muted", "Unknown")), "Live", view_rect)

func _draw_reports_rows(offset_y: float, view_rect: Rect2) -> void:
	_draw_button(Rect2(416, 154, 154, 34), "Generate", false)
	var rows_raw = active_tab_data.get("reports", [])
	var rows: Array = []
	if rows_raw is Array:
		rows = rows_raw
	if rows.is_empty():
		_draw_info_row(54, 224 - offset_y, "Reports", "No report", str(active_tab_data.get("status", "idle")), view_rect)
	for index in range(rows.size()):
		var item: Dictionary = rows[index] as Dictionary
		_draw_info_row(54, 224 + index * 34 - offset_y, str(item.get("name", "Report")), str(item.get("size_bytes", "")), "Saved", view_rect)

func _draw_logs_rows(offset_y: float, view_rect: Rect2) -> void:
	_draw_button(Rect2(416, 154, 154, 34), "Refresh logs", false)
	var rows_raw = active_tab_data.get("lines", ["No logs yet"])
	var rows: Array = ["No logs yet"]
	if rows_raw is Array:
		rows = rows_raw
	for index in range(rows.size()):
		_draw_text_if_visible(str(rows[index]), Vector2(54, 214 + index * 18 - offset_y), view_rect, 11, ThemeScript.TEXT_MUTED)

func _draw_diagnostics_study_stats(offset_y: float, view_rect: Rect2) -> void:
	var rows: Array = [
		{"title": "Study minutes", "value": str(active_tab_data.get("total_study_minutes", "Pending"))},
		{"title": "Pomodoro sessions", "value": str(active_tab_data.get("total_pomodoro_sessions", "Pending"))},
		{"title": "Smart sessions", "value": str(active_tab_data.get("total_smart_study_sessions", "Pending"))},
		{"title": "Flashcards", "value": str(active_tab_data.get("total_flashcards", "Pending"))},
		{"title": "Quiz questions", "value": str(active_tab_data.get("total_quiz_questions", "Pending"))},
		{"title": "Language words", "value": str(active_tab_data.get("total_language_words", "Pending"))},
		{"title": "Mastered words", "value": str(active_tab_data.get("mastered_language_words", "Pending"))}
	]
	for index in range(rows.size()):
		var item: Dictionary = rows[index] as Dictionary
		_draw_info_row(54, 224 + index * 34 - offset_y, str(item["title"]), str(item["value"]), "Live", view_rect)

func _draw_info_row(x: float, y: float, title: String, subtitle: String, status: String, view_rect: Rect2) -> void:
	var row_rect: Rect2 = Rect2(x - 6.0, y - 22.0, 540.0, 32.0)
	if not _rect_visible(row_rect, view_rect):
		return
	_draw_card_if_visible(row_rect, view_rect, Color(0.075, 0.085, 0.102, 0.94), 16.0)
	_draw_text_if_visible(title, Vector2(x + 8.0, y), view_rect, 12, ThemeScript.TEXT)
	_draw_text_if_visible(subtitle, Vector2(x + 186.0, y), view_rect, 11, ThemeScript.TEXT_MUTED)
	_draw_pill(Rect2(x + 444.0, y - 17.0, 72.0, 22.0), Color(0.10, 0.105, 0.12, 0.92), false)
	_draw_centered_text(status, x + 480.0, y, 11, ThemeScript.TEXT_MUTED)

func _draw_info_row_compact(x: float, y: float, width: float, title: String, subtitle: String, status: String, view_rect: Rect2) -> void:
	var row_rect: Rect2 = Rect2(x, y - 22.0, width, 30.0)
	if not _rect_visible(row_rect, view_rect):
		return
	_draw_card_if_visible(row_rect, view_rect, Color(0.075, 0.085, 0.102, 0.94), 15.0)
	_draw_text_if_visible(title, Vector2(x + 10.0, y - 2.0), view_rect, 11, ThemeScript.TEXT)
	_draw_text_if_visible(subtitle, Vector2(x + 82.0, y - 2.0), view_rect, 10, ThemeScript.TEXT_MUTED)
	_draw_pill(Rect2(x + width - 58.0, y - 17.0, 48.0, 20.0), Color(0.10, 0.105, 0.12, 0.92), false)
	_draw_centered_text(status, x + width - 34.0, y - 2.0, 9, ThemeScript.TEXT_MUTED)

func _draw_button(rect: Rect2, label: String, active: bool) -> void:
	_draw_tile(rect, active)
	_draw_centered_text(label, rect.position.x + rect.size.x * 0.5, rect.position.y + 22.0, 11, ThemeScript.TEXT)

func _draw_settings() -> void:
	draw_rect(Rect2(Vector2.ZERO, Vector2(WIDTH, HEIGHT)), _theme_background_color(), true)
	_draw_text("Settings", Vector2(26, 44), 26, ThemeScript.TEXT)
	var back_label: String = "Home" if settings_current_page == "home" else "Back"
	_draw_pill(Rect2(520, 22, 92, 34), Color(0.10, 0.11, 0.13, 0.94), false)
	_draw_centered_text(back_label, 566.0, 43.0, 12, ThemeScript.TEXT_MUTED)
	if settings_current_page == "home":
		_draw_settings_home()
	elif settings_current_page == "quick_shelf":
		_draw_quick_shelf_settings()
	elif settings_current_page == "privacy":
		_draw_privacy_settings()
	else:
		_draw_settings_detail_page()
	_draw_scrollbar(_settings_scroll_rect(), settings_scroll_y, _settings_content_height())
	if settings_dropdown_open:
		_draw_settings_dropdown()

func _draw_settings_home() -> void:
	var view_rect: Rect2 = _settings_scroll_rect()
	for index in range(SETTINGS_TILES.size()):
		var rect: Rect2 = _settings_tile_rect(index)
		if not _rect_visible(rect, view_rect):
			continue
		var tile: Dictionary = SETTINGS_TILES[index] as Dictionary
		var active: bool = str(tile["title"]) == "Exit NeXa"
		_draw_tile(rect, active)
		_draw_text(str(tile["icon"]), rect.position + Vector2(18, 39), 19, ThemeScript.TEXT)
		_draw_text(str(tile["title"]), rect.position + Vector2(54, 25), 15, ThemeScript.TEXT)
		_draw_text(str(tile["subtitle"]), rect.position + Vector2(54, 46), 10, ThemeScript.TEXT_MUTED)

func _settings_tile_rect(index: int) -> Rect2:
	var column: int = index % 2
	var row: int = int(index / 2)
	return Rect2(28.0 + float(column) * 300.0, 92.0 + float(row) * 82.0 - settings_scroll_y, 284.0, 66.0)

func _draw_settings_detail_page() -> void:
	var view_rect: Rect2 = _settings_scroll_rect()
	var title: String = settings_current_page.replace("_", " ").capitalize()
	_draw_text_if_visible(title, Vector2(44, 96 - settings_scroll_y), view_rect, 21, ThemeScript.TEXT)
	if settings_current_page == "about":
		_draw_about_settings(view_rect)
		return
	var rows: Array = _settings_rows_for_page(settings_current_page)
	for index in range(rows.size()):
		var row: Dictionary = rows[index] as Dictionary
		var rect: Rect2 = _setting_row_rect(index)
		if not _rect_visible(rect, view_rect):
			continue
		var section: String = str(row.get("section", ""))
		var key: String = str(row.get("key", ""))
		var value_text: String = str(row.get("subtitle", "Planned"))
		if section != "" and key != "":
			var value = _settings_value(section, key, row.get("default", "Pending"))
			value_text = _format_setting_value(value)
		var active: bool = settings_current_page == "modes" and str(row.get("title", "")) == str(_settings_value("modes", "current_mode", "Normal"))
		_draw_settings_row(rect, str(row.get("title", "Setting")), value_text, active)
	if settings_current_page == "network":
		_draw_text_if_visible("Wi-Fi connect actions stay dry-run/planned.", Vector2(50, 438 - settings_scroll_y), view_rect, 11, ThemeScript.TEXT_DIM)
	if settings_current_page == "notifications":
		var private_on: bool = bool(_settings_value("notifications", "private_notifications_enabled", false)) or bool(_settings_value("notifications", "private_reminders_enabled", false))
		var pin_enabled: bool = bool(privacy_status_data.get("pin_enabled", false))
		var note: String = "Private content unlocked" if bool(privacy_status_data.get("unlocked", false)) else ("Go to Privacy to set a 4-digit PIN" if private_on and not pin_enabled else "Private content locked")
		_draw_text_if_visible(note, Vector2(50, 438 - settings_scroll_y), view_rect, 11, ThemeScript.TEXT_DIM)
	if settings_current_page == "user":
		_draw_text_if_visible(settings_status_text, Vector2(50, 330 - settings_scroll_y), view_rect, 11, ThemeScript.TEXT_DIM)
	if settings_current_page == "safety" or settings_current_page == "exit_nexa":
		_draw_text_if_visible("Exit NeXa? Cancel or Exit UI planned only.", Vector2(50, 438 - settings_scroll_y), view_rect, 11, ThemeScript.TEXT_DIM)

func _draw_settings_row(rect: Rect2, title: String, value: String, active: bool) -> void:
	_draw_tile(rect, active)
	_draw_text(_short_text(title, 28), rect.position + Vector2(14, 24), 13, ThemeScript.TEXT)
	_draw_text(_short_text(value, 28), rect.position + Vector2(310, 24), 11, ThemeScript.TEXT_MUTED)

func _format_setting_value(value) -> String:
	if value is bool:
		return "On" if bool(value) else "Off"
	if value is Array:
		return str(value.size()) + " selected"
	return str(value)

func _pin_dots() -> String:
	var text := ""
	for index in range(4):
		text += "*" if index < pin_input.length() else "-"
	return text

func _draw_quick_shelf_settings() -> void:
	var view_rect: Rect2 = _settings_scroll_rect()
	var enabled: Array = _settings_enabled_quick_shelf()
	_draw_text_if_visible("Quick Shelf", Vector2(44, 96 - settings_scroll_y), view_rect, 21, ThemeScript.TEXT)
	_draw_text_if_visible(str(enabled.size()) + " selected", Vector2(466, 96 - settings_scroll_y), view_rect, 12, ThemeScript.TEXT_MUTED)
	for index in range(QUICK_SHELF_OPTIONS.size()):
		var rect: Rect2 = Rect2(44.0 + float(index % 2) * 282.0, 136.0 + float(int(index / 2)) * 44.0 - settings_scroll_y, 260.0, 36.0)
		if not _rect_visible(rect, view_rect):
			continue
		var name: String = str(QUICK_SHELF_OPTIONS[index])
		_draw_tile(rect, enabled.has(name))
		_draw_text(_short_text(name, 22), rect.position + Vector2(14, 23), 12, ThemeScript.TEXT)

func _draw_privacy_settings() -> void:
	var view_rect: Rect2 = _settings_scroll_rect()
	_draw_text_if_visible("Privacy", Vector2(44, 96 - settings_scroll_y), view_rect, 21, ThemeScript.TEXT)
	_draw_button(Rect2(44, 114 - settings_scroll_y, 264, 38), "Set 4-digit PIN", pin_mode == "set")
	_draw_button(Rect2(332, 114 - settings_scroll_y, 264, 38), "Unlock private", pin_mode == "verify")
	var unlocked: bool = bool(privacy_status_data.get("unlocked", false))
	var pin_enabled: bool = bool(privacy_status_data.get("pin_enabled", false))
	_draw_settings_row(Rect2(44, 166 - settings_scroll_y, 552, 38), "PIN", "Enabled" if pin_enabled else "Not set", false)
	_draw_settings_row(Rect2(44, 210 - settings_scroll_y, 552, 38), "Private content", "Unlocked" if unlocked else "Locked", unlocked)
	_draw_text_if_visible("PIN: " + _pin_dots(), Vector2(258, 270 - settings_scroll_y), view_rect, 18, ThemeScript.TEXT)
	for index in range(12):
		var col: int = index % 3
		var row: int = int(index / 3)
		var rect: Rect2 = Rect2(178.0 + float(col) * 74.0, 292.0 + float(row) * 42.0 - settings_scroll_y, 62.0, 34.0)
		if not _rect_visible(rect, view_rect):
			continue
		var label: String = str(index + 1) if index < 9 else ("Clear" if index == 9 else ("0" if index == 10 else "OK"))
		_draw_button(rect, label, false)
	_draw_button(Rect2(44, 470 - settings_scroll_y, 264, 38), "Lock now", false)
	_draw_settings_row(Rect2(44, 520 - settings_scroll_y, 552, 38), "Private notifications", _format_setting_value(_settings_value("notifications", "private_notifications_enabled", false)), false)
	_draw_settings_row(Rect2(44, 564 - settings_scroll_y, 552, 38), "Private reminders", _format_setting_value(_settings_value("notifications", "private_reminders_enabled", false)), false)

func _draw_settings_dropdown() -> void:
	var panel: Rect2 = _settings_dropdown_rect()
	_draw_rounded_rect(panel, Color(0.052, 0.060, 0.074, 1.0), 20.0)
	_draw_rounded_outline(panel, Color(1.0, 1.0, 1.0, 0.08), 20.0)
	_draw_text("Choose " + settings_dropdown_key.replace("_", " "), panel.position + Vector2(18, 28), 14, ThemeScript.TEXT)
	for index in range(settings_dropdown_options.size()):
		var rect: Rect2 = _settings_dropdown_option_rect(index)
		var value: String = str(settings_dropdown_options[index])
		var active: bool = value == str(_settings_value(settings_dropdown_section, settings_dropdown_key, ""))
		_draw_tile(rect, active)
		_draw_text(_short_text(value, 19), rect.position + Vector2(12, 22), 11, ThemeScript.TEXT)

func _settings_dropdown_rect() -> Rect2:
	return Rect2(82, 92, 476, 330)

func _settings_dropdown_option_rect(index: int) -> Rect2:
	var column: int = index % 2
	var row: int = int(index / 2)
	return Rect2(104.0 + float(column) * 226.0, 136.0 + float(row) * 31.0, 204.0, 25.0)

func _draw_quick_shelf() -> void:
	var panel: Rect2 = Rect2(20, 86, 600, 374)
	_draw_rounded_rect(panel, Color(0.052, 0.060, 0.074, 1.0), 28.0)
	_draw_rounded_outline(panel, Color(1.0, 1.0, 1.0, 0.07), 28.0)
	_draw_text("Quick Shelf", Vector2(44, 126), 24, ThemeScript.TEXT)
	_draw_text("Swipe down to close", Vector2(46, 148), 11, ThemeScript.TEXT_MUTED)
	var tiles: Array = _settings_enabled_quick_shelf()
	if tiles.is_empty():
		tiles = ["Brightness", "Sound", "Quiet Mode", "Network", "Reminders", "Study", "Diagnostics", "Settings"]
	var view_rect: Rect2 = _quick_shelf_scroll_rect()
	for index in range(tiles.size()):
		var rect: Rect2 = _quick_shelf_tile_rect(index)
		if not _rect_visible(rect, view_rect):
			continue
		var name: String = str(tiles[index])
		var active: bool = name == "Quiet Mode" and quiet_mode_local
		_draw_tile(rect, active)
		_draw_text(_quick_shelf_icon(name), rect.position + Vector2(14, 34), 18, ThemeScript.TEXT)
		_draw_text(_short_text(name, 18), rect.position + Vector2(48, 24), 13, ThemeScript.TEXT)
		_draw_text(_short_text(_quick_shelf_subtitle(name), 20), rect.position + Vector2(48, 45), 10, ThemeScript.TEXT_MUTED)
	if quick_shelf_status_text != "":
		_draw_text(quick_shelf_status_text, Vector2(46, 438), 11, ThemeScript.TEXT_MUTED)
	_draw_scrollbar(view_rect, quick_shelf_scroll_y, _quick_shelf_content_height())

func _quick_shelf_tile_rect(index: int) -> Rect2:
	var column: int = index % 2
	var row: int = int(index / 2)
	return Rect2(44.0 + float(column) * 282.0, 168.0 + float(row) * 72.0 - quick_shelf_scroll_y, 260.0, 58.0)

func _quick_shelf_icon(name: String) -> String:
	if name == "Brightness":
		return "☼"
	if name == "Sound":
		return "♪"
	if name == "Quiet Mode":
		return "!"
	if name == "Network":
		return "⌁"
	if name == "Diagnostics":
		return "▦"
	if name == "Settings":
		return "⚙"
	if name == "Clock":
		return "◷"
	if name == "Camera":
		return "□"
	if name == "Study" or name == "Study Stats":
		return "◌"
	return "◆"

func _quick_shelf_subtitle(name: String) -> String:
	if name == "Brightness":
		return str(brightness_percent) + "%"
	if name == "Sound":
		return str(sound_percent) + "%"
	if name == "Quiet Mode":
		return "On" if quiet_mode_local else "Off"
	if name in ["Diagnostics", "Settings", "Clock", "Network", "Camera", "Logs", "Reports", "Study", "Study Stats", "Games"]:
		return "Open"
	return "Planned"

func _draw_study() -> void:
	draw_rect(Rect2(Vector2.ZERO, Vector2(WIDTH, HEIGHT)), _theme_background_color(), true)
	_draw_text("NeXa Learn", Vector2(26, 44), 26, ThemeScript.TEXT)
	_draw_text("Learn smarter with NeXa", Vector2(28, 66), 11, ThemeScript.TEXT_MUTED)
	var back_label: String = "Home" if study_current_page == "home" else "Back"
	_draw_pill(Rect2(520, 22, 92, 34), Color(0.10, 0.11, 0.13, 0.94), false)
	_draw_centered_text(back_label, 566.0, 43.0, 12, ThemeScript.TEXT_MUTED)
	if study_current_page == "home":
		_draw_study_home()
	elif study_current_page == "pomodoro":
		_draw_study_pomodoro()
	elif study_current_page == "smart_study":
		_draw_study_smart()
	elif study_current_page == "flashcards":
		_draw_study_flashcards()
	elif study_current_page == "quizzes":
		_draw_study_quizzes()
	elif study_current_page == "languages":
		_draw_study_languages()
	elif study_current_page == "stats":
		_draw_study_stats()
	elif study_current_page == "history":
		_draw_study_history()
	elif study_current_page == "settings":
		_draw_study_settings()
	if study_status_text != "":
		_draw_text(_short_text(study_status_text, 70), Vector2(34, 460), 10, ThemeScript.TEXT_DIM)
	if text_input_open:
		_draw_text_input_overlay()

func _draw_calendar() -> void:
	draw_rect(Rect2(Vector2.ZERO, Vector2(WIDTH, HEIGHT)), _theme_background_color(), true)
	var month_label := str(calendar_data.get("month_name", _calendar_month_name(calendar_month))) + " " + str(calendar_year)
	_draw_text(month_label, Vector2(26, 44), 25, ThemeScript.TEXT)
	_draw_button(Rect2(330, 30, 84, 30), "Previous", false)
	_draw_button(Rect2(422, 30, 74, 30), "Next", false)
	_draw_pill(Rect2(520, 22, 92, 34), Color(0.10, 0.11, 0.13, 0.94), false)
	_draw_centered_text("Home", 566.0, 43.0, 12, ThemeScript.TEXT_MUTED)
	_draw_calendar_weekdays()
	_draw_calendar_grid()
	if calendar_mode == "add" or calendar_mode == "edit":
		_draw_calendar_form()
	elif calendar_mode == "delete_confirm":
		_draw_calendar_day_details()
		_draw_rounded_rect(Rect2(62, 286, 516, 128), Color(0.08, 0.04, 0.045, 0.98), 18.0)
		_draw_rounded_outline(Rect2(62, 286, 516, 128), Color(1.0, 0.22, 0.22, 0.45), 18.0)
		_draw_text("Delete selected event?", Vector2(84, 320), 17, ThemeScript.TEXT)
		_draw_text("This cannot be undone.", Vector2(84, 344), 11, ThemeScript.TEXT_MUTED)
		_draw_button(Rect2(78, 354, 210, 42), "Cancel", false)
		_draw_button(Rect2(352, 354, 210, 42), "Confirm delete", true)
	else:
		_draw_calendar_day_details()
	if calendar_status_text != "":
		_draw_text(_short_text(calendar_status_text, 74), Vector2(34, 472), 10, ThemeScript.TEXT_DIM)
	if text_input_open:
		_draw_text_input_overlay()

func _draw_calendar_weekdays() -> void:
	var labels := ["M", "T", "W", "T", "F", "S", "S"]
	for index in range(7):
		var rect := _calendar_weekday_rect(index)
		var color := Color(1.0, 0.48, 0.48, 0.78) if index == 6 else ThemeScript.TEXT_MUTED
		_draw_centered_text(str(labels[index]), rect.position.x + rect.size.x * 0.5, rect.position.y + 16.0, 11, color)

func _draw_calendar_grid() -> void:
	var cells := _calendar_cells()
	for index in range(42):
		var rect := _calendar_cell_rect(index)
		var cell: Dictionary = cells[index] as Dictionary if index < cells.size() else {}
		var selected := bool(cell.get("is_selected", false)) or str(cell.get("full_date", "")) == calendar_selected_date
		var fill := Color(0.120, 0.132, 0.158, 1.0) if selected else Color(0.064, 0.072, 0.088, 0.96)
		if not bool(cell.get("is_current_month", true)):
			fill = Color(0.045, 0.050, 0.062, 0.88)
		_draw_rounded_rect(rect, fill, 8.0)
		_draw_rounded_outline(rect, Color(1.0, 1.0, 1.0, 0.055), 8.0)
		var day_number := int(cell.get("day_number", 0))
		var day_text := str(day_number) if day_number > 0 else ""
		var day_color := Color(1.0, 0.45, 0.45, 0.82) if bool(cell.get("is_sunday", false)) else ThemeScript.TEXT
		if not bool(cell.get("is_current_month", true)):
			day_color = ThemeScript.TEXT_DIM
		if bool(cell.get("is_today", false)):
			_draw_rounded_rect(Rect2(rect.position.x + 25.0, rect.position.y + 4.0, 26.0, 20.0), Color(0.18, 0.58, 1.0, 0.24), 10.0)
		_draw_centered_text(day_text, rect.position.x + rect.size.x * 0.5, rect.position.y + 18.0, 11, day_color)
		_draw_calendar_event_indicator(rect, int(cell.get("events_count", 0)), bool(cell.get("has_reminder", false)))

func _draw_calendar_event_indicator(rect: Rect2, count: int, has_reminder: bool) -> void:
	if count <= 0:
		return
	var y := rect.position.y + 30.0
	if count <= 3:
		var start_x := rect.position.x + rect.size.x * 0.5 - float(count - 1) * 5.0
		for index in range(count):
			draw_circle(Vector2(start_x + float(index) * 10.0, y), 2.2, ThemeScript.BLUE)
	else:
		_draw_centered_text("3+", rect.position.x + rect.size.x * 0.5, y + 4.0, 9, ThemeScript.BLUE)
	if has_reminder:
		draw_circle(Vector2(rect.position.x + rect.size.x - 10.0, rect.position.y + 10.0), 2.0, ThemeScript.WARNING)

func _draw_calendar_day_details() -> void:
	var panel := Rect2(24, 370, 592, 90)
	_draw_rounded_rect(panel, Color(0.052, 0.060, 0.074, 0.98), 14.0)
	_draw_rounded_outline(panel, Color(1.0, 1.0, 1.0, 0.065), 14.0)
	_draw_text(_short_text(str(calendar_day_data.get("display_date", calendar_selected_date)), 42), Vector2(44, 390), 14, ThemeScript.TEXT)
	_draw_button(Rect2(44, 426, 92, 34), "Add", false)
	_draw_button(Rect2(148, 426, 92, 34), "Edit", calendar_selected_event_id > 0)
	_draw_button(Rect2(252, 426, 92, 34), "Delete", calendar_selected_event_id > 0)
	var events := _calendar_day_events()
	if events.is_empty():
		_draw_text("No events", Vector2(366, 432), 11, ThemeScript.TEXT_MUTED)
		return
	for index in range(mini(events.size(), 2)):
		var event: Dictionary = events[index] as Dictionary
		var row := _calendar_event_row_rect(index)
		var active := int(event.get("id", 0)) == calendar_selected_event_id
		_draw_rounded_rect(row, Color(0.12, 0.132, 0.158, 1.0) if active else Color(0.075, 0.085, 0.102, 1.0), 10.0)
		_draw_text(_short_text(str(event.get("start_time", "")) + " " + str(event.get("title", "")), 28), row.position + Vector2(8, 18), 10, ThemeScript.TEXT)

func _draw_calendar_form() -> void:
	_draw_rounded_rect(Rect2(24, 92, 592, 368), Color(0.040, 0.047, 0.060, 0.985), 18.0)
	_draw_rounded_outline(Rect2(24, 92, 592, 368), Color(1.0, 1.0, 1.0, 0.08), 18.0)
	_draw_text("Add Event" if calendar_mode == "add" else "Edit Event", Vector2(44, 110), 18, ThemeScript.TEXT)
	_draw_study_row(Rect2(44, 118, 552, 32), "Title", calendar_form_title if calendar_form_title != "" else "Tap to type")
	_draw_study_row(Rect2(44, 156, 552, 32), "Description", calendar_form_description if calendar_form_description != "" else "Optional")
	_draw_reminder_form_field(Rect2(44, 194, 260, 32), "Date", calendar_form_date)
	_draw_reminder_form_field(Rect2(324, 194, 170, 32), "Time", calendar_form_time)
	_draw_button(Rect2(44, 240, 160, 32), _calendar_reminder_label(), false)
	_draw_button(Rect2(224, 240, 160, 32), _calendar_snooze_label(), false)
	_draw_button(Rect2(404, 240, 160, 32), _calendar_repeat_label(), false)
	_draw_text("Reminder: Off / At time / 5 min before / 15 min before / 1 hour before", Vector2(48, 294), 9, ThemeScript.TEXT_DIM)
	_draw_text("Snooze: Off / 5 min / 10 min / 30 min", Vector2(48, 314), 9, ThemeScript.TEXT_DIM)
	_draw_text("Repeat: None / Daily / Weekly / Monthly / Yearly", Vector2(48, 334), 9, ThemeScript.TEXT_DIM)
	_draw_button(Rect2(44, 390, 170, 34), "Save", false)
	_draw_button(Rect2(232, 390, 170, 34), "Cancel", false)

func _draw_messages_center() -> void:
	draw_rect(Rect2(Vector2.ZERO, Vector2(WIDTH, HEIGHT)), _theme_background_color(), true)
	_draw_text("NeXa Messages", Vector2(30, 48), 25, ThemeScript.TEXT)
	_draw_pill(Rect2(520, 22, 92, 34), Color(0.10, 0.11, 0.13, 0.94), false)
	_draw_centered_text("Home", 566.0, 43.0, 12, ThemeScript.TEXT_MUTED)
	var view := _messages_scroll_rect()
	if nexa_messages_data.is_empty():
		_draw_centered_text("No messages", 320.0, 244.0, 15, ThemeScript.TEXT_MUTED)
		return
	for index in range(nexa_messages_data.size()):
		var rect := _message_row_rect(index)
		if not _rect_visible(rect, view):
			continue
		var message: Dictionary = nexa_messages_data[index] as Dictionary
		_draw_card(rect, Color(0.075, 0.086, 0.106, 1.0), 14.0, false)
		var priority := str(message.get("priority", "normal"))
		var accent := ThemeScript.WARNING if priority == "warning" else (Color(1.0, 0.35, 0.35, 1.0) if priority == "critical" else ThemeScript.BLUE)
		draw_circle(rect.position + Vector2(18, 27), 4.0, accent)
		_draw_text(_short_text(str(message.get("title", "NeXa")), 28), rect.position + Vector2(34, 22), 13, ThemeScript.TEXT)
		_draw_text(_short_text(str(message.get("body", "")), 42), rect.position + Vector2(34, 40), 10, ThemeScript.TEXT_MUTED)
		_draw_text(_short_text(str(message.get("source", "system")), 14), rect.position + Vector2(454, 22), 9, ThemeScript.TEXT_DIM)
	_draw_scrollbar(view, messages_scroll_y, _messages_content_height())

func _draw_games() -> void:
	draw_rect(Rect2(Vector2.ZERO, Vector2(WIDTH, HEIGHT)), _theme_background_color(), true)
	if games_mode == "library":
		_draw_games_library()
	elif games_mode == "tic_tac_toe_menu":
		_draw_tic_tac_toe_menu()
	elif games_mode == "tic_tac_toe_game":
		_draw_tic_tac_toe_game()
	elif games_mode == "tic_tac_toe_result":
		_draw_tic_tac_toe_game()
		_draw_tic_tac_toe_result_modal()
	elif games_mode == "exit_confirm":
		_draw_tic_tac_toe_game()
		_draw_tic_tac_toe_exit_confirm()
	if games_help_open:
		_draw_tic_tac_toe_help()

func _draw_games_library() -> void:
	_draw_text("Games", Vector2(30, 48), 26, ThemeScript.TEXT)
	_draw_text("Choose a game", Vector2(32, 78), 12, ThemeScript.TEXT_MUTED)
	_draw_pill(_games_exit_rect(), Color(0.10, 0.11, 0.13, 0.94), games_focus_index == 4)
	_draw_centered_text("Exit", 566.0, 43.0, 12, ThemeScript.TEXT_MUTED)
	var cards := [
		{"title": "Tic-Tac-Toe", "subtitle": "X  O"},
		{"title": "Coming Soon", "subtitle": "..."},
		{"title": "Coming Soon", "subtitle": "..."},
		{"title": "Coming Soon", "subtitle": "..."}
	]
	for index in range(cards.size()):
		var rect := _games_card_rect(index)
		var item: Dictionary = cards[index] as Dictionary
		var selected := games_focus_index == index
		_draw_card(rect, Color(0.11, 0.14, 0.19, 1.0) if selected else Color(0.070, 0.080, 0.098, 1.0), 18.0, false)
		if selected:
			_draw_rounded_outline(rect.grow(2.0), Color(0.28, 0.58, 1.0, 0.80), 20.0)
		_draw_text(_short_text(str(item.get("title", "")), 18), rect.position + Vector2(18, 30), 17, ThemeScript.TEXT)
		_draw_text(_short_text(str(item.get("subtitle", "")), 18), rect.position + Vector2(18, 58), 22 if index == 0 else 16, ThemeScript.TEXT_MUTED)

func _draw_tic_tac_toe_top_bar(title: String) -> void:
	_draw_button(_ttt_back_rect(), "Back", false)
	_draw_centered_text(title, 320.0, 46.0, 20, ThemeScript.TEXT)
	_draw_button(_ttt_exit_rect(), "Exit", false)

func _draw_tic_tac_toe_menu() -> void:
	_draw_tic_tac_toe_top_bar("Tic-Tac-Toe")
	_draw_centered_text("Tic-Tac-Toe", 320.0, 132.0, 28, ThemeScript.TEXT)
	_draw_centered_text("X  O", 320.0, 178.0, 35, ThemeScript.TEXT_MUTED)
	var labels := ["Play with Someone", "Play with NeXa", "How to Play"]
	for index in range(labels.size()):
		_draw_button(_ttt_menu_button_rect(index), labels[index], tic_tac_toe_menu_focus_index == index)

func _draw_tic_tac_toe_game() -> void:
	_draw_tic_tac_toe_top_bar("Tic-Tac-Toe")
	_draw_centered_text(_ttt_game_status_label(), 320.0, 88.0, 16, ThemeScript.TEXT_MUTED)
	var board := _ttt_board_rect()
	_draw_rounded_rect(board, Color(0.050, 0.058, 0.072, 1.0), 16.0)
	_draw_rounded_outline(board, Color(1.0, 1.0, 1.0, 0.10), 16.0)
	for index in range(9):
		var cell := _ttt_cell_rect(index)
		var mark := str(tic_tac_toe_board[index])
		var selected := index == tic_tac_toe_selected_cell and not tic_tac_toe_game_over
		var winning := _ttt_winning_cells().has(index)
		var fill := Color(0.13, 0.16, 0.20, 1.0) if selected else Color(0.080, 0.092, 0.112, 1.0)
		if winning:
			fill = Color(0.13, 0.22, 0.18, 1.0)
		_draw_rounded_rect(cell, fill, 10.0)
		_draw_rounded_outline(cell, Color(0.30, 0.60, 1.0, 0.78) if selected else Color(1.0, 1.0, 1.0, 0.08), 10.0)
		if mark != "":
			_draw_centered_text(mark, cell.position.x + cell.size.x * 0.5, cell.position.y + 58.0, 48, ThemeScript.TEXT if mark == "X" else ThemeScript.TEXT_MUTED)
	_draw_button(_ttt_new_game_rect(), "New Game", false)

func _draw_tic_tac_toe_result_modal() -> void:
	_draw_rounded_rect(Rect2(70, 146, 500, 250), Color(0.040, 0.047, 0.060, 0.985), 20.0)
	_draw_rounded_outline(Rect2(70, 146, 500, 250), Color(0.34, 0.62, 1.0, 0.28), 20.0)
	_draw_centered_text(_ttt_result_title(), 320.0, 214.0, 28, ThemeScript.TEXT)
	var subtitle := "No winner this time." if tic_tac_toe_result == "draw" else "Nice move." if tic_tac_toe_result == TTT_PLAYER_X else "Try again."
	_draw_centered_text(subtitle, 320.0, 252.0, 14, ThemeScript.TEXT_MUTED)
	var labels := ["Play Again", "Back", "Exit"]
	for index in range(labels.size()):
		_draw_button(_ttt_result_button_rect(index), labels[index], tic_tac_toe_result_focus_index == index)

func _draw_tic_tac_toe_exit_confirm() -> void:
	_draw_rounded_rect(Rect2(100, 178, 440, 190), Color(0.040, 0.047, 0.060, 0.990), 20.0)
	_draw_rounded_outline(Rect2(100, 178, 440, 190), Color(1.0, 0.80, 0.34, 0.26), 20.0)
	_draw_centered_text("Exit game?", 320.0, 236.0, 24, ThemeScript.TEXT)
	_draw_centered_text("Your current game will be lost.", 320.0, 270.0, 13, ThemeScript.TEXT_MUTED)
	_draw_button(_ttt_exit_confirm_button_rect(0), "Cancel", true)
	_draw_button(_ttt_exit_confirm_button_rect(1), "Exit", false)

func _draw_tic_tac_toe_help() -> void:
	_draw_rounded_rect(Rect2(80, 120, 480, 260), Color(0.040, 0.047, 0.060, 0.992), 20.0)
	_draw_rounded_outline(Rect2(80, 120, 480, 260), Color(0.34, 0.62, 1.0, 0.30), 20.0)
	_draw_centered_text("How to Play", 320.0, 172.0, 22, ThemeScript.TEXT)
	_draw_text("Players take turns placing X and O.", Vector2(122, 214), 13, ThemeScript.TEXT_MUTED)
	_draw_text("Get three in a row to win.", Vector2(122, 238), 13, ThemeScript.TEXT_MUTED)
	_draw_text("In Play with NeXa, you are X.", Vector2(122, 262), 13, ThemeScript.TEXT_MUTED)
	_draw_text("NeXa is O and moves locally.", Vector2(122, 286), 13, ThemeScript.TEXT_MUTED)
	_draw_button(Rect2(190, 338, 260, 38), "Back", false)

func _ttt_game_status_label() -> String:
	if tic_tac_toe_game_over:
		return _ttt_result_title()
	if tic_tac_toe_nexa_thinking:
		return "NeXa is thinking..."
	if tic_tac_toe_mode == "nexa":
		return "Your turn" if tic_tac_toe_current_player == TTT_PLAYER_X else "NeXa is thinking..."
	return "Player " + tic_tac_toe_current_player + " turn"

func _ttt_winning_cells() -> Array:
	for raw_line in TTT_WIN_LINES:
		var line: Array = raw_line as Array
		var a := int(line[0])
		var b := int(line[1])
		var c := int(line[2])
		var value := str(tic_tac_toe_board[a])
		if value != TTT_EMPTY and value == str(tic_tac_toe_board[b]) and value == str(tic_tac_toe_board[c]):
			return [a, b, c]
	return []

func _draw_todo() -> void:
	draw_rect(Rect2(Vector2.ZERO, Vector2(WIDTH, HEIGHT)), _theme_background_color(), true)
	_draw_text("To Do", Vector2(26, 44), 26, ThemeScript.TEXT)
	_draw_pill(Rect2(520, 22, 92, 34), Color(0.10, 0.11, 0.13, 0.94), false)
	_draw_centered_text("Home", 566.0, 43.0, 12, ThemeScript.TEXT_MUTED)
	if todo_mode == "lists":
		_draw_button(Rect2(412, 26, 92, 30), "New List", false)
		_draw_todo_lists()
	elif todo_mode == "list_detail":
		_draw_todo_task_list()
	elif todo_mode == "list_form":
		_draw_todo_list_form()
	elif todo_mode == "task_form":
		_draw_todo_task_form()
	elif todo_mode == "task_detail" or todo_mode == "delete_confirm":
		_draw_todo_task_detail()
	if todo_mode == "delete_confirm":
		_draw_rounded_rect(Rect2(62, 286, 516, 128), Color(0.08, 0.04, 0.045, 0.98), 18.0)
		_draw_rounded_outline(Rect2(62, 286, 516, 128), Color(1.0, 0.22, 0.22, 0.45), 18.0)
		_draw_text("Delete this task?", Vector2(84, 320), 17, ThemeScript.TEXT)
		_draw_text("This cannot be undone.", Vector2(84, 344), 11, ThemeScript.TEXT_MUTED)
		_draw_button(Rect2(78, 354, 210, 42), "Cancel", false)
		_draw_button(Rect2(352, 354, 210, 42), "Delete", true)
	if todo_status_text != "":
		_draw_text(_short_text(todo_status_text, 74), Vector2(34, 470), 10, ThemeScript.TEXT_DIM)
	if text_input_open:
		_draw_text_input_overlay()

func _draw_todo_lists() -> void:
	var view := _todo_lists_scroll_rect()
	var lists := _todo_lists()
	if lists.is_empty():
		_draw_text("Inbox", Vector2(44, 112), 16, ThemeScript.TEXT_MUTED)
	for index in range(lists.size()):
		var item: Dictionary = lists[index] as Dictionary
		var rect := _todo_list_card_rect(index)
		if not _rect_visible(rect, view):
			continue
		_draw_card_if_visible(rect, view, Color(0.070, 0.080, 0.098, 1.0), 16.0)
		_draw_text(_short_text(str(item.get("emoji", "📥")), 2), rect.position + Vector2(16, 38), 22, ThemeScript.TEXT)
		_draw_text(_short_text(str(item.get("name", "Inbox")), 34), rect.position + Vector2(56, 26), 16, ThemeScript.TEXT)
		var summary := str(item.get("total_tasks", 0)) + " tasks • " + str(item.get("active_tasks", 0)) + " active"
		if int(item.get("overdue", 0)) > 0:
			summary = str(item.get("total_tasks", 0)) + " tasks • " + str(item.get("overdue", 0)) + " overdue"
		elif int(item.get("due_today", 0)) > 0:
			summary = str(item.get("total_tasks", 0)) + " tasks • " + str(item.get("due_today", 0)) + " due today"
		var color := ThemeScript.WARNING if int(item.get("overdue", 0)) > 0 else ThemeScript.TEXT_MUTED
		_draw_text(_short_text(summary, 44), rect.position + Vector2(56, 48), 11, color)
	_draw_scrollbar(view, todo_scroll_y, _todo_lists_content_height())

func _draw_todo_task_list() -> void:
	var list_raw = todo_tasks_data.get("list", {})
	var list_item: Dictionary = list_raw if list_raw is Dictionary else {}
	_draw_button(Rect2(30, 70, 74, 30), "Back", false)
	_draw_text(_short_text(str(list_item.get("name", "Inbox")), 32), Vector2(118, 48), 20, ThemeScript.TEXT)
	_draw_button(Rect2(400, 26, 92, 30), "Add Task", false)
	var view := _todo_tasks_scroll_rect()
	_draw_text("Active", Vector2(44, 128 - todo_task_scroll_y), 14, ThemeScript.TEXT_MUTED)
	var active := _todo_active_tasks()
	for index in range(active.size()):
		_draw_todo_task_row(_todo_task_row_rect(index, false), active[index] as Dictionary, view, false)
	var completed_y := 168.0 + float(active.size()) * 48.0 - todo_task_scroll_y
	_draw_text("Completed", Vector2(44, completed_y), 14, ThemeScript.TEXT_MUTED)
	var completed := _todo_completed_tasks()
	for index in range(completed.size()):
		_draw_todo_task_row(_todo_task_row_rect(index, true), completed[index] as Dictionary, view, true)
	_draw_scrollbar(view, todo_task_scroll_y, _todo_tasks_content_height())

func _draw_todo_task_row(rect: Rect2, task: Dictionary, view: Rect2, completed: bool) -> void:
	if not _rect_visible(rect, view):
		return
	var selected := int(task.get("id", 0)) == todo_selected_task_id
	_draw_rounded_rect(rect, Color(0.120, 0.132, 0.158, 1.0) if selected else Color(0.070, 0.080, 0.098, 1.0), 12.0)
	_draw_text("✓" if completed else "○", rect.position + Vector2(12, 25), 13, ThemeScript.TEXT_MUTED)
	var title_color := ThemeScript.TEXT_MUTED if completed else ThemeScript.TEXT
	_draw_text(_short_text(str(task.get("title", "Task")), 42), rect.position + Vector2(38, 17), 12, title_color)
	var detail := "Completed" if completed else _todo_task_detail_line(task)
	_draw_text(_short_text(detail, 56), rect.position + Vector2(38, 33), 9, ThemeScript.TEXT_MUTED)

func _draw_todo_list_form() -> void:
	_draw_rounded_rect(Rect2(24, 104, 592, 336), Color(0.040, 0.047, 0.060, 0.985), 18.0)
	_draw_text("New List", Vector2(44, 132), 20, ThemeScript.TEXT)
	_draw_study_row(Rect2(44, 150, 120, 34), "Emoji", todo_list_form_emoji)
	_draw_study_row(Rect2(178, 150, 418, 34), "List name", todo_list_form_name if todo_list_form_name != "" else "Study")
	_draw_button(Rect2(44, 390, 170, 34), "Done", false)
	_draw_button(Rect2(232, 390, 170, 34), "Cancel", false)

func _draw_todo_task_form() -> void:
	_draw_rounded_rect(Rect2(24, 92, 592, 368), Color(0.040, 0.047, 0.060, 0.985), 18.0)
	_draw_text("Edit Task" if todo_selected_task_id > 0 else "Add Task", Vector2(44, 110), 18, ThemeScript.TEXT)
	_draw_study_row(Rect2(44, 118, 552, 32), "Task", todo_form_title if todo_form_title != "" else "Tap to type")
	_draw_study_row(Rect2(44, 156, 552, 32), "Notes", todo_form_notes if todo_form_notes != "" else "Optional")
	_draw_button(Rect2(44, 202, 120, 32), "Reminder", todo_form_reminder_enabled)
	_draw_reminder_form_field(Rect2(178, 202, 180, 32), "Date", todo_form_date)
	_draw_reminder_form_field(Rect2(374, 202, 120, 32), "Time", todo_form_time)
	_draw_button(Rect2(44, 250, 170, 32), _todo_repeat_label(), false)
	_draw_button(Rect2(230, 250, 48, 32), "-", false)
	_draw_button(Rect2(288, 250, 48, 32), "+", false)
	_draw_text("Repeat: None / Every X hours / Every X days / Weekly / Monthly / Yearly", Vector2(48, 308), 9, ThemeScript.TEXT_DIM)
	_draw_text("Snooze: 10 minutes / 30 minutes / 1 hour / Tomorrow", Vector2(48, 328), 9, ThemeScript.TEXT_DIM)
	_draw_button(Rect2(44, 390, 170, 34), "Done", false)
	_draw_button(Rect2(232, 390, 170, 34), "Cancel", false)

func _draw_todo_task_detail() -> void:
	_draw_rounded_rect(Rect2(24, 86, 592, 354), Color(0.045, 0.052, 0.064, 0.98), 18.0)
	_draw_text(_short_text(str(todo_selected_task.get("title", "Task Details")), 48), Vector2(44, 124), 20, ThemeScript.TEXT)
	_draw_text(_short_text(str(todo_selected_task.get("notes", "No notes")), 74), Vector2(44, 154), 11, ThemeScript.TEXT_MUTED)
	_draw_study_row(Rect2(44, 190, 552, 34), "Reminder", _todo_task_detail_line(todo_selected_task))
	_draw_study_row(Rect2(44, 234, 552, 34), "Repeat", _todo_task_repeat_line(todo_selected_task))
	_draw_study_row(Rect2(44, 278, 552, 34), "Status", str(todo_selected_task.get("status", "active")).capitalize())
	var primary := "Mark Active" if str(todo_selected_task.get("status", "active")) == "completed" else "Mark Done"
	_draw_button(Rect2(44, 386, 116, 34), primary, false)
	_draw_button(Rect2(174, 386, 92, 34), "Edit", false)
	_draw_button(Rect2(280, 386, 92, 34), "Delete", false)
	_draw_button(Rect2(386, 386, 92, 34), "Close", false)

func _todo_task_detail_line(task: Dictionary) -> String:
	var due_date := str(task.get("due_date", ""))
	var due_time := str(task.get("due_time", ""))
	if due_date == "" or due_time == "":
		return "No reminder"
	var prefix := "Overdue • " if bool(task.get("overdue", false)) else ""
	return prefix + due_date + " " + due_time

func _todo_task_repeat_line(task: Dictionary) -> String:
	var unit := str(task.get("repeat_unit", "none"))
	var interval := int(task.get("repeat_interval", 0))
	if unit == "hours":
		return "Every " + str(interval) + " hours"
	if unit == "days":
		return "Every " + str(interval) + " days"
	if unit == "weekly":
		return "Weekly"
	if unit == "monthly":
		return "Monthly"
	if unit == "yearly":
		return "Yearly"
	return "None"

func _calendar_weekday_rect(index: int) -> Rect2:
	return Rect2(34.0 + float(index) * 82.0, 78.0, 76.0, 20.0)

func _calendar_cell_rect(index: int) -> Rect2:
	return Rect2(34.0 + float(index % 7) * 82.0, 102.0 + float(int(index / 7)) * 43.0, 76.0, 38.0)

func _calendar_event_row_rect(index: int) -> Rect2:
	return Rect2(360, 400 + float(index) * 28.0 - calendar_event_scroll_y, 224, 24)

func _calendar_cells() -> Array:
	var weeks_raw = calendar_data.get("weeks", [])
	var cells: Array = []
	if weeks_raw is Array:
		for raw_week in weeks_raw:
			var week: Dictionary = raw_week as Dictionary
			var raw_cells = week.get("cells", [])
			if raw_cells is Array:
				for raw_cell in raw_cells:
					cells.append(raw_cell)
	return cells

func _calendar_day_events() -> Array:
	var raw_events = calendar_day_data.get("events", [])
	return raw_events if raw_events is Array else []

func _calendar_select_cell(index: int) -> void:
	var cells := _calendar_cells()
	if index >= cells.size():
		return
	var cell: Dictionary = cells[index] as Dictionary
	calendar_selected_date = str(cell.get("full_date", calendar_selected_date))
	calendar_selected_event_id = 0
	calendar_selected_event = {}
	calendar_mode = "details"
	_request_calendar_month()
	_request_calendar_day()
	_request_redraw()

func _calendar_month_name(month_number: int) -> String:
	var names := ["", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
	if month_number >= 1 and month_number <= 12:
		return str(names[month_number])
	return "Calendar"

func _draw_reminders() -> void:
	draw_rect(Rect2(Vector2.ZERO, Vector2(WIDTH, HEIGHT)), _theme_background_color(), true)
	_draw_text("Reminders", Vector2(26, 44), 26, ThemeScript.TEXT)
	_draw_text("Local alerts and past reminders", Vector2(28, 66), 11, ThemeScript.TEXT_MUTED)
	_draw_pill(Rect2(520, 22, 92, 34), Color(0.10, 0.11, 0.13, 0.94), false)
	_draw_centered_text("Home", 566.0, 43.0, 12, ThemeScript.TEXT_MUTED)
	if reminders_mode == "add" or reminders_mode == "edit":
		_draw_reminders_form()
	else:
		_draw_button(Rect2(44, 88, 160, 34), "Add Reminder", false)
		_draw_button(Rect2(220, 88, 160, 34), "Edit", reminders_selected_id > 0)
		_draw_button(Rect2(396, 88, 160, 34), "Delete", reminders_selected_id > 0)
		var selected_title := "Selected: " + _short_text(str(reminders_selected_item.get("title", "None")), 34) if reminders_selected_id > 0 else "Selected: none"
		var selected_due := "Due: " + str(reminders_selected_item.get("due_at", "")) if reminders_selected_id > 0 else "Due: none"
		_draw_study_row(Rect2(44, 132, 552, 34), selected_title, selected_due)
		_draw_reminders_table("Upcoming", "upcoming", _reminders_upcoming_scroll_rect(), reminders_upcoming_scroll_y)
		_draw_reminders_table("Past", "past", _reminders_past_scroll_rect(), reminders_past_scroll_y)
	if reminders_mode == "delete_confirm":
		_draw_rounded_rect(Rect2(62, 286, 516, 128), Color(0.08, 0.04, 0.045, 0.98), 18.0)
		_draw_rounded_outline(Rect2(62, 286, 516, 128), Color(1.0, 0.22, 0.22, 0.45), 18.0)
		_draw_text("Delete selected reminder?", Vector2(84, 320), 17, ThemeScript.TEXT)
		_draw_text("This cannot be undone.", Vector2(84, 344), 11, ThemeScript.TEXT_MUTED)
		_draw_button(Rect2(78, 354, 210, 42), "Cancel", false)
		_draw_button(Rect2(352, 354, 210, 42), "Confirm delete", true)
	if reminders_status_text != "":
		_draw_text(_short_text(reminders_status_text, 74), Vector2(34, 460), 10, ThemeScript.TEXT_DIM)
	if text_input_open:
		_draw_text_input_overlay()

func _draw_reminders_table(title: String, kind: String, view_rect: Rect2, scroll_y: float) -> void:
	_draw_text(title, view_rect.position + Vector2(0, -10), 15, ThemeScript.TEXT)
	_draw_rounded_rect(view_rect, Color(0.060, 0.068, 0.082, 0.96), 12.0)
	var rows_raw = reminders_data.get(kind, [])
	if not (rows_raw is Array) or rows_raw.is_empty():
		_draw_text("No reminders", view_rect.position + Vector2(14, 34), 11, ThemeScript.TEXT_MUTED)
	else:
		var rows: Array = rows_raw
		for index in range(rows.size()):
			var item: Dictionary = rows[index] as Dictionary
			var row_rect := _reminder_row_rect(kind, index)
			if not _rect_visible(row_rect, view_rect):
				continue
			var selected := int(item.get("id", 0)) == reminders_selected_id
			_draw_tile(row_rect, selected)
			_draw_text("✓" if selected else "○", row_rect.position + Vector2(8, 22), 11, ThemeScript.TEXT_MUTED)
			_draw_text(_short_text(str(item.get("title", "Reminder")), 20), row_rect.position + Vector2(30, 17), 11, ThemeScript.TEXT)
			_draw_text(_short_text(str(item.get("due_at", "")).replace("T", " "), 22), row_rect.position + Vector2(30, 31), 9, ThemeScript.TEXT_MUTED)
			if bool(item.get("is_private", false)):
				_draw_text("P", row_rect.position + Vector2(220, 22), 10, ThemeScript.TEXT_MUTED)
	_draw_scrollbar(view_rect, scroll_y, _reminders_content_height(kind))

func _draw_reminders_form() -> void:
	_draw_text("Add Reminder" if reminders_mode == "add" else "Edit Reminder", Vector2(44, 104), 19, ThemeScript.TEXT)
	_draw_study_row(Rect2(44, 136, 552, 34), "Reminder text", reminders_form_title if reminders_form_title != "" else "Tap to type")
	_draw_study_row(Rect2(44, 178, 552, 34), "Notes", reminders_form_notes if reminders_form_notes != "" else "Optional")
	_draw_reminder_form_field(Rect2(44, 220, 260, 34), "Date", reminders_form_date)
	_draw_reminder_form_field(Rect2(324, 220, 170, 34), "Time", reminders_form_time)
	_draw_button(Rect2(510, 220, 86, 34), "Private", reminders_form_private)
	_draw_button(Rect2(44, 274, 76, 30), "+5m", false)
	_draw_button(Rect2(130, 274, 76, 30), "+15m", false)
	_draw_button(Rect2(216, 274, 76, 30), "+30m", false)
	_draw_button(Rect2(302, 274, 76, 30), "+1h", false)
	_draw_button(Rect2(388, 274, 92, 30), "Tomorrow", false)
	_draw_button(Rect2(490, 274, 106, 30), "Next week", false)
	_draw_study_row(Rect2(44, 326, 552, 34), "Reminder", reminders_form_date + " " + reminders_form_time)
	_draw_text("This reminder will appear in Past." if _reminders_due_at_text() < Time.get_datetime_string_from_system(false, true) else "Upcoming reminder", Vector2(48, 374), 10, ThemeScript.TEXT_MUTED)
	_draw_button(Rect2(44, 390, 170, 34), "Save", false)
	_draw_button(Rect2(232, 390, 170, 34), "Cancel", false)

func _draw_study_home() -> void:
	for index in range(STUDY_TILES.size()):
		var rect: Rect2 = _study_tile_rect(index)
		var tile: Dictionary = STUDY_TILES[index] as Dictionary
		_draw_tile(rect, str(tile["title"]) == "Study Stats")
		_draw_text(str(tile["title"]), rect.position + Vector2(16, 28), 15, ThemeScript.TEXT)
		_draw_text(str(tile["subtitle"]), rect.position + Vector2(16, 49), 10, ThemeScript.TEXT_MUTED)

func _study_tile_rect(index: int) -> Rect2:
	var column: int = index % 2
	var row: int = int(index / 2)
	return Rect2(28.0 + float(column) * 300.0, 96.0 + float(row) * 72.0, 284.0, 58.0)

func _draw_study_pomodoro() -> void:
	_draw_text("Pomodoro", Vector2(44, 102), 20, ThemeScript.TEXT)
	_draw_study_row(Rect2(44, 118, 552, 38), "Topic", study_topic_text if study_topic_text != "" else "Tap to type")
	_draw_button(Rect2(44, 166, 120, 34), "-5 min", false)
	_draw_button(Rect2(176, 166, 120, 34), "+" + str(study_planned_minutes) + " min", false)
	_draw_button(Rect2(308, 166, 120, 34), "Break " + str(study_break_minutes), study_break_minutes > 0)
	_draw_button(Rect2(44, 216, 260, 42), "Start Focus", false)
	_draw_button(Rect2(324, 216, 260, 42), "Stop Focus", false)
	if bool(study_timer_data.get("active", false)):
		_draw_study_row(Rect2(44, 276, 552, 38), "Active", "Remaining " + str(int(study_timer_data.get("remaining_seconds", 0) / 60)) + "m")

func _draw_study_smart() -> void:
	_draw_text("Smart Study", Vector2(44, 102), 20, ThemeScript.TEXT)
	_draw_study_row(Rect2(44, 118, 350, 36), "Topic", study_topic_text if study_topic_text != "" else "Tap to type")
	_draw_study_row(Rect2(44, 164, 350, 36), "Goal", study_goal_text if study_goal_text != "" else "Tap to type")
	_draw_button(Rect2(420, 118, 170, 32), "+ Focus", false)
	_draw_button(Rect2(420, 156, 170, 32), "+ Break", false)
	_draw_button(Rect2(420, 194, 170, 32), "Remove", study_segments.size() > 1)
	_draw_button(Rect2(420, 232, 80, 32), "-5", false)
	_draw_button(Rect2(510, 232, 80, 32), "+5", false)
	var total_focus := 0
	var total_break := 0
	var view_rect: Rect2 = _study_segment_scroll_rect()
	_draw_text("Segments", Vector2(48, 206), 11, ThemeScript.TEXT_MUTED)
	for index in range(study_segments.size()):
		var segment: Dictionary = study_segments[index] as Dictionary
		var minutes := int(segment.get("minutes", 0))
		if str(segment.get("type", "focus")) == "break":
			total_break += minutes
		else:
			total_focus += minutes
		var rect: Rect2 = _study_segment_row_rect(index)
		if not _rect_visible(rect, view_rect):
			continue
		var marker := ">" if index == study_selected_segment_index else " "
		_draw_tile(rect, index == study_selected_segment_index)
		_draw_text(marker + " " + str(index + 1) + ". " + str(segment.get("type", "focus")).capitalize() + " " + str(minutes) + "m", rect.position + Vector2(8, 17), 11, ThemeScript.TEXT)
	_draw_scrollbar(view_rect, study_segment_scroll_y, _study_segment_content_height())
	_draw_study_row(Rect2(44, 374, 354, 30), "Focus total", str(total_focus) + "m")
	_draw_study_row(Rect2(44, 408, 170, 28), "Break total", str(total_break) + "m")
	_draw_study_row(Rect2(224, 408, 174, 28), "Segments", str(study_segments.size()))
	var validation := _validate_study_segments()
	_draw_text(_short_text("Validation: " + (validation if validation != "" else "Ready"), 58), Vector2(48, 454), 10, ThemeScript.TEXT_MUTED)
	if bool(study_timer_data.get("active", false)):
		var remaining: int = int(study_timer_data.get("remaining_seconds", 0))
		_draw_text(str(study_timer_data.get("kind", "focus")).capitalize() + ": %02d:%02d" % [int(remaining / 60), remaining % 60], Vector2(424, 286), 13, ThemeScript.TEXT)
		if bool(study_timer_data.get("note_prompt_pending", false)) and _study_current_segment_is_focus():
			_draw_text("What did you learn?", Vector2(424, 320), 12, ThemeScript.TEXT)
			_draw_button(Rect2(424, 334, 76, 30), "Add note", false)
			_draw_button(Rect2(510, 334, 76, 30), "Skip", false)
		_draw_button(Rect2(424, 374, 76, 28), "Stop", false)
		_draw_button(Rect2(510, 374, 76, 28), "Finish", false)
	else:
		_draw_button(Rect2(420, 274, 170, 34), "Start", false)

func _draw_study_flashcards() -> void:
	_draw_text("Flashcards", Vector2(44, 102), 20, ThemeScript.TEXT)
	_draw_button(Rect2(44, 118, 170, 38), "New Flashcards", false)
	_draw_button(Rect2(232, 118, 170, 38), "Add Question", study_selected_deck_id > 0)
	_draw_button(Rect2(420, 118, 170, 38), "Start Study", study_selected_deck_id > 0)
	_draw_button(Rect2(44, 164, 170, 34), "Delete Flashcards", study_selected_deck_id > 0)
	if study_flashcard_mode == "practice" and study_selected_card.has("id"):
		var title := str(study_data.get("deck", {}).get("name", "Flashcards")) if study_data.get("deck", {}) is Dictionary else "Flashcards"
		_draw_text(_short_text(title, 40), Vector2(48, 176), 14, ThemeScript.TEXT)
		_draw_text("Question " + str(study_selected_card.get("question_number", 1)) + "/" + str(maxi(1, int(study_data.get("card_count", 1)))), Vector2(48, 194), 10, ThemeScript.TEXT_MUTED)
		_draw_study_row(Rect2(44, 204, 552, 38), "Question", str(study_selected_card.get("question", "")))
		_draw_study_row(Rect2(44, 244, 552, 28), "Answer input", study_flashcard_answer_text if study_flashcard_answer_text != "" else "Tap Type Answer")
		_draw_button(Rect2(44, 278, 170, 30), "Type Answer", false)
		_draw_button(Rect2(232, 278, 170, 30), "Check Answer", study_flashcard_answer_text.strip_edges() != "")
		_draw_button(Rect2(420, 278, 170, 30), "Reveal Answer", study_selected_card.has("id"))
		_draw_button(Rect2(44, 316, 160, 30), "I know this", study_flashcard_answer_checked or study_flashcard_revealed_answer)
		_draw_button(Rect2(220, 316, 160, 30), "Not sure", study_flashcard_answer_checked or study_flashcard_revealed_answer)
		_draw_button(Rect2(396, 316, 160, 30), "I don't know", study_flashcard_answer_checked or study_flashcard_revealed_answer)
		_draw_button(Rect2(44, 354, 170, 30), "Next", false)
		_draw_button(Rect2(232, 354, 170, 30), "Finish", false)
		_draw_study_feedback(Rect2(44, 394, 552, 50), study_flashcard_feedback_text, str(study_selected_card.get("status", "new")) + " · " + str(study_selected_card.get("correct_count", 0)) + " correct · " + str(study_selected_card.get("wrong_count", 0)) + " wrong")
	elif study_flashcard_mode == "finished":
		_draw_text("Flashcards finished. Finish or continue?", Vector2(48, 210), 13, ThemeScript.TEXT)
		_draw_button(Rect2(44, 390, 170, 34), "Finish", false)
		_draw_button(Rect2(232, 390, 170, 34), "Continue", false)
	else:
		var selected_label := "Selected set " + str(study_selected_deck_id) if study_selected_deck_id > 0 else "Select one flashcard set"
		_draw_selected_study_item("Flashcards", {"question": selected_label, "status": "Single selected set"}, "question", "status", 204)
		if study_data.has("cards"):
			_draw_study_list("cards", "question", "status", "", 226)
		else:
			_draw_study_list("decks", "name", "card_count", "cards", 226)
	if study_flashcard_delete_confirm_open:
		_draw_rounded_rect(Rect2(62, 286, 516, 128), Color(0.08, 0.04, 0.045, 0.98), 18.0)
		_draw_rounded_outline(Rect2(62, 286, 516, 128), Color(1.0, 0.22, 0.22, 0.45), 18.0)
		_draw_text("Delete selected Flashcards?", Vector2(84, 320), 17, ThemeScript.TEXT)
		_draw_text("This cannot be undone.", Vector2(84, 344), 11, ThemeScript.TEXT_MUTED)
		_draw_button(Rect2(78, 354, 210, 42), "Cancel", false)
		_draw_button(Rect2(352, 354, 210, 42), "Confirm delete", true)

func _draw_study_quizzes() -> void:
	_draw_text("Quizzes", Vector2(44, 102), 20, ThemeScript.TEXT)
	_draw_button(Rect2(44, 118, 170, 38), "New Quiz", false)
	_draw_button(Rect2(232, 118, 170, 38), "Add Question", study_selected_quiz_id > 0)
	_draw_button(Rect2(420, 118, 170, 38), "Start Quiz", study_selected_quiz_id > 0)
	_draw_button(Rect2(44, 164, 170, 34), "Delete Quiz", study_selected_quiz_id > 0)
	if study_pending_quiz_question != "":
		_draw_text("Choose correct answer", Vector2(48, 166), 11, ThemeScript.TEXT_MUTED)
		_draw_button(Rect2(44, 174, 56, 32), "A", study_pending_correct_answer == "A")
		_draw_button(Rect2(108, 174, 56, 32), "B", study_pending_correct_answer == "B")
		_draw_button(Rect2(172, 174, 56, 32), "C", study_pending_correct_answer == "C")
		_draw_button(Rect2(236, 174, 56, 32), "D", study_pending_correct_answer == "D")
		_draw_button(Rect2(308, 174, 142, 32), "Save question", false)
	if study_quiz_mode == "play" and study_selected_question.has("id"):
		_draw_text("Question " + str(study_selected_question.get("question_number", 1)), Vector2(48, 204), 11, ThemeScript.TEXT_MUTED)
		_draw_study_row(Rect2(44, 208, 552, 24), "Question", str(study_selected_question.get("question", "")))
		_draw_button(Rect2(44, 238, 260, 32), "A. " + _short_text(str(study_selected_question.get("answer_a", "")), 26), false)
		_draw_button(Rect2(324, 238, 260, 32), "B. " + _short_text(str(study_selected_question.get("answer_b", "")), 26), false)
		_draw_button(Rect2(44, 276, 260, 32), "C. " + _short_text(str(study_selected_question.get("answer_c", "")), 26), false)
		_draw_button(Rect2(324, 276, 260, 32), "D. " + _short_text(str(study_selected_question.get("answer_d", "")), 26), false)
		_draw_study_feedback(Rect2(44, 316, 552, 30), study_quiz_feedback_text, str(study_selected_question.get("status", "new")))
		_draw_button(Rect2(44, 354, 170, 30), "Mark for review", false)
		_draw_button(Rect2(232, 354, 170, 30), "Next", study_quiz_answered)
		_draw_button(Rect2(420, 354, 170, 30), "Finish", false)
	elif study_quiz_mode == "finished":
		_draw_text("Quiz finished.", Vector2(48, 210), 13, ThemeScript.TEXT)
		_draw_button(Rect2(44, 390, 170, 30), "Finish", false)
		_draw_button(Rect2(232, 390, 170, 30), "Repeat wrong", false)
		_draw_button(Rect2(420, 390, 170, 30), "Repeat marked", false)
	else:
		if study_data.has("questions"):
			_draw_study_list("questions", "question", "status", "", 226)
		else:
			_draw_study_list("quizzes", "name", "question_count", "questions", 226)
	if study_quiz_delete_confirm_open:
		_draw_rounded_rect(Rect2(62, 286, 516, 128), Color(0.08, 0.04, 0.045, 0.98), 18.0)
		_draw_rounded_outline(Rect2(62, 286, 516, 128), Color(1.0, 0.22, 0.22, 0.45), 18.0)
		_draw_text("Delete selected Quiz?", Vector2(84, 320), 17, ThemeScript.TEXT)
		_draw_text("This cannot be undone.", Vector2(84, 344), 11, ThemeScript.TEXT_MUTED)
		_draw_button(Rect2(78, 354, 210, 42), "Cancel", false)
		_draw_button(Rect2(352, 354, 210, 42), "Confirm delete", true)

func _draw_study_languages() -> void:
	_draw_text("Languages", Vector2(44, 102), 20, ThemeScript.TEXT)
	_draw_button(Rect2(44, 118, 170, 38), "New List", false)
	_draw_button(Rect2(232, 118, 170, 38), "Add Word", study_selected_language_list_id > 0)
	_draw_button(Rect2(420, 118, 170, 38), "Edit List", study_selected_language_list_id > 0)
	_draw_button(Rect2(44, 164, 170, 34), "Start Practice", study_selected_language_list_id > 0)
	_draw_button(Rect2(232, 164, 170, 34), "Delete List", study_selected_language_list_id > 0)
	if study_language_mode == "practice" and study_selected_word.has("id"):
		_draw_text("Word " + str(study_selected_word.get("question_number", 1)), Vector2(48, 204), 11, ThemeScript.TEXT_MUTED)
		_draw_study_row(Rect2(44, 214, 552, 34), "Word", str(study_selected_word.get("word", "")))
		_draw_study_row(Rect2(44, 244, 552, 28), "Meaning input", study_language_answer_text if study_language_answer_text != "" else "Tap to type meaning")
		_draw_button(Rect2(44, 278, 170, 30), "Type Meaning", false)
		_draw_button(Rect2(232, 278, 170, 30), "Check Answer", study_language_answer_text.strip_edges() != "")
		_draw_button(Rect2(420, 278, 170, 30), "Reveal Answer", study_selected_word.has("id"))
		_draw_button(Rect2(44, 316, 170, 30), "Correct", study_language_answer_checked or study_language_revealed_word)
		_draw_button(Rect2(232, 316, 170, 30), "Wrong", study_language_answer_checked or study_language_revealed_word)
		_draw_button(Rect2(44, 354, 170, 30), "Next", false)
		_draw_button(Rect2(232, 354, 170, 30), "Finish", false)
		_draw_study_feedback(Rect2(44, 394, 552, 50), study_language_feedback_text, str(study_selected_word.get("status", "new")) + " · " + str(study_selected_word.get("correct_count", 0)) + " correct · " + str(study_selected_word.get("wrong_count", 0)) + " wrong")
	elif study_language_mode == "finished":
		_draw_text("Language practice finished.", Vector2(48, 210), 13, ThemeScript.TEXT)
		_draw_button(Rect2(44, 390, 170, 30), "Finish", false)
	elif study_language_mode == "edit":
		_draw_selected_study_item("Language list", {"id": study_selected_language_list_id, "question": "Selected list " + str(study_selected_language_list_id), "status": "Edit mode"}, "question", "status", 204)
		_draw_study_list("words", "word", "status", "", 226)
		_draw_button(Rect2(44, 390, 170, 30), "Add Word", false)
		_draw_button(Rect2(232, 390, 170, 30), "Delete Word", study_selected_language_word_id > 0)
		_draw_button(Rect2(420, 390, 170, 30), "Back to Lists", false)
	else:
		var selected_label := "Selected language list " + str(study_selected_language_list_id) if study_selected_language_list_id > 0 else "Select one language list"
		_draw_selected_study_item("Language list", {"question": selected_label, "status": "Single selected list"}, "question", "status", 204)
		_draw_study_list("lists", "name", "word_count", "words", 226)
	if study_language_delete_confirm_open:
		_draw_rounded_rect(Rect2(62, 286, 516, 128), Color(0.08, 0.04, 0.045, 0.98), 18.0)
		_draw_rounded_outline(Rect2(62, 286, 516, 128), Color(1.0, 0.22, 0.22, 0.45), 18.0)
		_draw_text("Delete selected language list?", Vector2(84, 320), 17, ThemeScript.TEXT)
		_draw_text("This cannot be undone.", Vector2(84, 344), 11, ThemeScript.TEXT_MUTED)
		_draw_button(Rect2(78, 354, 210, 42), "Cancel", false)
		_draw_button(Rect2(352, 354, 210, 42), "Confirm delete", true)

func _draw_study_stats() -> void:
	_draw_text("Study Stats", Vector2(44, 102), 20, ThemeScript.TEXT)
	var cards: Array = [
		{"title": "Minutes", "value": str(study_data.get("total_study_minutes", "Pending"))},
		{"title": "Pomodoro", "value": str(study_data.get("total_pomodoro_sessions", "Pending"))},
		{"title": "Smart", "value": str(study_data.get("total_smart_study_sessions", "Pending"))},
		{"title": "Decks", "value": str(study_data.get("total_flashcard_decks", "Pending"))},
		{"title": "Cards", "value": str(study_data.get("total_flashcards", "Pending"))},
		{"title": "Quizzes", "value": str(study_data.get("total_quiz_sets", "Pending"))},
		{"title": "Words", "value": str(study_data.get("total_language_words", "Pending"))},
		{"title": "Mastered", "value": str(study_data.get("mastered_language_words", "Pending"))}
	]
	for index in range(cards.size()):
		var rect: Rect2 = Rect2(44.0 + float(index % 2) * 276.0, 126.0 + float(int(index / 2)) * 48.0, 252.0, 38.0)
		var item: Dictionary = cards[index] as Dictionary
		_draw_study_row(rect, str(item["title"]), str(item["value"]))
	_draw_study_topic_stats(326)

func _draw_study_topic_stats(y_start: float) -> void:
	_draw_text("Topics", Vector2(48, y_start), 14, ThemeScript.TEXT)
	var rows_raw = study_data.get("per_topic_stats", [])
	if not (rows_raw is Array) or rows_raw.is_empty():
		_draw_text("No study data yet", Vector2(48, y_start + 26), 11, ThemeScript.TEXT_MUTED)
		return
	var rows: Array = rows_raw
	for index in range(mini(rows.size(), 3)):
		var item: Dictionary = rows[index] as Dictionary
		_draw_study_row(Rect2(44, y_start + 20 + index * 38, 552, 32), str(item.get("topic", "Topic")), str(item.get("sessions", 0)) + "x · " + str(item.get("total_minutes", 0)) + "m")

func _draw_study_history() -> void:
	_draw_text("History", Vector2(44, 102), 20, ThemeScript.TEXT)
	var rows_raw = study_data.get("events", [])
	if not (rows_raw is Array) or rows_raw.is_empty():
		_draw_text("No study history yet", Vector2(48, 142), 12, ThemeScript.TEXT_MUTED)
		return
	var rows: Array = rows_raw
	for index in range(mini(rows.size(), 8)):
		var item: Dictionary = rows[index] as Dictionary
		_draw_study_row(Rect2(44, 126 + index * 38, 552, 32), str(item.get("event_type", "event")), str(item.get("summary", "")))

func _draw_study_settings() -> void:
	_draw_text("Study Settings", Vector2(44, 102), 20, ThemeScript.TEXT)
	_draw_study_row(Rect2(44, 126, 552, 34), "Database", str(study_data.get("database_size_bytes", "Pending")) + " bytes")
	_draw_study_row(Rect2(44, 168, 552, 34), "Sessions", str(study_data.get("total_pomodoro_sessions", "Pending")))
	_draw_study_row(Rect2(44, 210, 552, 34), "Decks/cards", str(study_data.get("total_flashcard_decks", "Pending")) + " / " + str(study_data.get("total_flashcards", "Pending")))
	_draw_study_row(Rect2(44, 252, 552, 34), "Quizzes/questions", str(study_data.get("total_quiz_sets", "Pending")) + " / " + str(study_data.get("total_quiz_questions", "Pending")))
	_draw_study_row(Rect2(44, 294, 552, 34), "Lists/words", str(study_data.get("total_language_lists", "Pending")) + " / " + str(study_data.get("total_language_words", "Pending")))
	_draw_button(Rect2(44, 390, 260, 42), "Delete all Study data", false)
	_draw_button(Rect2(324, 390, 260, 42), "Export planned", false)
	if study_delete_confirm_open:
		_draw_rounded_rect(Rect2(62, 286, 516, 128), Color(0.08, 0.04, 0.045, 0.98), 18.0)
		_draw_rounded_outline(Rect2(62, 286, 516, 128), Color(1.0, 0.22, 0.22, 0.45), 18.0)
		_draw_text("Delete all Study data?", Vector2(84, 320), 17, ThemeScript.TEXT)
		_draw_text("This cannot be undone.", Vector2(84, 344), 11, ThemeScript.TEXT_MUTED)
		_draw_button(Rect2(78, 354, 210, 42), "Cancel", false)
		_draw_button(Rect2(352, 354, 210, 42), "Confirm delete", true)

func _draw_study_row(rect: Rect2, title: String, value: String) -> void:
	_draw_tile(rect, false)
	_draw_text(_short_text(title, 26), rect.position + Vector2(12, 22), 12, ThemeScript.TEXT)
	_draw_text(_short_text(value, 34), rect.position + Vector2(210, 22), 10, ThemeScript.TEXT_MUTED)

func _draw_reminder_form_field(rect: Rect2, label: String, value: String) -> void:
	_draw_tile(rect, false)
	_draw_text(_short_text(label, 16), rect.position + Vector2(12, 14), 9, ThemeScript.TEXT_MUTED)
	_draw_centered_text(_short_text(value, 16), rect.position.x + rect.size.x * 0.5, rect.position.y + 25.0, 13, ThemeScript.TEXT)

func _draw_study_list(key: String, title_key: String, count_key: String, suffix: String, y_start: float) -> void:
	var rows_raw = study_data.get(key, [])
	if not (rows_raw is Array) or rows_raw.is_empty():
		_draw_text("No study data yet", Vector2(48, y_start + 18), 11, ThemeScript.TEXT_MUTED)
		return
	var rows: Array = rows_raw
	for index in range(mini(rows.size(), 5)):
		var item: Dictionary = rows[index] as Dictionary
		var rect := _study_list_rect(index)
		var active := (key == "decks" and int(item.get("id", 0)) == study_selected_deck_id) or (key == "quizzes" and int(item.get("id", 0)) == study_selected_quiz_id) or (key == "lists" and int(item.get("id", 0)) == study_selected_language_list_id) or (key == "words" and int(item.get("id", 0)) == study_selected_language_word_id)
		_draw_tile(rect, active)
		_draw_text(_short_text(str(item.get(title_key, "Item")), 26), rect.position + Vector2(12, 22), 12, ThemeScript.TEXT)
		_draw_text(_short_text(str(item.get(count_key, 0)) + " " + suffix, 34), rect.position + Vector2(210, 22), 10, ThemeScript.TEXT_MUTED)

func _draw_study_feedback(rect: Rect2, feedback: String, status: String) -> void:
	_draw_tile(rect, false)
	var color := ThemeScript.TEXT_MUTED
	if feedback.begins_with("Correct"):
		color = Color(0.30, 0.90, 0.52, 1.0)
	elif feedback.begins_with("Wrong") or feedback.begins_with("Incorrect"):
		color = Color(1.0, 0.32, 0.32, 1.0)
	elif feedback != "":
		color = Color(0.95, 0.78, 0.36, 1.0)
	_draw_text(_short_text(feedback if feedback != "" else "Feedback appears here", 72), rect.position + Vector2(12, 20), 13, color)
	_draw_text(_short_text("Status: " + status, 72), rect.position + Vector2(12, 40), 10, ThemeScript.TEXT_MUTED)

func _study_list_rect(index: int) -> Rect2:
	return Rect2(44, 226 + index * 42, 552, 34)

func _draw_selected_study_item(label: String, item: Dictionary, title_key: String, value_key: String, y: float) -> void:
	if not item.has("id"):
		_draw_study_row(Rect2(44, y, 552, 34), label, "Select an item")
	else:
		_draw_study_row(Rect2(44, y, 552, 34), str(item.get(title_key, label)), str(item.get(value_key, "")))

func _draw_text_input_overlay() -> void:
	_draw_rounded_rect(Rect2(22, 72, 596, 372), Color(0.040, 0.047, 0.060, 0.98), 24.0)
	_draw_rounded_outline(Rect2(22, 72, 596, 372), Color(1.0, 1.0, 1.0, 0.08), 24.0)
	_draw_text(text_input_title, Vector2(44, 108), 18, ThemeScript.TEXT)
	_draw_study_row(Rect2(44, 122, 552, 38), "Input", text_input_value)
	var keys := _text_input_keys()
	for index in range(keys.length()):
		var rect: Rect2 = _text_key_rect(index)
		_draw_button(rect, keys.substr(index, 1), false)
	if text_input_keyboard_mode == "text":
		_draw_button(Rect2(40, 386, 96, 34), "Space", false)
	_draw_button(Rect2(146, 386, 96, 34), "Back", false)
	_draw_button(Rect2(252, 386, 96, 34), "Clear", false)
	_draw_button(Rect2(412, 386, 82, 34), "Save", true)
	_draw_button(Rect2(504, 386, 82, 34), "Cancel", false)

func _text_key_rect(index: int) -> Rect2:
	var column: int = index % 9
	var row: int = int(index / 9)
	return Rect2(44.0 + float(column) * 58.0, 170.0 + float(row) * 38.0, 46.0, 28.0)

func _draw_about_settings(view_rect: Rect2) -> void:
	var rows: Array = [
		"Project: NeXa ToTem",
		"Smart Desk Companion",
		"Author: Andrzej Dul",
		"Brand/company: DevDul",
		"Hardware: Raspberry Pi 5 2GB",
		"Display: 2.8-inch HDMI IPS touch LCD, 640x480",
		"Camera: CSI camera, ov5647 when present",
		"Audio: USB speaker",
		"Planned sensors: BME680/BME688, LTR-329, CAP1188, sound sensor, RGB LEDs",
		"Remote: controller with screen/joystick and Remote Wi-Fi link planned",
		"Software: Godot LCD UI, Python localhost diagnostics/settings API",
		"Renderer: OpenGL ES Compatibility, fixed 640x480 window",
		"Features: Face Home, Menu, Clock, Control Center, Quick Shelf",
		"Diagnostics: Wi-Fi details, camera preview, audio, logs, reports, benchmarks",
		"Settings: Appearance, Notifications, Privacy/PIN, Modes, Quick Shelf",
		"More settings: Display, Sound, Network, Remote, Diagnostics, Safety/Exit",
		"Safety: Wi-Fi changes are dry-run/planned",
		"Safety: Exit and power actions are planned/safe only",
		"Camera preview is off by default and stops on close/stale timeout"
	]
	for index in range(rows.size()):
		var rect: Rect2 = Rect2(44, 120 + index * 34 - settings_scroll_y, 552, 30)
		if not _rect_visible(rect, view_rect):
			continue
		_draw_card_if_visible(rect, view_rect, Color(0.075, 0.085, 0.102, 0.94), 15.0)
		_draw_text_if_visible(_short_text(str(rows[index]), 78), rect.position + Vector2(12, 20), view_rect, 11, ThemeScript.TEXT_MUTED)

func _draw_placeholder(title: String) -> void:
	_draw_soft_panel(Rect2(76, 158, 488, 156), 32.0)
	_draw_centered_text(title, WIDTH * 0.5, 226.0, 26, ThemeScript.TEXT)
	_draw_centered_text("Press Escape to return home", WIDTH * 0.5, 258.0, 13, ThemeScript.TEXT_MUTED)
