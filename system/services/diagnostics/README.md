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

## Live Diagnostics API

`live_api.py` exposes a lightweight local API for the Godot LCD UI.

- The server binds only to `127.0.0.1:8769`.
- Live collectors use safe subprocess timeouts and return Unknown or empty lists when data is unavailable.
- Read endpoints use short TTL caches so the UI can show cached data immediately.
- Running or slow work returns pending/running states instead of blocking the UI.
- Control Center has a lightweight `/api/control-center` endpoint that avoids full network scans.
- `/api/network` returns connected, saved, and available Wi-Fi networks when they can be read safely.
- `/api/control-center` avoids full saved/available Wi-Fi lists so swipe-down stays fast.
- Diagnostics tabs request their own data, such as system, processes, audio, camera, network, logs, and reports.
- Benchmarks and report generation run only after button requests.
- Camera preview is off by default and starts only when the UI toggle requests it.
- Camera preview prefers a persistent low-FPS MJPEG session when available.
- Camera preview uses one live worker/session while enabled, not repeated still-image process launches.
- Preview stops on off, close, or stale timeout to release the camera and protect Raspberry Pi memory.
- GPU usage is not faked; it is reported as not supported unless a reliable source is available.
- Wi-Fi, brightness, sound, and remote-network write actions are safe prototype state or dry-run/planned actions in this sprint.
- Network connect/write actions remain dry-run/planned and do not disconnect or modify the current Wi-Fi connection.
