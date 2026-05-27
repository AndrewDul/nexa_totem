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
- Menu Environment opens the Environment screen for ESP8266/BME688 room data.
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

The UI polls `/api/hardware/state` for local hardware state. Normal development uses about once per second. ESP mode can lower this with `NEXA_ESP_POLL_INTERVAL_SECONDS=0.2` so joystick and ultrasonic updates feel responsive.

"Local network connected" means NeXa is receiving recent ESP8266 hardware data. It does not mean the internet is connected.

The top-left local network indicator shows connected or disconnected based on fresh ESP8266 data.

The Environment screen shows temperature, humidity, pressure, gas resistance, air status, and advice when live data is available.

Distance `-1` means no valid ultrasonic echo. Distance above zero means a valid object/person distance was measured. Face/Clock switching uses a small stable delay so one bad reading does not flicker the UI.

The UI does not configure Wi-Fi, routing, DHCP, hotspot, or access point settings.

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
- Quick Shelf Reminders opens the local Reminders app.
- Quick Shelf Calendar opens the local Calendar app.
- Network, Camera, Logs, and Reports open Diagnostics with the selected tab active.
- Other Quick Shelf tiles show visible planned status instead of silently doing nothing.
- Quick Shelf scroll drag is limited to the scrollbar strip so it does not block normal tile taps.
- Study opens the NeXa Learn Study screen from Menu or Quick Shelf.
- NeXa Learn includes Smart Study, Flashcards, Quizzes, Languages, Study Stats, History, and Settings pages.
- Smart Study is the user-facing focus/session builder and supports custom focus and break segments.
- Smart Study segment lists scroll when they grow, while controls stay in a separate right-side column.
- Smart Study keeps Topic/Goal clear of the right controls, scrolls long segment lists, shows summary under the table, enforces alternating focus/break segments, and shows Stop/Finish during active sessions.
- Smart Study note prompts are tied to completed focus work, not break/rest segments.
- Face Home shows a running study session as plain `Focus: MM:SS` or `Break: MM:SS` text without a box.
- Study uses a reusable on-screen text input overlay for local touch entry.
- Physical keyboard input works while the on-screen keyboard remains visible.
- Flashcards uses one selected set at a time and guards Add Question, Start Study, and Delete until a set is selected.
- Flashcards uses a separate practice screen with answer checking, reveal answer, I know this, Not sure, I don't know, Next, Finish, Continue, and bottom green/red feedback.
- Quizzes uses one selected quiz at a time and guards Add Question, Start Quiz, and Delete until a quiz is selected.
- Quizzes uses a separate solve screen with visible A/B/C/D answer text, selected correct-answer creation, wrong feedback, marked review, and delete confirmation.
- Language Learning uses selected-list edit and separate practice screens with typed meaning checks, reveal answer, Correct/Wrong outcomes, and delete word/list actions.
- Study delete-all uses a two-step confirmation before sending the delete request.
- Study Stats is available inside Study, in Diagnostics, and from Quick Shelf when selected.
- Reminders opens from Menu and Quick Shelf as a local 640x480 app with Add/Edit/Delete, Upcoming and Past tables, selected-row editing, quick relative due times, and delete confirmation.
- Reminder due notifications show as a global overlay on any screen, in the top reminder indicator, and in Control Center Notifications.
- Control Center notification rows are built from real due reminders, with no static sample notifications.
- Control Center Notifications is generic and uses `No notifications` as the empty state.
- Control Center notification rows scroll inside their own list area when there are many notifications.
- Each Control Center reminder notification has a remove control, opens a compact detail modal when tapped, and can be dismissed with a left or right swipe.
- Removing a notification dismisses/hides that notification entry and keeps the original reminder record available in Reminders/Past.
- Private reminders use the existing PIN privacy state and show a locked placeholder until privacy is unlocked.
- Reminder due polling runs on a safe interval, date/time fields use centered fixed-width drawing, and date/time input uses a numeric datetime keyboard.
- Enabling a private reminder without a PIN opens Privacy PIN setup and preserves the reminder form state.
- Calendar opens from Menu and Quick Shelf as a local monthly calendar with a 42-cell Monday-start grid.
- Calendar draws English month/year headers, Previous/Next navigation, weekday labels, Sunday styling, today and selected-day highlights, and compact event indicators.
- Calendar day details support selected-event Add/Edit/Delete flows, event time, reminder, snooze, and repeat options.
- Calendar due notifications are local, global, and integrated into generic Control Center Notifications without deleting events.
- To Do opens from Menu and Quick Shelf as a local task app with list cards, emoji lists, New List, and scroll support.
- To Do list detail has Active and Completed sections, task details, Add/Edit/Delete, Mark Done, and Mark Active flows.
- To Do task forms support local reminders, snooze options, and repeat choices for every X hours, every X days, weekly, monthly, and yearly schedules.
- To Do due notifications are local, global, and integrated into generic Control Center Notifications without deleting tasks.
- Completed To Do tasks remain visible and stop reminder notifications.
- Games opens from Menu and Quick Shelf as a local Games Library.
- Tic-Tac-Toe is the first local game and runs inside the existing 640x480 Godot LCD UI.
- Tic-Tac-Toe supports Play with Someone and Play with NeXa.
- Play with NeXa uses deterministic local move logic, not AI models, LLM calls, backend calls, or external services.
- Games support touch, mouse, keyboard, and future joystick/remote input through shared NeXa input actions.
- Tic-Tac-Toe keeps Back and Exit separate: Back returns to the game menu, while Exit returns to Face Home.
- Face Home has a Home Message Mode where the NeXa face is on the LEFT (x=0..320) and all message/notification text appears on the RIGHT (x=342..606) without a card, border, or chat bubble.
- Home starts with a lightweight 5-second NeXa ToTem DevDul animation, then shows the startup greeting for 10 visible seconds.
- The startup greeting slides in from y=-180 to 0 and fades in; dismissal slides it out back to y=-180 before closing.
- The startup greeting uses the saved User preferred call name, then first name, then plain "Hello".
- Home Message Mode has a smooth enter and exit animation: text drops from the top on enter (face lerps from center to left); text exits upward on dismiss (face returns to center).
- Home Message Mode uses a circular close control at the top-right of the text area for manual dismissal.
- NeXa messages count their 4-second preview timer only while fully visible on Home, not during enter or exit animation.
- Messages Center rows support swipe-to-dismiss: swipe left or right 60px (with abs(dx)>abs(dy) guard) to remove a message; vertical movement is preserved for scroll.
- The face animates offscreen during screen transitions: left for Menu, right for Clock, down for Control Center, up for Quick Shelf. The face is not drawn over completed non-Home screens.
- Face Home includes a subtle HH:MM clock that stays separate from message and notification indicators.
- NeXa Messages stores system and conversational messages separately from Notification Center reminders.
- Settings includes a User profile page for first name, last name, and preferred call name.
- Top message and notification indicators are custom drawn with Godot primitives instead of emoji icons.
- Normal Reminder, Calendar, To Do, and Study prompts use Home Message Mode on Home or indicators/centers outside Home instead of full-screen popups.
- The Home behavior foundation includes startup greeting and soft idle blink states with LED and sound cue placeholders only.
- Screens return to Face Home after 30 seconds of inactivity, except Games; active text input is also respected.
- Hardware absence can show Clock after `presence_show_clock_after_seconds`, currently 3 seconds for the demo.
- Joystick repeat is controlled by `joystick_repeat_delay_seconds`, currently 0.28 seconds. Select requires returning to CENTER before it can trigger again.
- Smart Study can suggest a quick break game after 30 seconds of break time and return from Games when focus resumes.
- Display, Sound, Network, Remote, Diagnostics, Safety, About, and Exit NeXa pages are represented.
- About shows NeXa ToTem project, author Andrzej Dul, DevDul, hardware, software, features, settings, and safety notes.
- Settings Exit NeXa closes the NeXa UI/runtime only. It does not power off the Raspberry Pi.
- Settings stay within the fixed 640x480 window and use the existing scroll support when content is larger than the panel.
