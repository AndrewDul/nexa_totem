extends RefCounted
class_name NexaMessage

const MESSAGE_TYPES := ["greeting", "info", "reminder", "calendar", "todo", "study", "system", "diagnostic", "warning", "critical", "private"]
const PRIORITIES := ["silent", "normal", "reminder", "important", "warning", "critical"]
const DISPLAY_POLICIES := ["home_only", "indicator_only", "home_or_indicator", "urgent_interrupt", "silent_store"]
const DEFAULT_DISPLAY_POLICY := "home_or_indicator"

var id := ""
var title := ""
var body := ""
var source := ""
var message_type := "info"
var priority := "normal"
var expression := "calm"
var led_behavior := "idle_soft"
var sound_cue := "none"
var is_private := false
var display_policy := DEFAULT_DISPLAY_POLICY
var actions: Array = []
var created_at := ""
var expires_after_seconds := 0.0

func to_dictionary() -> Dictionary:
	return {
		"id": id,
		"title": title,
		"body": body,
		"source": source,
		"message_type": message_type,
		"priority": priority,
		"expression": expression,
		"led_behavior": led_behavior,
		"sound_cue": sound_cue,
		"is_private": is_private,
		"display_policy": display_policy,
		"actions": actions,
		"created_at": created_at,
		"expires_after_seconds": expires_after_seconds
	}
