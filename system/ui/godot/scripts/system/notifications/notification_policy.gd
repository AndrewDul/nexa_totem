extends RefCounted
class_name NexaNotificationPolicy

const DISPLAY_HOME_ONLY := "home_only"
const DISPLAY_INDICATOR_ONLY := "indicator_only"
const DISPLAY_HOME_OR_INDICATOR := "home_or_indicator"
const DISPLAY_URGENT_INTERRUPT := "urgent_interrupt"
const DISPLAY_SILENT_STORE := "silent_store"

const NORMAL_NOTIFICATION_POLICY := DISPLAY_HOME_OR_INDICATOR
const CRITICAL_INTERRUPT_RESERVED := true

static func should_interrupt(display_policy: String, priority: String) -> bool:
	return display_policy == DISPLAY_URGENT_INTERRUPT and priority == "critical"
