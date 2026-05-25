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
