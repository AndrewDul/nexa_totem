extends Control

const NavigationControllerScript := preload("res://scripts/navigation_controller.gd")
const GestureDetectorScript := preload("res://scripts/gesture_detector.gd")
const FaceRendererScript := preload("res://scripts/face_renderer.gd")
const DiagnosticsDataScript := preload("res://scripts/diagnostics_data.gd")
const ThemeScript := preload("res://scripts/theme.gd")

const WIDTH := 640.0
const HEIGHT := 480.0
const TARGET_REDRAW_FPS := 30.0
const REDRAW_INTERVAL := 1.0 / TARGET_REDRAW_FPS
const CLOCK_REDRAW_INTERVAL := 1.0
const TRANSITION_SECONDS := 0.14
const CLOSE_TRANSITION_SECONDS := 0.10
const MENU_TILES := [
	{"icon": "◷", "title": "Time", "subtitle": "Clock"},
	{"icon": "◌", "title": "Study", "subtitle": "Focus"},
	{"icon": "!", "title": "Reminders", "subtitle": "Alerts"},
	{"icon": "□", "title": "Calendar", "subtitle": "Events"},
	{"icon": "✓", "title": "Tasks", "subtitle": "To-do"},
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
	"Network"
]

var nav := NavigationControllerScript.new()
var gesture := GestureDetectorScript.new()
var face := FaceRendererScript.new()
var diagnostics_data := DiagnosticsDataScript.new()
var elapsed := 0.0
var active_tab := "Overview"
var panel_data := {}
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

func _ready() -> void:
	custom_minimum_size = Vector2(WIDTH, HEIGHT)
	panel_data = diagnostics_data.load_panel_data()
	set_process(true)
	_request_redraw()

func _process(delta: float) -> void:
	elapsed += delta
	redraw_accumulator += delta
	clock_redraw_accumulator += delta
	if transition_active:
		transition_progress = minf(1.0, transition_progress + delta / transition_duration)
		if transition_progress >= 1.0:
			transition_active = false
			if transition_closing:
				nav.current_screen = "Face Home"
			_request_redraw()
	# Redraw is throttled: Face Home and transitions animate at 30 FPS max,
	# static panels draw only after input/open/tab changes, and Clock ticks once per second.
	var animated := transition_active or nav.current_screen == "Face Home" or elapsed < nav.status_bubble_until
	var clock_tick := nav.current_screen == "Clock" and clock_redraw_accumulator >= CLOCK_REDRAW_INTERVAL
	if (animated or redraw_requested) and redraw_accumulator >= REDRAW_INTERVAL:
		redraw_accumulator = 0.0
		redraw_requested = false
		queue_redraw()
	elif clock_tick:
		clock_redraw_accumulator = 0.0
		queue_redraw()

func _gui_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.pressed:
		if event.button_index == MOUSE_BUTTON_WHEEL_UP:
			_handle_scroll_wheel(event.position, -28.0)
			return
		if event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			_handle_scroll_wheel(event.position, 28.0)
			return
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		if event.pressed:
			if _begin_scroll_drag(event.position):
				return
			else:
				gesture.begin(event.position, elapsed)
		else:
			if scroll_drag_active:
				scroll_drag_active = false
				scroll_drag_area = ""
				return
			_handle_gesture(gesture.finish(event.position, elapsed), event.position)
	if event is InputEventMouseMotion and gesture.is_pressed:
		gesture.update(event.position)
	if event is InputEventMouseMotion and scroll_drag_active:
		_update_scroll_drag(event.position)

func _unhandled_key_input(event: InputEvent) -> void:
	if not event.pressed:
		return
	if event.keycode == KEY_LEFT and nav.current_screen == "Face Home":
		_open_menu()
	elif event.keycode == KEY_RIGHT and nav.current_screen == "Face Home":
		_open_clock()
	elif event.keycode == KEY_DOWN and nav.current_screen == "Face Home":
		_open_control_center()
	elif event.keycode == KEY_ESCAPE:
		_go_home()
	_request_redraw()

func _handle_gesture(action: String, position: Vector2) -> void:
	if action == "tap":
		_handle_tap(position)
	elif action == "long_press" and nav.current_screen == "Face Home":
		_open_settings_placeholder()
	elif nav.current_screen == "Face Home":
		if action == "swipe_left":
			_open_menu()
		elif action == "swipe_right":
			_open_clock()
		elif action == "swipe_down":
			_open_control_center()
	elif nav.current_screen == "Menu" and action == "swipe_right":
		_go_home()
	elif nav.current_screen == "Clock" and action == "swipe_left":
		_go_home()
	elif nav.current_screen == "Notification Control Center" and action == "swipe_up":
		_go_home()
	_request_redraw()

func _handle_tap(position: Vector2) -> void:
	if nav.current_screen == "Face Home":
		nav.show_status_bubble(elapsed)
		return
	if nav.current_screen == "Menu":
		_handle_menu_tap(position)
		return
	if nav.current_screen == "Notification Control Center":
		if position.y > 112.0 and position.y < 278.0 and position.x > 408.0:
			_open_diagnostics()
		return
	if nav.current_screen == "Diagnostics":
		if Rect2(536, 22, 78, 34).has_point(position):
			_go_home()
			return
		_handle_diagnostics_tap(position)

func _handle_menu_tap(position: Vector2) -> void:
	for index in range(MENU_TILES.size()):
		var rect: Rect2 = _menu_tile_rect(index)
		if rect.has_point(position):
			var tile: Dictionary = MENU_TILES[index] as Dictionary
			if tile["title"] == "Diagnostics":
				_open_diagnostics()
			else:
				_open_placeholder(tile["title"] + " placeholder")
			return

func _handle_diagnostics_tap(position: Vector2) -> void:
	for index in range(DIAGNOSTIC_TABS.size()):
		var rect: Rect2 = _diagnostic_tab_rect(index)
		if rect.has_point(position):
			active_tab = str(DIAGNOSTIC_TABS[index])
			diagnostic_scroll_y = 0.0
			_request_redraw()
			return

func _begin_scroll_drag(position: Vector2) -> bool:
	if nav.current_screen == "Diagnostics" and _diagnostics_scroll_rect().has_point(position) and _diagnostics_max_scroll() > 0.0:
		scroll_drag_active = true
		scroll_drag_area = "diagnostics"
		scroll_drag_last_y = position.y
		return true
	if nav.current_screen == "Notification Control Center" and _control_scroll_rect().has_point(position) and _control_center_max_scroll() > 0.0:
		scroll_drag_active = true
		scroll_drag_area = "control"
		scroll_drag_last_y = position.y
		return true
	return false

func _update_scroll_drag(position: Vector2) -> void:
	var delta_y: float = scroll_drag_last_y - position.y
	scroll_drag_last_y = position.y
	_apply_scroll(scroll_drag_area, delta_y)

func _handle_scroll_wheel(position: Vector2, amount: float) -> void:
	if nav.current_screen == "Diagnostics" and _diagnostics_scroll_rect().has_point(position):
		_apply_scroll("diagnostics", amount)
	elif nav.current_screen == "Notification Control Center" and _control_scroll_rect().has_point(position):
		_apply_scroll("control", amount)

func _apply_scroll(area: String, amount: float) -> void:
	if area == "diagnostics":
		diagnostic_scroll_y = clampf(diagnostic_scroll_y + amount, 0.0, _diagnostics_max_scroll())
		_request_redraw()
	elif area == "control":
		control_center_scroll_y = clampf(control_center_scroll_y + amount, 0.0, _control_center_max_scroll())
		_request_redraw()

func _diagnostics_scroll_rect() -> Rect2:
	return Rect2(24, 138, 592, 318)

func _control_scroll_rect() -> Rect2:
	return Rect2(36, 286, 568, 166)

func _diagnostics_max_scroll() -> float:
	return maxf(0.0, _diagnostics_content_height() - _diagnostics_scroll_rect().size.y)

func _control_center_max_scroll() -> float:
	return maxf(0.0, _control_center_content_height() - _control_scroll_rect().size.y)

func _diagnostics_content_height() -> float:
	if active_tab == "Processes":
		return 362.0
	if active_tab == "Benchmarks":
		return 300.0
	if active_tab == "Overview":
		return 260.0
	return 220.0

func _control_center_content_height() -> float:
	return 182.0

func _open_menu() -> void:
	_navigate_to("Menu", "menu_open")

func _open_clock() -> void:
	_navigate_to("Clock", "clock_open")

func _open_control_center() -> void:
	_navigate_to("Notification Control Center", "control_open")

func _open_diagnostics() -> void:
	nav.previous_screen = nav.current_screen
	nav.current_screen = "Diagnostics"
	transition_active = false
	_request_redraw()

func _open_settings_placeholder() -> void:
	nav.placeholder_title = "Settings setup is planned"
	_navigate_to("Settings Setup", "diagnostics")

func _open_placeholder(title: String) -> void:
	nav.placeholder_title = title
	_navigate_to(title, "diagnostics")

func _go_home() -> void:
	if nav.current_screen == "Face Home":
		return
	var direction := "diagnostics"
	if nav.current_screen == "Menu":
		direction = "menu_close"
	elif nav.current_screen == "Clock":
		direction = "clock_close"
	elif nav.current_screen == "Notification Control Center":
		direction = "control_close"
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

func _draw() -> void:
	draw_rect(Rect2(Vector2.ZERO, Vector2(WIDTH, HEIGHT)), ThemeScript.BACKGROUND, true)
	if transition_active:
		_draw_transition()
	else:
		_draw_screen(nav.current_screen, Vector2.ZERO)

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
		_:
			overlay_offset = Vector2(0.0, 12.0 * (1.0 - t))
	_draw_face_home()
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
		"Diagnostics":
			_draw_diagnostics()
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
		_:
			_draw_placeholder(screen_name)
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)

func _font():
	return get_theme_default_font()

func _draw_text(text: String, position: Vector2, size: int = 18, color: Color = ThemeScript.TEXT) -> void:
	draw_string(_font(), position, text, HORIZONTAL_ALIGNMENT_LEFT, -1.0, size, color)

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
	var fill: Color = Color(0.12, 0.135, 0.16, 1.0) if active else Color(0.09, 0.102, 0.125, 1.0)
	_draw_card(rect, fill, 22.0, false)
	if active:
		_draw_rounded_rect(Rect2(rect.position + Vector2(0.0, 12.0), Vector2(4.0, rect.size.y - 24.0)), ThemeScript.BLUE, 2.0)

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
	face.draw_face(self, Vector2(WIDTH, HEIGHT), elapsed)
	_draw_text(Time.get_datetime_string_from_system(false, true).substr(11, 5), Vector2(538, 34), 17, Color(0.48, 0.62, 0.82, 0.82))
	if elapsed < nav.status_bubble_until:
		var bubble: Rect2 = Rect2(198, 350, 244, 58)
		_draw_card(bubble, Color(0.075, 0.085, 0.105, 0.96), 28.0, false)
		_draw_text("Status OK", bubble.position + Vector2(28, 37), 20, ThemeScript.TEXT)

func _draw_menu() -> void:
	draw_rect(Rect2(Vector2.ZERO, Vector2(WIDTH, HEIGHT)), ThemeScript.BACKGROUND, true)
	_draw_text("Menu", Vector2(32, 52), 27, ThemeScript.TEXT)
	for index in range(MENU_TILES.size()):
		var rect: Rect2 = _menu_tile_rect(index)
		var tile: Dictionary = MENU_TILES[index] as Dictionary
		_draw_tile(rect, tile["title"] == "Diagnostics")
		_draw_text(str(tile["icon"]), rect.position + Vector2(18, 45), 22, ThemeScript.BLUE if tile["title"] == "Diagnostics" else ThemeScript.TEXT)
		_draw_text(str(tile["title"]), rect.position + Vector2(58, 30), 17, ThemeScript.TEXT)
		_draw_text(str(tile["subtitle"]), rect.position + Vector2(58, 52), 11, ThemeScript.TEXT_MUTED)

func _menu_tile_rect(index: int) -> Rect2:
	var column: int = index % 2
	var row: int = int(index / 2)
	return Rect2(28.0 + float(column) * 300.0, 96.0 + float(row) * 86.0, 284.0, 72.0)

func _draw_clock() -> void:
	draw_rect(Rect2(Vector2.ZERO, Vector2(WIDTH, HEIGHT)), ThemeScript.BACKGROUND, true)
	var now: Dictionary = Time.get_datetime_dict_from_system()
	var time_text: String = "%02d:%02d" % [now.hour, now.minute]
	var date_text: String = "%04d-%02d-%02d" % [now.year, now.month, now.day]
	_draw_centered_text(time_text, WIDTH * 0.5, 226.0, 76, Color(0.93, 0.96, 1.0, 1.0))
	_draw_centered_text(date_text, WIDTH * 0.5, 274.0, 20, Color(0.58, 0.70, 0.88, 0.92))
	draw_circle(Vector2(320, 332), 8.0 + sin(elapsed * 0.9) * 1.2, Color(0.18, 0.58, 1.0, 0.92))
	# Future clock settings: show time on face, show date on face, auto show clock screen.
	# Future timing settings: show clock every X minutes, show clock duration seconds.

func _draw_control_center() -> void:
	_draw_soft_panel(Rect2(20, 20, 600, 440), 30.0)
	_draw_text("Control Center", Vector2(44, 64), 26, ThemeScript.TEXT)
	_draw_pill(Rect2(44, 82, 104, 26), Color(0.10, 0.16, 0.12, 1.0), false)
	_draw_text("System OK", Vector2(60, 100), 12, ThemeScript.OK)
	var controls: Array = [
		{"title": "Brightness", "value": "Soft"},
		{"title": "Sound", "value": "Desk"},
		{"title": "Quiet Mode", "value": "Off"},
		{"title": "Wi-Fi", "value": "Home"},
		{"title": "Remote", "value": "Ready"},
		{"title": "Diagnostics", "value": "Open"}
	]
	for index in range(controls.size()):
		var rect: Rect2 = Rect2(44.0 + float(index % 3) * 184.0, 124.0 + float(int(index / 3)) * 76.0, 164.0, 62.0)
		var item: Dictionary = controls[index] as Dictionary
		_draw_tile(rect, item["title"] == "Diagnostics")
		_draw_text(str(item["title"]), rect.position + Vector2(14, 27), 15, ThemeScript.TEXT)
		_draw_text(str(item["value"]), rect.position + Vector2(14, 48), 11, ThemeScript.TEXT_MUTED)
	_draw_text("Notifications", Vector2(46, 292), 20, ThemeScript.TEXT)
	var control_view: Rect2 = _control_scroll_rect()
	var y_offset: float = control_center_scroll_y
	_draw_notification(Rect2(44, 310 - y_offset, 552, 38), "Reminder", "Study plan", control_view)
	_draw_notification(Rect2(44, 354 - y_offset, 552, 38), "System", "UI running", control_view)
	_draw_notification(Rect2(44, 398 - y_offset, 552, 38), "Private", "Locked", control_view)
	_draw_notification(Rect2(44, 442 - y_offset, 552, 38), "System", "No saved report", control_view)
	_draw_scrollbar(control_view, control_center_scroll_y, _control_center_content_height())

func _draw_notification(rect: Rect2, label: String, message: String, view_rect: Rect2) -> void:
	if rect.position.y + rect.size.y < view_rect.position.y or rect.position.y > view_rect.position.y + view_rect.size.y:
		return
	_draw_card(rect, Color(0.09, 0.10, 0.12, 0.96), 20.0, false)
	_draw_pill(Rect2(rect.position.x + 12.0, rect.position.y + 8.0, 82.0, 22.0), Color(0.08, 0.12, 0.18, 0.92), label == "Private")
	_draw_text(label, rect.position + Vector2(26, 25), 11, ThemeScript.TEXT_MUTED)
	_draw_text(message, rect.position + Vector2(116, 25), 14, ThemeScript.TEXT)

func _draw_diagnostics() -> void:
	draw_rect(Rect2(Vector2.ZERO, Vector2(WIDTH, HEIGHT)), ThemeScript.BACKGROUND, true)
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
	elif active_tab == "Network":
		_draw_network_rows(offset_y, view_rect)
	else:
		_draw_info_row(52, 226 - offset_y, active_tab, "No saved report", "Waiting", view_rect)

func _draw_overview_cards(offset_y: float, view_rect: Rect2) -> void:
	var cards: Array = [
		{"title": "Overall", "body": panel_data.get("status", "No report"), "pill": "OK"},
		{"title": "Raspberry Pi", "body": "No saved report", "pill": "Saved"},
		{"title": "Speaker", "body": "Ready", "pill": "Ready"},
		{"title": "Camera", "body": "Ready", "pill": "Ready"},
		{"title": "Resources", "body": "Saved report", "pill": "Saved"}
	]
	for index in range(cards.size()):
		var rect: Rect2 = Rect2(48.0 + float(index % 2) * 274.0, 204.0 + float(int(index / 2)) * 70.0 - offset_y, 250.0, 54.0)
		var item: Dictionary = cards[index] as Dictionary
		if not _rect_visible(rect, view_rect):
			continue
		_draw_card_if_visible(rect, view_rect, Color(0.085, 0.095, 0.115, 0.96), 22.0)
		_draw_text_if_visible(str(item["title"]), rect.position + Vector2(14, 22), view_rect, 15, ThemeScript.TEXT)
		_draw_text_if_visible(str(item["body"]), rect.position + Vector2(14, 42), view_rect, 11, ThemeScript.TEXT_MUTED)
		_draw_pill(Rect2(rect.position.x + 174.0, rect.position.y + 14.0, 58.0, 24.0), Color(0.08, 0.13, 0.11, 0.92), item["pill"] == "OK")
		_draw_centered_text(str(item["pill"]), rect.position.x + 203.0, rect.position.y + 31.0, 11, ThemeScript.OK if item["pill"] == "OK" else ThemeScript.TEXT_MUTED)

func _draw_process_rows(offset_y: float, view_rect: Rect2) -> void:
	var y := 208.0 - offset_y
	_draw_text_if_visible("Service", Vector2(54, y), view_rect, 11, ThemeScript.TEXT_DIM)
	_draw_text_if_visible("Status", Vector2(328, y), view_rect, 11, ThemeScript.TEXT_DIM)
	_draw_text_if_visible("CPU", Vector2(430, y), view_rect, 11, ThemeScript.TEXT_DIM)
	_draw_text_if_visible("RAM", Vector2(506, y), view_rect, 11, ThemeScript.TEXT_DIM)
	y += 18.0
	for raw_row in diagnostics_data.sample_process_rows():
		var row: Dictionary = raw_row as Dictionary
		var row_rect: Rect2 = Rect2(48, y - 14.0, 544, 32)
		_draw_card_if_visible(row_rect, view_rect, Color(0.075, 0.085, 0.102, 0.94), 16.0)
		_draw_text_if_visible(str(row["name"]), Vector2(62, y + 7.0), view_rect, 12, ThemeScript.TEXT)
		_draw_text_if_visible(str(row["status"]), Vector2(328, y + 7.0), view_rect, 11, ThemeScript.TEXT_MUTED)
		_draw_text_if_visible(str(row["cpu"]) + "%", Vector2(430, y + 7.0), view_rect, 11, ThemeScript.TEXT_MUTED)
		_draw_text_if_visible(str(row["ram"]) + " MB", Vector2(506, y + 7.0), view_rect, 11, ThemeScript.TEXT_MUTED)
		y += 36.0

func _draw_benchmark_rows(offset_y: float, view_rect: Rect2) -> void:
	var top_card: Rect2 = Rect2(50, 206 - offset_y, 540, 54)
	_draw_card_if_visible(top_card, view_rect, Color(0.085, 0.095, 0.115, 0.96), 22.0)
	_draw_text_if_visible("Slowest check", Vector2(66, 228 - offset_y), view_rect, 16, ThemeScript.TEXT)
	_draw_text_if_visible("No saved report", Vector2(66, 248 - offset_y), view_rect, 12, ThemeScript.TEXT_MUTED)
	var checks: Array = ["Pi health", "Speaker", "Camera", "System", "Panel data"]
	for index in range(checks.size()):
		_draw_info_row(54, 292 + index * 28 - offset_y, str(checks[index]), "Waiting", "Pending", view_rect)

func _draw_network_rows(offset_y: float, view_rect: Rect2) -> void:
	_draw_info_row(54, 224 - offset_y, "Home Wi-Fi", "Planned", "Planned", view_rect)
	_draw_info_row(54, 260 - offset_y, "NeXa Remote", "Planned", "Planned", view_rect)
	_draw_info_row(54, 296 - offset_y, "Remote status", "No fake live data", "Waiting", view_rect)
	_draw_info_row(54, 332 - offset_y, "Two Wi-Fi", "Future", "Later", view_rect)

func _draw_info_row(x: float, y: float, title: String, subtitle: String, status: String, view_rect: Rect2) -> void:
	var row_rect: Rect2 = Rect2(x - 6.0, y - 22.0, 540.0, 32.0)
	if not _rect_visible(row_rect, view_rect):
		return
	_draw_card_if_visible(row_rect, view_rect, Color(0.075, 0.085, 0.102, 0.94), 16.0)
	_draw_text_if_visible(title, Vector2(x + 8.0, y), view_rect, 12, ThemeScript.TEXT)
	_draw_text_if_visible(subtitle, Vector2(x + 186.0, y), view_rect, 11, ThemeScript.TEXT_MUTED)
	_draw_pill(Rect2(x + 444.0, y - 17.0, 72.0, 22.0), Color(0.10, 0.105, 0.12, 0.92), false)
	_draw_centered_text(status, x + 480.0, y, 11, ThemeScript.TEXT_MUTED)

func _draw_placeholder(title: String) -> void:
	_draw_soft_panel(Rect2(76, 158, 488, 156), 32.0)
	_draw_centered_text(title, WIDTH * 0.5, 226.0, 26, ThemeScript.TEXT)
	_draw_centered_text("Press Escape to return home", WIDTH * 0.5, 258.0, 13, ThemeScript.TEXT_MUTED)
