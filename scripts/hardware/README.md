# Hardware Scripts

This folder is for scripts that help test sensors, lights, servos, and other hardware.

The first scripts check Raspberry Pi health, USB speaker audio, CSI camera status, optional CSI camera capture validation, and combined system status.

`run_diagnostics.py` is the main diagnostics runner. It runs fast checks by default:

- Raspberry Pi health
- USB speaker/audio status
- CSI camera quick status
- combined system status

Fast checks do not run heavy validation by default. Camera capture validation only runs through `capture_camera_test.py` or through `run_diagnostics.py --include-camera-capture`.

The audio test sound is optional and only runs when requested.

Diagnostics scripts can print JSON with `--json`. They can save latest reports with `--save-report` and timestamped history reports with `--save-history` when the script supports it.

Saved reports are prepared for the future diagnostic panel. The panel should read saved JSON instead of running hardware checks every time it opens.
