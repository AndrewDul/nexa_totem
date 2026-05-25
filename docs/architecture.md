# Architecture Log

This file is an append-only architecture log for NeXa ToTem. New decisions should be added as new dated entries.

## 2026-05-25 — Initial Repository Structure

Today I set up the clean repository structure for NeXa ToTem.

I decided to keep all project notes inside `docs/`. I decided not to add 3D printing or mechanical model folders yet, because this first structure is focused on the system, firmware, tests, scripts, assets, and config.

The main Raspberry Pi system modules live directly inside `system/`. I decided not to use `system/pi/app/` because the path is too long for this project.

The `firmware/` folder is for Arduino Uno, ESP8266 remote, and ESP32-S3 experiments.

The `tests/` folder is split into unit, integration, hardware, firmware, safety, and smoke tests.

The `scripts/` folder is split into setup, run, test, hardware, and git helper scripts.

The `assets/` folder is for UI, icons, sounds, and branding.

The `config/` folder is for example configuration files.

Each folder now has a `README.md` file that explains what the folder is for.

## 2026-05-25 — Repository Structure and Diagnostics Foundation

Today I set up the clean repository structure for NeXa ToTem.

I changed the system structure so main modules live directly under `system/`.

I decided not to use `system/pi/app/` because it makes paths too long for this project.

I decided to keep documentation inside `docs/`.

I decided not to add 3D printing or mechanical model folders yet.

I added `README.md` files inside every main folder and subfolder so each area has a clear purpose.

I added the first diagnostics foundation.

I added a shared component status format for future LCD UI and web panel.

I added a logging foundation so future diagnostic panels can show logs and status history.

I added Raspberry Pi health checks.

I added USB speaker/audio diagnostics.

I added scripts for Pi health, audio output, and combined system status.

I added unit tests for parser and status logic.

This prepares NeXa ToTem to report problems such as missing speaker, audio output problems, high temperature, undervoltage, or unknown Pi health state.

## 2026-05-25 — Camera Diagnostics Foundation

I added the first CSI camera diagnostics foundation.

The camera check is designed to be fast by default so it does not slow down the NeXa ToTem system.

The quick camera check detects available Raspberry Pi camera tools and checks whether a camera is visible.

The capture validation is optional and only runs when requested.

Camera status now uses the shared component status format.

The combined system status now includes Raspberry Pi health, USB speaker/audio status, and CSI camera status.

I added scripts for camera status and camera capture validation.

I added unit tests for camera parser, command selection, camera status, capture validation, and combined system status.

This prepares the future diagnostic panel to show camera state, camera errors, validation results, and saved reports.

## 2026-05-25 — Diagnostic Reports and Validation History Foundation

I added report helpers for latest and history diagnostic reports.

I added validation result helpers.

I added a diagnostic panel data backend shape.

The future diagnostic panel should read saved reports instead of running hardware checks every time.

This keeps the system fast.

I added a main `run_diagnostics.py` script.

I added test runner scripts.

I added README files explaining how the diagnostics and reports are organized.

This prepares NeXa ToTem to show logs, statuses, reports, validation results, and test results in one diagnostic panel later.

## 2026-05-25 — NeXa Resource Monitoring and Benchmark Foundation

I added a resource monitoring foundation for NeXa-owned processes.

The diagnostic panel should show NeXa resource usage, not the full Linux process list.

I added a process registry for backend, Godot LCD UI, web panel, camera service, sensor service, remote link, diagnostics runner, and test runner.

I added process CPU/RAM snapshot support.

I added benchmark helpers for component/check durations.

I added scripts for checking NeXa resources and running quick resource benchmarks.

I added saved report support for future diagnostic panel.

I prepared Godot telemetry placeholders for FPS, frame time, and render data, but I did not fake GPU usage.

GPU usage percent is reported as unsupported/unknown until there is a reliable measurement source.

## 2026-05-25 — Godot LCD UI Prototype Foundation

I started the first Godot UI prototype for the local NeXa ToTem screen.

The target display is 640x480 touch.

For this sprint, I use a fixed 640x480 window on the current HDMI monitor, not fullscreen.

Fullscreen LCD mode will be added later after the 2.8-inch LCD is connected and tested.

Face Home is the central screen.

Swipe left opens Menu.

Swipe right opens Clock.

Swipe down opens Notification + Control Center.

Diagnostics opens as a tabbed screen because there will be many data categories.

Python remains the backend and Godot is the local visual UI layer.

The UI must not run hardware checks directly; it should read saved reports or backend data later.
