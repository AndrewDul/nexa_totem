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

The current visual direction is polished toward a premium Apple-like style while staying lightweight for Raspberry Pi 5 2GB.

- Face Home uses a pure dark screen with vertical blue bean eyes and a rounded blue mouth.
- Redraw is throttled and the project caps runtime at 30 FPS for Raspberry Pi 5 2GB.
- Runtime script errors from unsafe helper calls and `.translated()` usage were fixed.
- Strong eye glow was removed so the face stays clean and sharp.
- Menu uses a compact 2-column rounded tile layout with large touch targets.
- Text overflow was reduced with short labels and subtitles.
- Fonts were reduced slightly for the 640x480 display.
- Content overflow now has lightweight scroll support.
- Diagnostics content can scroll inside its content card.
- Control Center content can scroll if needed.
- Face Home has a subtle idle blink about every 10 seconds.
- Control Center and Diagnostics use visible rounded cards, tiles, pills, soft borders, and dark glass-like panels.
- Screen changes use faster, cheaper slide transitions.
- Panel transitions draw Face Home as the base plus one moving overlay panel.
- Panels do not stack; Face Home remains the center.
- Reverse swipes close panels back to Face Home.
- The UI remains fixed 640x480 windowed mode during development.

The Diagnostics screen uses tabs because diagnostics will have many categories.

Godot is the local visual UI layer only. Python remains the backend and the source of system logic, diagnostics, reports, and resource data.

The UI must not run hardware checks directly. Later it should read from the Python backend API or saved diagnostic reports.
