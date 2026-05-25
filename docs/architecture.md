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

