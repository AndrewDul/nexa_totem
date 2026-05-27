extends RefCounted
class_name NexaInputRouter

const ACTION_UP := "nexa_up"
const ACTION_DOWN := "nexa_down"
const ACTION_LEFT := "nexa_left"
const ACTION_RIGHT := "nexa_right"
const ACTION_ACCEPT := "nexa_accept"
const ACTION_BACK := "nexa_back"
const ACTION_EXIT := "nexa_exit"

const ACTIVITY_INPUTS := [ACTION_UP, ACTION_DOWN, ACTION_LEFT, ACTION_RIGHT, ACTION_ACCEPT, ACTION_BACK, ACTION_EXIT]

# main.gd owns the active router today. This file records the shared actions
# used by touch, mouse, keyboard, and future remote/joystick input.
