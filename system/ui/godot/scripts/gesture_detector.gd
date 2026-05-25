extends RefCounted
class_name GestureDetector

const MIN_SWIPE_DISTANCE := 70.0
const LONG_PRESS_SECONDS := 0.7

var drag_start := Vector2.ZERO
var drag_current := Vector2.ZERO
var press_started_at := 0.0
var is_pressed := false

func begin(position: Vector2, now: float) -> void:
	drag_start = position
	drag_current = position
	press_started_at = now
	is_pressed = true

func update(position: Vector2) -> void:
	drag_current = position

func finish(position: Vector2, now: float) -> String:
	if not is_pressed:
		return ""
	is_pressed = false
	drag_current = position
	var delta := drag_current - drag_start
	if delta.length() < 18.0 and now - press_started_at >= LONG_PRESS_SECONDS:
		return "long_press"
	if delta.length() < 18.0:
		return "tap"
	if abs(delta.x) > abs(delta.y) and abs(delta.x) >= MIN_SWIPE_DISTANCE:
		return "swipe_left" if delta.x < 0.0 else "swipe_right"
	if delta.y >= MIN_SWIPE_DISTANCE:
		return "swipe_down"
	return ""
