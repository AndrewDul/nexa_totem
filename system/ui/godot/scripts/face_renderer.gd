extends RefCounted
class_name FaceRenderer

const STATE_IDLE := "idle"
const STATE_CALM := "calm"
const STATE_CURIOUS := "curious"
const STATE_ALERT := "alert"
const STATE_THINKING := "thinking"

var expression_state := STATE_IDLE

func draw_face(canvas: CanvasItem, viewport_size: Vector2, elapsed: float) -> void:
	var center := viewport_size * 0.5
	var breath := sin(elapsed * 1.4) * 6.0
	var eye_y := center.y - 58.0 + breath * 0.18
	var eye_offset := sin(elapsed * 0.7) * 5.0
	var eye_color := Color(0.18, 0.58, 1.0, 1.0)
	var mouth_color := Color(0.18, 0.58, 1.0, 0.95)
	_draw_bean_eye(canvas, Vector2(center.x - 92.0 + eye_offset, eye_y), 78.0 + breath, 42.0, eye_color)
	_draw_bean_eye(canvas, Vector2(center.x + 92.0 + eye_offset, eye_y), 78.0 + breath, 42.0, eye_color)
	var mouth_start := Vector2(center.x - 76.0, center.y + 90.0 + breath * 0.12)
	var mouth_end := Vector2(center.x + 76.0, center.y + 90.0 + breath * 0.12)
	canvas.draw_line(mouth_start, mouth_end, mouth_color, 12.0, true)
	canvas.draw_circle(mouth_start, 6.0, mouth_color)
	canvas.draw_circle(mouth_end, 6.0, mouth_color)

func _draw_bean_eye(canvas: CanvasItem, center: Vector2, width: float, height: float, color: Color) -> void:
	var left := center + Vector2(-width * 0.28, 0.0)
	var right := center + Vector2(width * 0.28, 0.0)
	canvas.draw_circle(left, height * 0.52, color)
	canvas.draw_circle(right, height * 0.52, color)
	canvas.draw_rect(Rect2(left.x, center.y - height * 0.52, right.x - left.x, height * 1.04), color, true)
