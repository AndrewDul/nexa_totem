extends RefCounted
class_name HomeBehaviorRegistry

const BEHAVIORS := {
	"startup_greeting": {
		"expression": "happy",
		"eyes": "open_soft_one_blink",
		"mouth": "small_smile",
		"led_behavior": "startup_soft",
		"sound_cue": "startup_chime"
	},
	"idle_calm": {
		"expression": "calm",
		"eyes": "soft_idle_blink",
		"mouth": "neutral_soft_smile",
		"led_behavior": "idle_soft",
		"sound_cue": "none"
	},
	"notification_soft": {
		"expression": "focused",
		"eyes": "attentive",
		"mouth": "neutral",
		"led_behavior": "notification_blue",
		"sound_cue": "notification_chime"
	},
	"warning_soft": {
		"expression": "concerned",
		"eyes": "slightly_narrowed",
		"mouth": "concerned_small_curve",
		"led_behavior": "warning_amber",
		"sound_cue": "warning_soft"
	},
	"private_locked": {
		"expression": "locked",
		"eyes": "calm_narrow",
		"mouth": "neutral",
		"led_behavior": "private_lock",
		"sound_cue": "none"
	}
}

func behavior_for_name(name: String) -> Dictionary:
	return BEHAVIORS.get(name, BEHAVIORS["idle_calm"])
