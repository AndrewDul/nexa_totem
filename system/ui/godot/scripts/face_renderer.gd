extends RefCounted
class_name FaceRenderer

const STATE_IDLE := "idle"
const STATE_CALM := "calm"
const STATE_CURIOUS := "curious"
const STATE_ALERT := "alert"
const STATE_THINKING := "thinking"
const BLINK_PERIOD := 10.0
const BLINK_DURATION := 0.16

var expression_state := STATE_IDLE

func draw_face(canvas: CanvasItem, viewport_size: Vector2, elapsed: float) -> void:
	var center := viewport_size * 0.5
	var breath := sin(elapsed * 0.72) * 1.0
	var eye_y := center.y - 58.0 + breath * 3.0
	var eye_offset := sin(elapsed * 0.32) * 1.4
	var eye_scale := 1.0 + breath * 0.018
	var blink_amount: float = _blink_amount(elapsed)
	var eye_color := Color(0.18, 0.58, 1.0, 1.0)
	var mouth_color := Color(0.18, 0.58, 1.0, 0.95)
	var eye_height: float = 104.0 * eye_scale * lerpf(1.0, 0.12, blink_amount)
	var eye_width: float = 36.0 * eye_scale * lerpf(1.0, 1.08, blink_amount)
	_draw_bean_eye(canvas, Vector2(center.x - 86.0 + eye_offset, eye_y), eye_width, eye_height, eye_color)
	_draw_bean_eye(canvas, Vector2(center.x + 86.0 + eye_offset, eye_y), eye_width, eye_height, eye_color)
	var mouth_width := 132.0 + breath * 5.0
	var mouth_y := center.y + 104.0 + breath * 3.0
	var mouth_start := Vector2(center.x - mouth_width * 0.5, mouth_y)
	var mouth_end := Vector2(center.x + mouth_width * 0.5, mouth_y)
	canvas.draw_line(mouth_start, mouth_end, mouth_color, 12.0, true)
	canvas.draw_circle(mouth_start, 6.0, mouth_color)
	canvas.draw_circle(mouth_end, 6.0, mouth_color)

func _blink_amount(elapsed: float) -> float:
	var phase: float = fmod(elapsed + 2.0, BLINK_PERIOD)
	if phase > BLINK_DURATION:
		return 0.0
	var normalized: float = phase / BLINK_DURATION
	return sin(normalized * PI)

func _draw_bean_eye(canvas: CanvasItem, center: Vector2, width: float, height: float, color: Color) -> void:
	_draw_vertical_capsule(canvas, center, width, height, color)
	_draw_vertical_capsule(canvas, center + Vector2(-width * 0.16, -height * 0.15), width * 0.18, height * 0.50, Color(0.62, 0.82, 1.0, 0.16))

func _draw_vertical_capsule(canvas: CanvasItem, center: Vector2, width: float, height: float, color: Color) -> void:
	if height <= width:
		var line_radius: float = height * 0.5
		var left := center + Vector2(-width * 0.5 + line_radius, 0.0)
		var right := center + Vector2(width * 0.5 - line_radius, 0.0)
		canvas.draw_circle(left, line_radius, color)
		canvas.draw_circle(right, line_radius, color)
		canvas.draw_rect(Rect2(left.x, center.y - line_radius, right.x - left.x, height), color, true)
		return
	var radius := width * 0.5
	var top := center + Vector2(0.0, -height * 0.5 + radius)
	var bottom := center + Vector2(0.0, height * 0.5 - radius)
	canvas.draw_circle(top, radius, color)
	canvas.draw_circle(bottom, radius, color)
	canvas.draw_rect(Rect2(center.x - radius, top.y, width, bottom.y - top.y), color, true)
