# Godot LCD UI Prototype

This is the first local premium LCD UI prototype for NeXa ToTem.

The target screen is a 2.8-inch 640x480 touch display in landscape orientation.

For this sprint, development runs on the current HDMI monitor as a fixed 640x480 window. Fullscreen LCD mode is not enabled yet.

Fullscreen mode will be added later after the real 2.8-inch LCD is connected and tested.

Face Home is the center of the UI.

- Swipe left to open Menu.
- Swipe right to open Clock.
- Swipe down to open Notification Control Center.
- Tap the face to show a small status bubble.
- Long press the face to show a setup placeholder.

The Diagnostics screen uses tabs because diagnostics will have many categories.

Godot is the local visual UI layer only. Python remains the backend and the source of system logic, diagnostics, reports, and resource data.

The UI must not run hardware checks directly. Later it should read from the Python backend API or saved diagnostic reports.
