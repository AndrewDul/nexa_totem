# CSI Camera

This folder is for Raspberry Pi CSI camera code and camera status checks.

The current module provides the first camera diagnostics foundation.

It supports fast checks for Raspberry Pi camera tools:

- `rpicam-hello`
- `libcamera-hello`
- `rpicam-still`
- `libcamera-still`

The normal status check only lists cameras. It does not open a preview or capture an image.

Optional capture validation saves a small test image under `var/reports/camera/` when it is explicitly requested. Generated reports and images are ignored by Git.
