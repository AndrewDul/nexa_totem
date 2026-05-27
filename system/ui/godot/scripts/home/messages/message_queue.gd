extends RefCounted
class_name NexaMessageQueue

const PRIORITY_ORDER := {
	"critical": 5,
	"warning": 4,
	"important": 3,
	"reminder": 2,
	"normal": 1,
	"silent": 0
}

var active_message: Dictionary = {}
var pending_messages: Array = []

func push_message(message: Dictionary) -> void:
	pending_messages.append(message)
	pending_messages.sort_custom(func(a, b): return _priority_value(a) > _priority_value(b))

func dismiss_active() -> void:
	active_message = {}

func peek_next() -> Dictionary:
	return pending_messages[0] as Dictionary if not pending_messages.is_empty() else {}

func pop_next() -> Dictionary:
	if pending_messages.is_empty():
		return {}
	active_message = pending_messages.pop_front() as Dictionary
	return active_message

func list_pending() -> Array:
	return pending_messages.duplicate()

func _priority_value(message: Dictionary) -> int:
	return int(PRIORITY_ORDER.get(str(message.get("priority", "normal")), 1))
