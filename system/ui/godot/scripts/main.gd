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

func _ready() -> void:
	custom_minimum_size = Vector2(WIDTH, HEIGHT)
	panel_data = diagnostics_data.load_panel_data()
	add_child(api)
	api.data_received.connect(_on_api_data_received)
	api.api_offline.connect(_on_api_offline)
	api.frame_received.connect(_on_camera_frame_received)
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
			elif nav.current_screen == "Notification Control Center":
				control_center_refresh_pending = true
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
	_update_api_polling(delta)

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
			if _begin_slider_drag(event.position):
				return
			if _begin_scroll_drag(event.position):
				return
			else:
				gesture.begin(event.position, elapsed)
		else:
			if slider_drag_active:
				_finish_slider_drag()
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
		_handle_control_center_tap(position)
		return
	if nav.current_screen == "Diagnostics":
		if Rect2(536, 22, 78, 34).has_point(position):
			_go_home()
			return
		_handle_diagnostics_action_tap(position)
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
			if active_tab == "Camera" and str(DIAGNOSTIC_TABS[index]) != "Camera":
				_stop_camera_preview()
			active_tab = str(DIAGNOSTIC_TABS[index])
			diagnostic_scroll_y = 0.0
			active_tab_data = {}
			_request_active_diagnostics_tab()
			_request_redraw()
			return

func _handle_control_center_tap(position: Vector2) -> void:
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
		_request_redraw()
		return

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
	return 260.0

func _control_center_content_height() -> float:
	return 182.0

func _open_menu() -> void:
	_navigate_to("Menu", "menu_open")

func _open_clock() -> void:
	_navigate_to("Clock", "clock_open")

func _open_control_center() -> void:
	_navigate_to("Notification Control Center", "control_open")
	control_center_refresh_pending = true
	# Control Center opens from cached data first. API refresh happens after transition to avoid UI lag.

func _open_diagnostics() -> void:
	nav.previous_screen = nav.current_screen
	nav.current_screen = "Diagnostics"
	transition_active = false
	active_tab = "Overview"
	active_tab_data = {}
	api.request_get("/api/overview")
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
	if nav.current_screen == "Diagnostics" and active_tab == "Camera":
		_stop_camera_preview()
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

func _update_api_polling(delta: float) -> void:
	if api.in_flight:
		return
	api_poll_accumulator += delta
	if transition_active:
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
	api.request_get(endpoint)

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
	elif endpoint == "/api/overview":
		overview_live_data = payload
		active_tab_data = payload
	elif endpoint == "/api/network":
		network_detail_data = payload
		if nav.current_screen == "Diagnostics" and active_tab == "Network":
			active_tab_data = payload
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

func _on_api_offline(endpoint: String) -> void:
	api_online = false
	api_status_text = "API offline"
	if endpoint == "/api/camera/preview/frame" and camera_preview_on:
		camera_preview_status = "No frame yet"
	_request_redraw()

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
	var fill: Color = Color(0.11, 0.32, 0.66, 1.0) if active else Color(0.09, 0.102, 0.125, 1.0)
	_draw_card(rect, fill, 22.0, false)
	if active:
		_draw_rounded_rect(Rect2(rect.position + Vector2(0.0, 12.0), Vector2(4.0, rect.size.y - 24.0)), ThemeScript.BLUE, 2.0)

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
	_draw_text("Notifications", Vector2(46, 292), 20, ThemeScript.TEXT)
	var control_view: Rect2 = _control_scroll_rect()
	var y_offset: float = control_center_scroll_y
	_draw_notification(Rect2(44, 310 - y_offset, 552, 38), "Reminder", "Study plan", control_view)
	_draw_notification(Rect2(44, 354 - y_offset, 552, 38), "System", "UI running", control_view)
	_draw_notification(Rect2(44, 398 - y_offset, 552, 38), "Private", "Locked", control_view)
	_draw_notification(Rect2(44, 442 - y_offset, 552, 38), "System", "No saved report", control_view)
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
			_draw_text("Notifications", Vector2(46, 300), 18, ThemeScript.TEXT)
			_draw_notification_safe(Rect2(44, 318, 552, 40), "Reminder", "Study plan")
			_draw_notification_safe(Rect2(44, 366, 552, 40), "System", "UI running")

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

func _draw_notification_safe(rect: Rect2, label: String, message: String) -> void:
	_draw_rounded_rect(rect, Color(0.078, 0.087, 0.104, 1.0), 16.0)
	_draw_text(label, rect.position + Vector2(14, 25), 11, ThemeScript.TEXT_MUTED)
	_draw_text(message, rect.position + Vector2(112, 25), 13, ThemeScript.TEXT)

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

func _draw_placeholder(title: String) -> void:
	_draw_soft_panel(Rect2(76, 158, 488, 156), 32.0)
	_draw_centered_text(title, WIDTH * 0.5, 226.0, 26, ThemeScript.TEXT)
	_draw_centered_text("Press Escape to return home", WIDTH * 0.5, 258.0, 13, ThemeScript.TEXT_MUTED)
