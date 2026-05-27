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

## 2026-05-25 — Settings MVP and Private PIN Foundation

I added the first Settings MVP for NeXa ToTem.

I added Appearance, Notifications, Modes, Quick Shelf, Display, Sound, Network, Remote, Privacy, Diagnostics, and Safety sections.

I added private notifications and private reminders settings.

I added a 4-digit PIN foundation and store only hash/salt, not the raw PIN.

I added a local settings store under var/data.

I kept settings actions safe/prototype where hardware actions are not ready.

I kept the Godot UI fixed at 640x480 windowed mode and OpenGL/Compatibility.

## 2026-05-25 — Settings End-to-End Interaction Fix

I fixed Settings navigation so tiles open their detail pages.

I connected Settings rows to real settings updates.

I wired Appearance, Notifications, Modes, Quick Shelf, Display, Sound, Network, Remote, Privacy, Diagnostics, and Safety pages.

I kept PIN-based private notifications/reminders safe with hash/salt storage.

I kept Safety/Exit actions planned/safe only.

I added tests to catch Settings routing and update regressions.

## 2026-05-25 — Appearance Dropdowns, Quick Shelf Panel, and About Page

I changed Appearance choices to use dropdown-style option lists.

I made background color, tile accent color, and presets apply visibly instead of only saving.

I added the bottom swipe-up Quick Shelf panel that uses the selected Settings tiles.

I added an About page with project, author, DevDul, hardware, software, features, settings, and safety information.

I kept real hardware/network/power actions safe or planned where they are not ready.

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

## 2026-05-25 — Quick Shelf Tile Interaction Fix

I fixed Quick Shelf tile tap routing.

I changed Quick Shelf scroll drag so it does not consume normal tile taps.

I made Quick Shelf tiles open Settings, Diagnostics, Clock, and selected Diagnostics tabs.

I kept unfinished Quick Shelf tiles as visible planned actions.

I kept Exit NeXa planned/safe only.

## 2026-05-25 — Clock Menu Routing and Appearance Time Colors

I wired the Menu Time tile to open the Clock screen.

I made the Clock screen close back to Face Home with any swipe.

I added seconds to the Clock screen.

I added Appearance color settings for time, hour, minute, second, date, day, month, and year.

I made grouped Time color and Date color updates apply to their related parts.

I kept the UI fixed at 640x480 and OpenGL/Compatibility.

## 2026-05-26 — NeXa Learn Study MVP

I added the NeXa Learn / Study module.

I added a local SQLite database under var/data/study/nexa_study.db.

I added Pomodoro topics with duplicate/similar topic checks.

I added Flashcard decks with persistent cards, statuses, notes, and review progress.

I added Quizzes with persistent questions, attempts, wrong/marked status, and progress.

I added Language Learning with word lists, pronunciation, meanings, review counts, and mastered logic.

I added Smart Study sessions and notes.

I added Study History and Study Settings.

I added Study Stats in Study, Diagnostics, and Quick Shelf.

I kept web panel and remote text input planned for later.

I kept the UI fixed at 640x480 and OpenGL/Compatibility.

## 2026-05-26 — Study Interaction Completion

I merged Pomodoro-style timing into Smart Study.

I changed the Face Home study timer overlay to plain Focus text.

I added custom Smart Study focus/break segments with validation.

I added optional break notes.

I completed the Flashcards editor and review flow with typed answer, reveal answer, I know this, Not sure, and I don't know.

I completed the Quiz editor and solving flow with selectable correct answer A/B/C/D.

I added the Language Learning Wrong review path.

I made Study delete actions two-step safe confirmations.

I added physical keyboard support while keeping the on-screen keyboard.

I removed the Back tile from Study Home.

## 2026-05-26 — Study UX Correction After Manual Test

I added scroll support for long Smart Study segment lists.

I moved Smart Study controls so they do not cover segments.

I made break note controls appear only during breaks.

I clarified Stop and Finish behaviour for active Smart Study sessions.

I redesigned Flashcards around a single selected set, answer checking, reveal answer, review confidence, and a 50-correct mastered threshold.

I redesigned Quizzes around a single selected quiz, A/B/C/D question creation, selected correct answer, and solve mode.

I kept physical keyboard and on-screen keyboard working together.

I kept Study Home without Pomodoro and Back tiles.

## 2026-05-26 — Study Practice Window UX Finalization

I fixed Smart Study layout so Topic/Goal no longer sit under right-side controls.

I added segment-list scrolling and moved summary under the segment table.

I enforced alternating focus/break segment rules.

I moved note prompts to completed focus segments instead of breaks.

I redesigned Flashcards into a selected-set list plus separate practice screen.

I added clear answer checking, reveal answer, bottom feedback, and Finish/Continue for Flashcards.

I redesigned Quizzes into a selected-quiz list plus separate solve screen with visible A/B/C/D answers.

I redesigned Languages into selected-list edit and practice screens with typed meaning checking.

I kept the UI touch-friendly on 640x480.

## 2026-05-26 — Local Reminders App and Reminder Notifications

I added the Reminders app in Menu.

I added a local SQLite reminders database under var/data/reminders/nexa_reminders.db.

I added Add/Edit/Delete reminder flows.

I split reminders into Upcoming and Past tables.

I kept past reminders after due time so the user can reuse/edit/delete them manually.

I added due reminder notifications on Face Home, top indicator, and Control Center/notification area.

I integrated private reminders with the existing PIN privacy system.

I added Reminders to Quick Shelf.

I added tests and validators for reminders.

## 2026-05-26 — Reminder Notification Trigger and Private PIN Fix

I fixed due reminder polling so reminders actually appear on Face Home, top badge, and Control Center.

I fixed the Reminders date/time fields so values stay inside their fields.

I added numeric/date-time keyboard mode for date and time input.

I made Private reminder toggle check whether a PIN exists.

I route users to Privacy PIN setup when they enable private reminders without a PIN.

I preserved reminder form state while setting up PIN.

I strengthened reminders tests around due reminders, snooze, dismiss, and private locked reminders.

## 2026-05-26 — Notification Center Reminder Actions

I replaced static Control Center notification rows with reminder-driven notifications.

I added delete/dismiss controls to each notification row.

I added tap-to-open notification detail modal.

I added swipe left/right dismiss for notification rows.

I kept notification dismissal separate from deleting reminder records.

I kept private reminder content locked until PIN/privacy unlock.

## 2026-05-26 — Final Notification Runtime Fix

I fixed edited past reminders so future due times move them back to Upcoming.

I made the due reminder modal global so it can appear on any screen.

I fixed Control Center Notifications so due reminders appear there too.

I made the Notifications section generic, with "No notifications" as empty state.

I added scroll support for many notification rows.

I kept notification dismissal separate from deleting reminder records.

## 2026-05-26 — Local Calendar App

I added the Calendar app in Menu.

I added a local SQLite calendar database under var/data/calendar/nexa_calendar.db.

I added a monthly 42-cell calendar grid with Previous/Next navigation.

I added weekday labels M T W T F S S, Sunday styling, today highlight, selected day highlight, and event indicators.

I added day details, Add/Edit/Delete event flows, reminders, snooze, and repeat options.

I added lightweight calendar reminder polling and generic notifications integration.

I kept the UI fixed at 640x480 and OpenGL/Compatibility.

## 2026-05-26 — Local To Do App and Task Notifications

I added the To Do app in Menu and Quick Shelf.

I added a local SQLite To Do database under var/data/todo/nexa_todo.db.

I added task lists with emoji, New List, and scrollable list cards.

I added task list screens with Active and Completed sections.

I added Add/Edit/Delete task flows, Mark Done, Mark Active, reminders, snooze, and repeat settings.

I added To Do due reminder polling.

I connected To Do reminders to the global notification modal and Control Center Notifications.

I kept completed tasks visible but stopped their notifications.

I kept the UI fixed at 640x480 and OpenGL/Compatibility.

## 2026-05-26 — Local Games Library and Tic-Tac-Toe

I added a local Games screen in Menu.

I added Tic-Tac-Toe as the first local game.

I kept the game inside the existing 640x480 Godot LCD UI, not as a separate window.

I added Play with Someone and Play with NeXa.

I made Play with NeXa use deterministic local logic, not AI models or LLM calls.

I added input support for touch, mouse, keyboard and future remote/joystick through shared NeXa input actions.

I added Back and Exit behavior, where Back returns to the game menu and Exit returns to Face Home.

I kept the game lightweight for Raspberry Pi 5 2GB.

I kept global notifications working above the game.

## 2026-05-26 — Home Message System, Behaviors and Non-Intrusive Indicators

I added the Home Message Mode direction where the face stays alive on the left and text appears on the right without boxes, borders or chat bubbles.

I added a message model and queue foundation for NeXa/system messages.

I added a behavior registry foundation for face expression, LED behavior and sound cue mapping.

I added custom top-bar indicators for NeXa messages and notifications.

I changed normal notifications so they do not interrupt every screen with full popups.

I kept full message content available through Home Message Mode, Message Center and Notification Center.

I added initial behaviors: startup greeting and soft idle blink.

I added the Smart Study break game suggestion after 30 seconds of break time.

I kept games exempt from normal inactivity return, but allowed Study break end to close break games and return to focus.

## 2026-05-26 — Home Startup Animation and Message Timing Polish

I added the NeXa ToTem DevDul startup animation as a lightweight Home sequence inside the existing Godot LCD UI.

I made the startup greeting auto-dismiss after 10 seconds.

I made NeXa messages auto-dismiss 10 seconds after they are actually visible on Home, so messages created while the user is in another app wait behind the indicator until they are seen.

I added a circular close button for Home messages. Closing a preview only hides the preview; it does not delete reminder, calendar, or To Do source records.

I balanced Home Message Mode into a left face half and right text half.

I added a subtle Home clock that avoids the message and notification indicators.

I fixed Home notification previews so reminders are not hidden forever behind the greeting. Pending reminders can appear on Home after the greeting closes.

I kept non-Home notifications non-intrusive through top indicators and Notification Center.

I kept the Smart Study break game suggestion behavior.

## 2026-05-26 — User Profile Greeting and Slower Startup Polish

I slowed the NeXa ToTem startup animation from 3 seconds to 5 seconds.

I made the startup greeting slide down softly after the startup animation.

I removed the hardcoded user name from the startup greeting.

I added Settings -> User with first name, last name, and preferred call name.

I made the greeting use preferred call name first, then first name, then plain Hello.

I kept the greeting visible for 10 seconds after it is actually shown.

I kept reminders and notifications able to appear after the greeting closes.

## 2026-05-27 — Home Animation Polish: Swipe Delete, Enter/Exit Animation, Face Transitions

I flipped the Home Message Mode layout from face-LEFT/text-RIGHT to text-LEFT/face-RIGHT.

Text now sits at x=34..298 and slides in from y=-180 to 0 on enter, and back out to y=-180 on exit.

The face now sits at x=480 at scale 0.52 in message mode, and lerps back to the idle center at x=320 at scale 0.86 on exit.

I added a smooth exit animation so message dismiss fades the text upward and returns the face to center before closing, removing the previous hard jump.

I added a proper enter/exit state machine: home_message_enter_active, home_message_exit_active, _start_home_message_enter, _start_home_message_exit, _update_home_message_exit_anim, _finish_home_message_exit.

I added animation helpers: _home_message_text_y_offset, _home_message_text_alpha, _home_message_face_center, _home_message_face_scale.

The auto-dismiss timer only counts elapsed seconds while the message is fully visible, not during enter or exit animation.

I added swipe-to-dismiss in Messages Center. Each row supports left/right swipe with a 60px threshold and abs(dx) > abs(dy) guard so vertical scroll is preserved. State is tracked in messages_swipe_active_id, messages_swipe_start_x, messages_swipe_start_y, messages_swipe_row_index.

I added face movement during screen transitions. The face animates offscreen in the direction of the transition: left for menu open/close, right for clock open/close, down for control center open/close, up for Quick Shelf open/close. The face is not drawn over completed non-Home screens.

I added _home_face_transition_center and _draw_face_home_during_transition so the transition draw path uses the correct animated center without affecting the normal Face Home draw path.

I updated design_tokens.gd with the new text-left/face-right constants, offscreen positions, and new animation timing.

I kept Raspberry Pi 5 2GB performance as top priority: no shaders, no blur, no expensive effects, no fullscreen, Godot Compatibility/OpenGL only.

## 2026-05-27 — Final Home Message Side Correction

I corrected Home Message Mode so the NeXa face stays on the left and all message/notification text appears on the right.

Face now sits at message-mode center Vector2(160, 245) scale 0.52, lerping from idle center Vector2(320, 245).

Text now sits at x=342, width=264 (x=342..606), so it never overlaps the face half.

Close X moved to Rect2(584, 58, 26, 26) to stay inside the right-side text area near the clock/indicator strip.

Action buttons moved to the right side starting at x=342.

I kept the existing enter/exit animation intact. Text still drops in from y=-180 to 0 on enter and exits upward back to y=-180 on exit. The face still moves smoothly from center to the left-side message position on enter and returns smoothly to center on exit.

I kept NeXa Messages swipe dismiss, the 10-second visible timer, the circular close button, and non-intrusive notification indicators unchanged.

## 2026-05-27 — Shorter Home Message Preview Timing

I shortened NeXa Home message preview timing from 10 visible seconds to 4 visible seconds.

The timer still only counts while the message is actually fully visible on Home. It does not count during the enter animation, the exit animation, or while the user is on another screen.

Existing enter/exit animations, close button, notification indicators, swipe dismiss, and reminder/calendar/To Do preview flow stay unchanged.

## 2026-05-27 — Hardware Gateway Server Foundation

I added the safe hardware gateway foundation.

Raspberry Pi receives ESP8266 JSON through a local HTTP endpoint.

The server keeps only the latest state in memory for now.

I added state fields for presence, distance, joystick, BME688 environment data, Wi-Fi RSSI and raw Arduino line.

I added a local network status indicator in the UI.

I added an Environment screen foundation.

I added safe foundations for presence-based Face/Clock behavior and joystick menu navigation.

I did not change Raspberry Pi Wi-Fi or hotspot configuration in this sprint, so internet/SSH is safe.

The future hotspot will be a separate sprint.
