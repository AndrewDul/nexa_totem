# Reminders Store

Reminders is a local-only SQLite module for NeXa ToTem.

- Database path: `var/data/reminders/nexa_reminders.db`.
- Tests can override the database with `NEXA_REMINDERS_DB_PATH`.
- The database and parent folder are created automatically.
- Schema version is `1` through SQLite `PRAGMA user_version`.
- The store uses Python standard library modules only.

The module stores active, due, dismissed, and archived reminders plus reminder events. Past reminders are kept until the user deletes them manually, so old reminders can be edited and reused by setting a new future due time.

Private reminders integrate with the existing Settings privacy state. When private reminders are enabled and privacy is locked, API payloads return `Private reminder locked` with `requires_pin: true` instead of exposing reminder text.

Reminder list splitting is based on `due_at` relative to current time. Future reminders appear in Upcoming even if they were previously due or dismissed, and past reminders remain in Past until deleted.

Due reminders stay in the due response after `mark-triggered` until the user dismisses or snoozes them. Snooze moves the reminder back to active/upcoming with a future due time.

Control Center notification removal uses reminder dismiss, not reminder delete. Dismissed reminders are hidden from due notification lists but remain in the database and continue to appear in Past until the user deletes them from the Reminders app.

The store accepts Godot UI date/time values such as `YYYY-MM-DDTHH:MM:SS` and timezone-aware Python ISO strings. Naive UI values are treated as local wall time before UTC comparison.
