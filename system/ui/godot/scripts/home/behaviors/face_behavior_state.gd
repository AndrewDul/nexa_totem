extends RefCounted
class_name FaceBehaviorState

var current_face_expression := "calm"
var current_led_behavior := "idle_soft"
var current_sound_cue := "none"
var behavior_last_applied_id := ""

func apply_behavior(behavior_id: String, behavior: Dictionary) -> void:
	behavior_last_applied_id = behavior_id
	current_face_expression = str(behavior.get("expression", "calm"))
	current_led_behavior = str(behavior.get("led_behavior", "idle_soft"))
	current_sound_cue = str(behavior.get("sound_cue", "none"))
