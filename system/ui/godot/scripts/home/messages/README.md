# Home Messages

This folder defines NeXa message data and queue behavior for messages NeXa wants to communicate.

Use it for message models, priority ordering, display policy notes, preview timing, and future small message helpers. Do not put Reminder, Calendar, or To Do storage here; those stay in their own services and appear through notifications.

`main.gd` currently mirrors the runtime state for Home Message Mode and Message Center. Message previews slide in with an enter animation (text from y=-180 to 0 on the RIGHT at x=342, face from idle center x=320 to message center x=160 on the LEFT), auto-dismiss after 4 seconds of actual Home visibility, and exit with a smooth animation (text slides back to y=-180, face returns to idle center x=320) before closing. Closing a preview does not delete the stored message or source notification.

Messages Center rows support swipe-to-dismiss: a left or right swipe of 60px or more (with abs(dx)>abs(dy) guard to preserve vertical scroll) removes the row and calls `_dismiss_nexa_message_by_id`.
