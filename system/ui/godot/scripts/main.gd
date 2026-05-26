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
const SETTINGS_TILES := [
	{"icon": "◐", "title": "Appearance", "subtitle": "Theme"},
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
const QUICK_SHELF_OPTIONS := ["Clock", "Calendar", "Reminders", "Tasks", "Study", "Pomodoro", "Games", "Diagnostics", "Network", "Camera", "Air Quality", "Temperature", "Brightness", "Sound", "Quiet Mode", "Remote", "Settings", "LED", "Logs", "Reports", "Exit NeXa"]

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
	if event is InputEventScreenTouch:
		if event.pressed:
			if _begin_slider_drag(event.position):
				return
			if _begin_scroll_drag(event.position):
				return
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
	if event is InputEventScreenDrag:
		if gesture.is_pressed:
			gesture.update(event.position)
		if scroll_drag_active:
			_update_scroll_drag(event.position)
		if slider_drag_active:
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
	elif nav.current_screen == "Menu" and action == "swipe_right":
		_go_home()
	elif nav.current_screen == "Clock" and action == "swipe_left":
		_go_home()
	elif nav.current_screen == "Notification Control Center" and action == "swipe_up":
		_go_home()
	elif nav.current_screen == "Quick Shelf" and action == "swipe_down":
		_go_home()
	_request_redraw()

func _handle_tap(position: Vector2) -> void:
	if transition_active:
		return
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
		return
	if nav.current_screen == "Settings":
		_handle_settings_tap(position)
		return
	if nav.current_screen == "Quick Shelf":
		_handle_quick_shelf_panel_tap(position)

func _handle_menu_tap(position: Vector2) -> void:
	for index in range(MENU_TILES.size()):
		var rect: Rect2 = _menu_tile_rect(index)
		if rect.has_point(position):
			var tile: Dictionary = MENU_TILES[index] as Dictionary
			if tile["title"] == "Diagnostics":
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
		_request_redraw()
		return
	var current = _settings_value(section, key, row.get("default"))
	if row.has("set_value"):
		_settings_update(section, key, row.get("set_value"))
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
	else:
		_settings_update(section, key, value)

func _apply_appearance_preset(preset_name: String) -> void:
	var preset: Dictionary = _appearance_preset_values(preset_name)
	var updates: Array = [{"section": "appearance", "key": "preset", "value": preset_name}]
	for key in ["eye_color", "mouth_color", "tile_accent_color", "background_color", "led_color"]:
		updates.append({"section": "appearance", "key": key, "value": preset.get(key, "Blue")})
	_settings_update_many(updates)

func _appearance_preset_values(preset_name: String) -> Dictionary:
	var presets: Dictionary = {
		"NeXa Blue": {"eye_color": "Blue", "mouth_color": "Blue", "tile_accent_color": "Blue", "background_color": "Black", "led_color": "Blue"},
		"Apple Dark": {"eye_color": "White", "mouth_color": "White", "tile_accent_color": "Graphite", "background_color": "Black", "led_color": "White"},
		"Warm Desk": {"eye_color": "Warm White", "mouth_color": "Warm White", "tile_accent_color": "Gold", "background_color": "Brown", "led_color": "Warm White"},
		"Focus Green": {"eye_color": "Green", "mouth_color": "Green", "tile_accent_color": "Green", "background_color": "Graphite", "led_color": "Green"},
		"Night Red": {"eye_color": "Red", "mouth_color": "Red", "tile_accent_color": "Red", "background_color": "Black", "led_color": "Red"},
		"Soft Pink": {"eye_color": "Pink", "mouth_color": "Pink", "tile_accent_color": "Pink", "background_color": "Graphite", "led_color": "Pink"},
		"Minimal White": {"eye_color": "White", "mouth_color": "White", "tile_accent_color": "White", "background_color": "Black", "led_color": "White"}
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
			{"title": "LED color", "section": "appearance", "key": "led_color", "kind": "choice", "options": COLOR_OPTIONS, "default": "Blue"}
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
	elif nav.current_screen == "Settings" and _settings_scroll_rect().has_point(position):
		_apply_scroll("settings", amount)
	elif nav.current_screen == "Quick Shelf" and _quick_shelf_scroll_rect().has_point(position):
		_apply_scroll("quick_shelf", amount)

func _apply_scroll(area: String, amount: float) -> void:
	if area == "diagnostics":
		diagnostic_scroll_y = clampf(diagnostic_scroll_y + amount, 0.0, _diagnostics_max_scroll())
		_request_redraw()
	elif area == "control":
		control_center_scroll_y = clampf(control_center_scroll_y + amount, 0.0, _control_center_max_scroll())
		_request_redraw()
	elif area == "settings":
		settings_scroll_y = clampf(settings_scroll_y + amount, 0.0, _settings_max_scroll())
		_request_redraw()
	elif area == "quick_shelf":
		quick_shelf_scroll_y = clampf(quick_shelf_scroll_y + amount, 0.0, _quick_shelf_max_scroll())
		_request_redraw()

func _diagnostics_scroll_rect() -> Rect2:
	return Rect2(24, 138, 592, 318)

func _control_scroll_rect() -> Rect2:
	return Rect2(36, 286, 568, 166)

func _settings_scroll_rect() -> Rect2:
	return Rect2(24, 84, 592, 372)

func _settings_scrollbar_hit_rect() -> Rect2:
	return Rect2(596, 84, 24, 372)

func _quick_shelf_scroll_rect() -> Rect2:
	return Rect2(24, 120, 592, 324)

func _quick_shelf_scrollbar_hit_rect() -> Rect2:
	return Rect2(596, 120, 24, 324)

func _diagnostics_max_scroll() -> float:
	return maxf(0.0, _diagnostics_content_height() - _diagnostics_scroll_rect().size.y)

func _control_center_max_scroll() -> float:
	return maxf(0.0, _control_center_content_height() - _control_scroll_rect().size.y)

func _settings_max_scroll() -> float:
	return maxf(0.0, _settings_content_height() - _settings_scroll_rect().size.y)

func _quick_shelf_max_scroll() -> float:
	return maxf(0.0, _quick_shelf_content_height() - _quick_shelf_scroll_rect().size.y)

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

func _settings_content_height() -> float:
	if settings_current_page == "home":
		return 672.0
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

func _open_menu() -> void:
	_navigate_to("Menu", "menu_open")

func _open_clock() -> void:
	_navigate_to("Clock", "clock_open")

func _open_control_center() -> void:
	_navigate_to("Notification Control Center", "control_open")
	control_center_refresh_pending = true
	# Control Center opens from cached data first. API refresh happens after transition to avoid UI lag.

func _open_quick_shelf() -> void:
	_navigate_to("Quick Shelf", "quick_open")
	quick_shelf_scroll_y = 0.0
	if settings_data.is_empty():
		api.request_get("/api/settings")

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
	elif endpoint == "/api/settings" or endpoint == "/api/settings/update" or endpoint == "/api/settings/reset-section" or endpoint == "/api/privacy/pin/set":
		var settings_raw = payload.get("settings", {})
		if settings_raw is Dictionary:
			settings_data = settings_raw
			settings_status_text = "Saved"
		if endpoint == "/api/privacy/pin/set":
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
	draw_rect(Rect2(Vector2.ZERO, Vector2(WIDTH, HEIGHT)), _theme_background_color(), true)
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
		"quick_open":
			overlay_offset = Vector2(0.0, HEIGHT * (1.0 - t))
		"quick_close":
			overlay_offset = Vector2(0.0, HEIGHT * t)
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
		"Quick Shelf":
			_draw_face_home()
			_draw_quick_shelf()
		"Diagnostics":
			_draw_diagnostics()
		"Settings":
			_draw_settings()
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
	face.draw_face(self, Vector2(WIDTH, HEIGHT), elapsed, _settings_color(str(_settings_value("appearance", "eye_color", "Blue")), Color(0.18, 0.58, 1.0, 1.0)), _settings_color(str(_settings_value("appearance", "mouth_color", "Blue")), Color(0.18, 0.58, 1.0, 0.95)))
	_draw_text(Time.get_datetime_string_from_system(false, true).substr(11, 5), Vector2(538, 34), 17, Color(0.48, 0.62, 0.82, 0.82))
	if elapsed < nav.status_bubble_until:
		var bubble: Rect2 = Rect2(198, 350, 244, 58)
		_draw_card(bubble, Color(0.075, 0.085, 0.105, 0.96), 28.0, false)
		_draw_text("Status OK", bubble.position + Vector2(28, 37), 20, ThemeScript.TEXT)

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
		_draw_tile(rect, tile["title"] == "Diagnostics")
		_draw_text(str(tile["icon"]), rect.position + Vector2(18, 45), 22, ThemeScript.BLUE if tile["title"] == "Diagnostics" else ThemeScript.TEXT)
		_draw_text(str(tile["title"]), rect.position + Vector2(58, 30), 17, ThemeScript.TEXT)
		_draw_text(str(tile["subtitle"]), rect.position + Vector2(58, 52), 11, ThemeScript.TEXT_MUTED)

func _menu_tile_rect(index: int) -> Rect2:
	var column: int = index % 2
	var row: int = int(index / 2)
	return Rect2(28.0 + float(column) * 300.0, 96.0 + float(row) * 86.0, 284.0, 72.0)

func _draw_clock() -> void:
	draw_rect(Rect2(Vector2.ZERO, Vector2(WIDTH, HEIGHT)), _theme_background_color(), true)
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
	return "◆"

func _quick_shelf_subtitle(name: String) -> String:
	if name == "Brightness":
		return str(brightness_percent) + "%"
	if name == "Sound":
		return str(sound_percent) + "%"
	if name == "Quiet Mode":
		return "On" if quiet_mode_local else "Off"
	if name in ["Diagnostics", "Settings", "Clock", "Network", "Camera", "Logs", "Reports"]:
		return "Open"
	return "Planned"

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
