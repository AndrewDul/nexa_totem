# Hardware Scripts

This folder is for scripts that help test sensors, lights, servos, and other hardware.

The first scripts check Raspberry Pi health, USB speaker audio, CSI camera status, optional CSI camera capture validation, and combined system status.

Fast checks do not run heavy validation by default. Camera capture validation only runs through `capture_camera_test.py`.

Diagnostics scripts can print JSON with `--json`. They can save the latest report under `var/reports/diagnostics/` with `--save-report`.
