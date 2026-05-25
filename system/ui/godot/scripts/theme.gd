extends RefCounted
class_name NexaTheme

const BACKGROUND := Color(0.0, 0.0, 0.0, 1.0)
const PANEL := Color(0.06, 0.065, 0.075, 0.96)
const TILE := Color(0.10, 0.11, 0.13, 0.96)
const TILE_SOFT := Color(0.16, 0.17, 0.19, 0.90)
const TEXT := Color(0.92, 0.94, 0.97, 1.0)
const TEXT_MUTED := Color(0.58, 0.62, 0.68, 1.0)
const BLUE := Color(0.18, 0.58, 1.0, 1.0)
const BLUE_SOFT := Color(0.12, 0.36, 0.70, 0.8)
const WARNING := Color(1.0, 0.72, 0.22, 1.0)
const OK := Color(0.25, 0.86, 0.54, 1.0)

static func rounded_rect(canvas: CanvasItem, rect: Rect2, color: Color, radius: float = 22.0) -> void:
	canvas.draw_rect(rect, color, true)
