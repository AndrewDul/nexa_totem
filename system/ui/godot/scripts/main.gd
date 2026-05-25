extends Control

const NavigationControllerScript := preload("res://scripts/navigation_controller.gd")
const GestureDetectorScript := preload("res://scripts/gesture_detector.gd")
const FaceRendererScript := preload("res://scripts/face_renderer.gd")
const DiagnosticsDataScript := preload("res://scripts/diagnostics_data.gd")

const WIDTH := 640.0
const HEIGHT := 480.0
const MENU_TILES := [
	{"title": "Time", "subtitle": "Clock view"},
	{"title": "Study", "subtitle": "Focus timer"},
	{"title": "Reminders", "subtitle": "Local alerts"},
	{"title": "Calendar", "subtitle": "Planned"},
	{"title": "Tasks", "subtitle": "Today list"},
	{"title": "Games", "subtitle": "Later"},
	{"title": "Diagnostics", "subtitle": "System state"},
	{"title": "Settings", "subtitle": "Setup"}
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

func _ready() -> void:
	custom_minimum_size = Vector2(WIDTH, HEIGHT)
	panel_data = diagnostics_data.load_panel_data()
	set_process(true)

func _process(delta: float) -> void:
	elapsed += delta
	queue_redraw()

func _gui_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		if event.pressed:
			gesture.begin(event.position, elapsed)
		else:
			_handle_gesture(gesture.finish(event.position, elapsed), event.position)
	if event is InputEventMouseMotion and gesture.is_pressed:
		gesture.update(event.position)

func _unhandled_key_input(event: InputEvent) -> void:
	if not event.pressed:
		return
	if event.keycode == KEY_LEFT:
		nav.open_menu()
	elif event.keycode == KEY_RIGHT:
		nav.open_clock()
	elif event.keycode == KEY_DOWN:
		nav.open_control_center()
	elif event.keycode == KEY_ESCAPE:
		nav.go_home()
	queue_redraw()

func _handle_gesture(action: String, position: Vector2) -> void:
	if action == "swipe_left":
		nav.open_menu()
	elif action == "swipe_right":
		nav.open_clock()
	elif action == "swipe_down":
		nav.open_control_center()
	elif action == "tap":
		_handle_tap(position)
	elif action == "long_press":
		nav.open_settings_placeholder()
	queue_redraw()

func _handle_tap(position: Vector2) -> void:
	if nav.current_screen == "Face Home":
		nav.show_status_bubble(elapsed)
		return
	if nav.current_screen == "Menu":
		_handle_menu_tap(position)
		return
	if nav.current_screen == "Notification Control Center":
		if position.y > 150.0 and position.y < 270.0:
			nav.open_diagnostics()
		return
	if nav.current_screen == "Diagnostics":
		_handle_diagnostics_tap(position)

func _handle_menu_tap(position: Vector2) -> void:
	var index := 0
	for row in range(2):
		for column in range(4):
			var rect := Rect2(24.0 + column * 148.0, 122.0 + row * 138.0, 128.0, 108.0)
			if rect.has_point(position):
				var tile = MENU_TILES[index]
				if tile["title"] == "Diagnostics":
					nav.open_diagnostics()
				else:
					nav.open_placeholder(tile["title"] + " placeholder")
			index += 1

func _handle_diagnostics_tap(position: Vector2) -> void:
	for index in range(DIAGNOSTIC_TABS.size()):
		var rect := Rect2(12.0 + float(index % 5) * 122.0, 62.0 + float(index / 5) * 44.0, 112.0, 34.0)
		if rect.has_point(position):
			active_tab = DIAGNOSTIC_TABS[index]
			return

func _draw() -> void:
	draw_rect(Rect2(Vector2.ZERO, Vector2(WIDTH, HEIGHT)), Color.BLACK, true)
	match nav.current_screen:
		"Face Home":
			_draw_face_home()
		"Menu":
			_draw_menu()
		"Clock":
			_draw_clock()
		"Notification Control Center":
			_draw_control_center()
		"Diagnostics":
			_draw_diagnostics()
		_:
			_draw_placeholder(nav.current_screen)

func _font():
	return get_theme_default_font()

func _font_size_large() -> int:
	return 48

func _draw_text(text: String, position: Vector2, size: int = 18, color: Color = Color.WHITE) -> void:
	draw_string(_font(), position, text, HORIZONTAL_ALIGNMENT_LEFT, -1.0, size, color)

func _draw_panel(rect: Rect2, color: Color = Color(0.07, 0.075, 0.085, 0.96)) -> void:
	draw_rect(rect, color, true)

func _draw_face_home() -> void:
	face.draw_face(self, Vector2(WIDTH, HEIGHT), elapsed)
	_draw_text(Time.get_datetime_string_from_system(false, true).substr(11, 5), Vector2(536, 36), 18, Color(0.55, 0.70, 0.95))
	_draw_text("Face Home", Vector2(30, 42), 16, Color(0.42, 0.48, 0.56))
	if elapsed < nav.status_bubble_until:
		_draw_panel(Rect2(188, 348, 264, 58), Color(0.08, 0.10, 0.13, 0.96))
		_draw_text("Prototype status: OK", Vector2(216, 384), 20, Color(0.82, 0.90, 1.0))

func _draw_menu() -> void:
	_draw_text("Menu", Vector2(28, 58), 34, Color(0.92, 0.94, 0.97))
	_draw_text("Swipe back or press Escape for Home", Vector2(30, 88), 15, Color(0.54, 0.58, 0.66))
	var index := 0
	for row in range(2):
		for column in range(4):
			var rect := Rect2(24.0 + column * 148.0, 122.0 + row * 138.0, 128.0, 108.0)
			_draw_panel(rect, Color(0.10, 0.11, 0.13, 0.98))
			var tile = MENU_TILES[index]
			_draw_text(tile["title"], rect.position + Vector2(14, 42), 20, Color(0.92, 0.94, 0.97))
			_draw_text(tile["subtitle"], rect.position + Vector2(14, 72), 13, Color(0.58, 0.63, 0.70))
			index += 1

func _draw_clock() -> void:
	var now := Time.get_datetime_dict_from_system()
	var time_text := "%02d:%02d" % [now.hour, now.minute]
	var date_text := "%04d-%02d-%02d" % [now.year, now.month, now.day]
	_draw_text(time_text, Vector2(204, 210), 74, Color(0.92, 0.95, 1.0))
	_draw_text(date_text, Vector2(254, 260), 20, Color(0.55, 0.70, 0.95))
	draw_circle(Vector2(320, 335), 8.0 + sin(elapsed) * 2.0, Color(0.18, 0.58, 1.0))
	# Future clock settings: show time on face, show date on face, auto show clock screen.
	# Future timing settings: show clock every X minutes, show clock duration seconds.

func _draw_control_center() -> void:
	_draw_panel(Rect2(18, 20, 604, 440), Color(0.07, 0.075, 0.085, 0.98))
	_draw_text("NeXa Control Center", Vector2(42, 68), 28, Color(0.94, 0.96, 0.99))
	_draw_text("Current status: OK / Prototype", Vector2(44, 96), 16, Color(0.42, 0.86, 0.58))
	var controls := ["Brightness", "Sound", "Quiet Mode", "Wi-Fi", "Remote", "Diagnostics"]
	for index in range(controls.size()):
		var rect := Rect2(42.0 + float(index % 3) * 186.0, 134.0 + float(index / 3) * 74.0, 164.0, 58.0)
		_draw_panel(rect, Color(0.11, 0.12, 0.14, 0.98))
		_draw_text(controls[index], rect.position + Vector2(14, 36), 18, Color(0.90, 0.93, 0.97))
	_draw_text("Notifications", Vector2(44, 306), 22, Color(0.92, 0.94, 0.97))
	_draw_text("Reminder: Review study plan", Vector2(58, 342), 16, Color(0.70, 0.76, 0.84))
	_draw_text("System: Prototype UI running", Vector2(58, 370), 16, Color(0.70, 0.76, 0.84))
	_draw_text("Private: Placeholder only", Vector2(58, 398), 16, Color(0.70, 0.76, 0.84))

func _draw_diagnostics() -> void:
	_draw_text("Diagnostics", Vector2(24, 42), 28, Color(0.94, 0.96, 0.99))
	for index in range(DIAGNOSTIC_TABS.size()):
		var rect := Rect2(12.0 + float(index % 5) * 122.0, 62.0 + float(index / 5) * 44.0, 112.0, 34.0)
		var active := DIAGNOSTIC_TABS[index] == active_tab
		_draw_panel(rect, Color(0.16, 0.26, 0.42, 0.98) if active else Color(0.10, 0.11, 0.13, 0.98))
		_draw_text(DIAGNOSTIC_TABS[index], rect.position + Vector2(10, 23), 13, Color(0.90, 0.94, 0.98))
	_draw_panel(Rect2(26, 154, 588, 288), Color(0.06, 0.065, 0.075, 0.96))
	_draw_diagnostics_tab_content()

func _draw_diagnostics_tab_content() -> void:
	_draw_text(active_tab, Vector2(48, 194), 24, Color(0.92, 0.94, 0.97))
	if active_tab == "Overview":
		_draw_text("Overall status: " + panel_data.get("status", "not_checked"), Vector2(52, 232), 17, Color(0.72, 0.80, 0.90))
		_draw_text("Raspberry Pi status: Latest saved report or not checked", Vector2(52, 262), 15, Color(0.62, 0.68, 0.76))
		_draw_text("Speaker status: Latest saved report or not checked", Vector2(52, 290), 15, Color(0.62, 0.68, 0.76))
		_draw_text("Camera status: Latest saved report or not checked", Vector2(52, 318), 15, Color(0.62, 0.68, 0.76))
		_draw_text("Resource status: Latest saved resource report", Vector2(52, 346), 15, Color(0.62, 0.68, 0.76))
	elif active_tab == "Processes":
		var y := 232
		for row in diagnostics_data.sample_process_rows():
			_draw_text(row["name"] + "  " + row["status"] + "  CPU " + row["cpu"] + "%  RAM " + row["ram"] + " MB", Vector2(52, y), 14, Color(0.66, 0.72, 0.80))
			y += 26
	elif active_tab == "Benchmarks":
		_draw_text("Slowest check: Latest saved benchmark or not checked", Vector2(52, 236), 15, Color(0.66, 0.72, 0.80))
		_draw_text("pi health, speaker status, camera status, system status, panel data build", Vector2(52, 266), 14, Color(0.58, 0.64, 0.72))
	elif active_tab == "Camera":
		_draw_text("Camera command and detection will come from saved reports.", Vector2(52, 236), 15, Color(0.66, 0.72, 0.80))
		_draw_text("Last capture validation: placeholder", Vector2(52, 266), 15, Color(0.58, 0.64, 0.72))
	elif active_tab == "Audio":
		_draw_text("Speaker status, playback outputs, USB detection, default output placeholder.", Vector2(52, 236), 15, Color(0.66, 0.72, 0.80))
	elif active_tab == "Reports":
		_draw_text("Latest reports list and history reports placeholder.", Vector2(52, 236), 15, Color(0.66, 0.72, 0.80))
	elif active_tab == "Logs":
		_draw_text("Latest logs placeholder. No large log viewer yet.", Vector2(52, 236), 15, Color(0.66, 0.72, 0.80))
	elif active_tab == "Network":
		_draw_text("Home Wi-Fi, NeXa Remote network, and remote status placeholders.", Vector2(52, 236), 15, Color(0.66, 0.72, 0.80))
		_draw_text("Future two-Wi-Fi-interface architecture note.", Vector2(52, 266), 15, Color(0.58, 0.64, 0.72))
	else:
		_draw_text("Latest saved report or prototype placeholder.", Vector2(52, 236), 15, Color(0.66, 0.72, 0.80))

func _draw_placeholder(title: String) -> void:
	_draw_text(title, Vector2(58, 205), 30, Color(0.92, 0.94, 0.97))
	_draw_text("Prototype placeholder. Press Escape for Face Home.", Vector2(60, 245), 17, Color(0.58, 0.64, 0.72))
