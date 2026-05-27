# To Do Store

To Do is a local-only SQLite module for NeXa ToTem.

- Database path: `var/data/todo/nexa_todo.db`.
- Tests can override the database with `NEXA_TODO_DB_PATH`.
- The database and parent folder are created automatically.
- Schema version is `1` through SQLite `PRAGMA user_version`.
- The store uses Python standard library modules only.

The store creates a default `📥 Inbox` list when no active lists exist. Lists and tasks use soft delete so deleted items disappear from the UI without requiring external cleanup.

Completed tasks remain visible in the Completed section and stop reminder notifications. Marking a task active can re-enable an existing reminder schedule.

To Do reminders are local. Dismiss advances repeating reminders or disables one-shot reminders without deleting the task. Snooze moves the next reminder into the future and hides the current notification until that time.

