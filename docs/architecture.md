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

## 2026-05-25 — Godot UI Premium Visual Polish

I improved the visual direction of the Godot LCD UI prototype.

I refined typography, spacing, rounded cards, and tile style.

I kept the UI fixed at 640x480 windowed mode for development.

I kept Face Home clean and removed debug labels.

I kept vertical blue bean eyes and a blue rounded mouth as the main face direction.

I added or prepared smoother slide transitions.

I kept navigation centered on Face Home so panels do not stack.

## 2026-05-25 — Godot UI Runtime and Performance Polish

I fixed runtime drawing helper problems in the Godot prototype.

I reduced visual effects that caused lag.

I kept the face clean with vertical blue eyes and reduced glow.

I changed Menu and Control Center to use visible rounded cards and tiles.

I kept transitions lightweight.

I kept the UI fixed at 640x480 windowed mode.

I kept Face Home as the center so panels do not stack.

## 2026-05-25 — Godot UI Runtime Stability and Tile Layout Polish

I fixed a Godot runtime issue caused by Rect2.translated usage.

I tightened the UI layout so menu tiles use short labels and avoid overflow.

I changed the transition approach to be lighter and faster.

I kept the UI fixed at 640x480 windowed mode.

I kept the screen style dark, simple, and card-based.

## 2026-05-25 — Godot UI Scroll and Idle Blink Polish

I added lightweight scroll support for content that does not fit on the 640x480 screen.

I added subtle idle eye blinking to Face Home.

I reduced UI font sizes slightly to avoid text overflow.

I kept transitions fast and lightweight.

I kept the UI fixed at 640x480 windowed mode.

## 2026-05-25 — Live Diagnostics API and Lazy Godot Data Loading

I added a local diagnostics API for real status data.

I kept Godot fast by using lazy loading and cached data.

I wired Control Center and Diagnostics toward real system, process, audio, camera, network, logs, reports, and benchmark data.

I made camera preview toggle-controlled so it does not run all the time.

I kept heavy checks as on-demand jobs with pending/running/done states.

I kept Wi-Fi and remote network write actions as safe dry-run/planned actions for now.

## 2026-05-25 — Control Center Performance and Live Diagnostics Completion

I changed Control Center to open from cached/default state first.

I delayed data refresh until after the slide transition so the UI does not lag.

I added interactive brightness and sound prototype sliders.

I added CPU usage and GPU status to diagnostics overview.

I improved camera preview lifecycle and Camera tab layout.

I added saved/available Wi-Fi list support where safely available.

I made benchmark results visible after on-demand runs.

I kept network and remote actions dry-run/planned for safety.

## 2026-05-25 — Godot Raspberry Pi Renderer Stability Fix

I switched the Godot LCD UI to Compatibility/OpenGL mode for Raspberry Pi stability.

Vulkan/Mobile crashed with MESA device memory allocation errors on Pi 5 2GB.

I kept the UI fixed at 640x480 windowed mode.

I simplified Control Center drawing so swipe-down does not freeze or crash.

I kept API refresh delayed until after the Control Center transition.

## 2026-05-25 — Camera Live Preview and Benchmark Crash Fix

I fixed a Benchmark tab crash caused by null API result data.

I added safe handling for missing benchmark result dictionaries.

I changed camera preview toward a real live preview worker/session while enabled.

I kept preview off by default and stopped it on off/close/stale timeout.

I cleaned the Camera diagnostics layout so controls stay inside the content panel.

## 2026-05-25 — Camera Preview Smoothness and Diagnostics Layout Fix

I improved camera preview toward a persistent MJPEG live session when available.

I kept preview low FPS and stopped it on off/close/stale timeout.

I fixed Diagnostics Overview overflow.

I fixed Camera tab right-column overflow.

I clarified Remote naming in the UI.

## 2026-05-25 — Wi-Fi Details and Camera Preview Smoothing

I added Wi-Fi details to Control Center.

I showed connected, saved, and available Wi-Fi networks in Diagnostics Network.

I kept Wi-Fi connection changes dry-run/planned.

I kept Control Center lightweight by loading network lists only on Wi-Fi details or Network tab.

I improved camera preview toward smoother persistent MJPEG frame updates.

## 2026-05-25 — Godot LCD UI and Live Diagnostics MVP Checkpoint

I finished the first useful Godot LCD UI foundation for NeXa ToTem.

The UI runs as a fixed 640x480 window for development. Fullscreen LCD mode is still disabled until the real 2.8-inch screen is tested.

I switched Godot to Compatibility/OpenGL mode because Vulkan/Mobile caused Raspberry Pi GPU memory crashes on the Pi 5 2GB. The launcher now keeps the safer OpenGL path for development.

I kept Face Home as the center of the product UI. From Face Home the user can open Menu, Clock, Control Center, Notifications/Control Center, and Diagnostics without stacking panels.

I improved Control Center so it opens from cached/default state first. Data refresh happens after the slide transition so the panel does not freeze the UI.

I added live diagnostics through a local Python API on localhost. Godot does not run hardware checks directly. It asks the API for data and shows Pending, Unknown, or dry-run states when data is not ready.

I added real or safely collected diagnostics for Raspberry Pi health, CPU temperature, CPU usage, RAM usage, disk/system data, USB speaker status, CSI camera status, Wi-Fi state, logs, reports, and benchmark results.

I added interactive prototype controls for brightness, sound, quiet mode, remote network state, and Wi-Fi details. Wi-Fi and remote network write actions stay dry-run/planned for safety.

I added Wi-Fi details in Control Center. The Wi-Fi tile can show the current connected network, saved networks, and available networks without making the main Control Center open slowly.

I improved Diagnostics Network so it shows connected Wi-Fi, saved Wi-Fi networks, available Wi-Fi networks, Remote Wi-Fi state, and Remote controller state.

I clarified naming in the UI. Remote Wi-Fi means NeXa's own remote network/AP state. Remote means the physical handheld controller connection state. I removed the confusing Pilot label from the user-facing UI.

I added a camera diagnostics tab with a preview area and compact status/actions layout. The preview is off by default and starts only when the user toggles it on.

I changed camera preview toward a persistent MJPEG live session when available. It avoids spawning a separate still-image capture for every frame. Preview stops when turned off, when leaving Camera/Diagnostics, or after stale timeout.

I fixed the Benchmark tab crash caused by missing/null result data. Benchmark data is now handled safely and benchmark results are shown only after the user runs them.

I kept tests and validators in place for the Godot UI, diagnostics API, camera preview lifecycle, network data, OpenGL renderer stability, and no-fullscreen development mode.

