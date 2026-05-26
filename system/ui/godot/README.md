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
- Menu Time opens the same Clock screen as the Face Home swipe gesture.
- Clock shows hours, minutes, seconds, day, month, and year.
- Clock closes back to Face Home with any swipe.

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
- Raspberry Pi runtime uses Godot Compatibility/OpenGL renderer for stability.
- Vulkan/Mobile crashed on Pi 5 2GB during Control Center with MESA GPU memory allocation errors.
- Control Center uses safe mode drawing with a fixed, lightweight panel.

The Diagnostics screen uses tabs because diagnostics will have many categories.

Godot is the local visual UI layer only. Python remains the backend and the source of system logic, diagnostics, reports, and resource data.

The UI must not run hardware checks directly. Later it should read from the Python backend API or saved diagnostic reports.

The current prototype now reads live diagnostics through the local Python API at `127.0.0.1:8769`.

- Godot does not run hardware checks or shell commands directly.
- Control Center uses a lightweight `/api/control-center` request so opening it stays instant.
- Control Center opens from cached/default state first, then refreshes API data after the slide transition.
- The Wi-Fi tile opens a compact detail panel with the connected network, up to three saved networks, and up to three available networks.
- Brightness and sound sliders are interactive prototype controls that update locally immediately.
- Diagnostics requests only the active tab data and shows Pending or API offline when data is not ready.
- Processes, System, and Camera tabs poll only while open.
- Camera preview is low-FPS, controlled by an explicit toggle, and stopped when the camera tab or Diagnostics closes.
- Camera tab fetches the latest preview frame only while Camera is active and preview is on.
- Camera tab uses a compact layout that stays inside the Diagnostics panel.
- Preview is stopped when leaving Camera, leaving Diagnostics, or returning Home/Escape.
- Remote Wi-Fi means NeXa's own network/AP state; Remote means the handheld controller connection state.
- Benchmark, report, camera check, and audio check buttons use pending/running/done states.
- Network tab shows connected, saved, and available Wi-Fi networks when they can be read safely.
- Benchmarks run on demand and show result rows after completion.
- Wi-Fi connect actions are planned/dry-run in this sprint; the UI does not change real network connections.
- Wi-Fi and remote network write actions are dry-run/planned in this sprint.

## Settings MVP

The Godot UI now includes an Apple-like Settings Home with large rounded tiles and detail pages.

- Settings tiles are clickable and open their detail pages.
- Settings rows update local state immediately and save through the local API.
- Appearance covers presets, eye color, mouth color, tile accent, background, and LED color.
- Appearance can update the Face Home eye/mouth preview colors and active tile accent.
- Appearance uses lightweight dropdown-style option lists for colors and presets.
- Appearance can customize whole time, hour, minute, second, whole date, day, month, and year colors.
- Theme presets update eye, mouth, tile accent, background, and LED color together.
- Background and active tile accent changes are visible in the live UI.
- Notifications covers style, Face Home display, sound, LED, face expression, behaviour, private notifications, and private reminders.
- Privacy provides a usable 4-digit PIN setup/unlock/lock flow for private notifications and reminders.
- Modes includes Normal, Quiet, Focus, Night, Away, Demo, and Maintenance.
- Quick Shelf lets the user choose which tiles should appear in the future bottom swipe-up shelf and saves the selection.
- Face Home swipe-up opens the actual Quick Shelf bottom panel using the selected tiles.
- Quick Shelf slides up from the bottom and closes with swipe-down, Escape, or Home.
- Quick Shelf tiles are clickable.
- Quick Shelf Settings, Diagnostics, Clock, Network, Camera, Logs, and Reports actions are wired.
- Network, Camera, Logs, and Reports open Diagnostics with the selected tab active.
- Other Quick Shelf tiles show visible planned status instead of silently doing nothing.
- Quick Shelf scroll drag is limited to the scrollbar strip so it does not block normal tile taps.
- Display, Sound, Network, Remote, Diagnostics, Safety, About, and Exit NeXa pages are represented.
- About shows NeXa ToTem project, author Andrzej Dul, DevDul, hardware, software, features, settings, and safety notes.
- Safety and Exit NeXa actions are planned/safe only; the UI does not power off or reboot the Raspberry Pi.
- Settings stay within the fixed 640x480 window and use the existing scroll support when content is larger than the panel.
