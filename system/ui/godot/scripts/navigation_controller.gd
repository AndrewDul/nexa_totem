extends RefCounted
class_name NavigationController

const SCREEN_FACE_HOME := "Face Home"
const SCREEN_MENU := "Menu"
const SCREEN_CLOCK := "Clock"
const SCREEN_NOTIFICATION_CONTROL_CENTER := "Notification Control Center"
const SCREEN_DIAGNOSTICS := "Diagnostics"
const SCREEN_SETTINGS := "Settings Setup"

var current_screen := SCREEN_FACE_HOME
var previous_screen := SCREEN_FACE_HOME
var status_bubble_until := 0.0
var placeholder_title := ""

func go_home() -> void:
	_go_to(SCREEN_FACE_HOME)

func open_menu() -> void:
	_go_to(SCREEN_MENU)

func open_clock() -> void:
	_go_to(SCREEN_CLOCK)

func open_control_center() -> void:
	_go_to(SCREEN_NOTIFICATION_CONTROL_CENTER)

func open_diagnostics() -> void:
	_go_to(SCREEN_DIAGNOSTICS)

func open_settings_placeholder() -> void:
	placeholder_title = "Settings setup is planned"
	_go_to(SCREEN_SETTINGS)

func show_status_bubble(now: float) -> void:
	status_bubble_until = now + 2.0

func open_placeholder(title: String) -> void:
	placeholder_title = title
	_go_to(title)

func _go_to(screen_name: String) -> void:
	previous_screen = current_screen
	current_screen = screen_name
