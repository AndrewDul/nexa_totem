# Diagnostics Service

This folder contains the shared diagnostics foundation for NeXa ToTem.

Component status reports describe the current state of one part of the system. They use a plain dictionary with a component name, status, message, details, check time, and source.

The combined system status joins component reports into one system report for `nexa_totem`.

Report helpers can save JSON files under `var/reports/diagnostics/`.

Latest reports live under `var/reports/diagnostics/latest/`. They are for quick reads by the future diagnostic panel.

History reports live under `var/reports/diagnostics/history/`. They are timestamped so the system can show what changed over time. The helpers can prune older history reports to avoid filling the SD card.

Validation results describe a test that was run. They include the validation name, status, message, start time, finish time, duration, details, and source.

The panel data helper builds one backend dictionary for a future LCD UI or web panel. It reads saved JSON reports only. It does not run hardware checks, camera checks, audio checks, or tests by default. This keeps the panel fast and avoids slowing normal runtime.

The panel data helper can also read saved NeXa resource reports and benchmark reports. These reports show NeXa components and checks, not the full Linux process table.

Reports are only saved when a script asks for them, such as with `--save-report` or `--save-history`.
