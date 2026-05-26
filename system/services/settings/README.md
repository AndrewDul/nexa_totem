# NeXa Settings

`settings_store.py` keeps local prototype settings for the NeXa ToTem LCD UI.

- Settings live under `var/data/nexa_settings.json`.
- Missing or broken JSON falls back to safe defaults.
- Updates validate known sections and keys before saving.
- `POST /api/settings/update` is used by the Godot Settings UI for row changes.
- `POST /api/settings/update-many` saves grouped updates such as Appearance presets.
- `POST /api/settings/update-many` also supports grouped Appearance time/date color updates.
- `POST /api/settings/reset-section` can restore a known section to defaults.
- Appearance color values are validated against the built-in color list.
- Appearance stores clock/date color keys: `time_color`, `hour_color`, `minute_color`, `second_color`, `date_color`, `day_color`, `month_color`, and `year_color`.
- Grouped Time color updates apply to hour, minute, and second colors; grouped Date color updates apply to day, month, and year colors.
- Appearance presets are validated against the built-in preset list.
- PINs are never stored raw; the store saves a salt and PBKDF2 hash.
- PIN setup uses `/api/privacy/pin/set`, unlock uses `/api/privacy/pin/verify`, and manual locking uses `/api/privacy/lock`.
- `GET /api/settings` removes `pin_hash` and `pin_salt` before returning data.
- `GET /api/privacy/status` reports only safe lock/unlock state.
- Private notifications and private reminders use the PIN unlock state to decide whether content should be hidden.
- Hardware-facing actions are safe prototype settings in this sprint.
- Wi-Fi connect, Remote Wi-Fi/AP, restart, reboot, power, and Exit NeXa actions are planned/dry-run only.
