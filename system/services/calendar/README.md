# Calendar Store

Calendar is a local-only SQLite module for NeXa ToTem.

- Database path: `var/data/calendar/nexa_calendar.db`.
- Tests can override the database with `NEXA_CALENDAR_DB_PATH`.
- The database and parent folder are created automatically.
- Schema version is `1` through SQLite `PRAGMA user_version`.
- The store uses Python standard library modules only.

The store keeps one row per calendar event. Repeating events are expanded only for the requested visible month/day or the small due-check window, so recurring events are not generated thousands of times in advance.

Calendar reminders are local. Dismissing a calendar notification updates reminder state and does not delete the event. Snooze creates a local snooze row and lets the same event notify again when the snooze time is reached.
