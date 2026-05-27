# Troubleshooting

## Godot Drawing Helper Runtime Errors

Godot helper calls failed because drawing helpers were not callable at runtime from the theme script.

Fixed by using local callable drawing helpers in `main.gd`.

`Rect2.translated()` was not available in this Godot runtime.

Use `Rect2(rect.position + offset, rect.size)` instead.

Repeated script errors can cause visible lag, so runtime logs must be clean before judging performance.

## Godot crashes on Raspberry Pi with Vulkan/Mobile renderer

Problem:
Godot crashed after opening Control Center with:

`MESA: error: Failed to allocate device memory for BO`

`MESA: error: failed to allocate memory for command list`

`handle_crash: Program crashed with signal 11`

`libvulkan_broadcom.so`

Cause:
The Raspberry Pi 5 2GB Vulkan/Mobile path can run out of GPU memory for this UI.

Fix:
Run Godot in Compatibility/OpenGL mode:

`--rendering-driver opengl3`

Also set `project.godot`:

`renderer/rendering_method="gl_compatibility"`

`renderer/rendering_method.mobile="gl_compatibility"`

Control Center should use safe lightweight drawing.

The X11 OpenGL context warning can appear before Godot falls back to OpenGL ES Compatibility.

This is acceptable when the app continues with OpenGL ES Compatibility and does not crash.

## Godot OpenGL ES compatibility warning on Raspberry Pi

Problem:
When launching the Godot UI on Raspberry Pi, the terminal may show:

`ERROR: Condition "ctxErrorOccurred || !gl_display.context->glx_context" is true. Returning: ERR_UNCONFIGURED`

and then:

`WARNING: Your video card drivers seem not to support the required OpenGL version, switching to OpenGLES.`

This is acceptable when Godot continues and shows:

`OpenGL API OpenGL ES ... Compatibility`

Cause:
Godot first tries an OpenGL context path that may not work on the Raspberry Pi desktop session, then falls back to OpenGL ES Compatibility.

Fix / current rule:
This warning is not a failure if the app continues in OpenGL ES Compatibility and does not crash.

Do not treat this as a failed smoke test unless it is followed by a crash, SCRIPT ERROR, Vulkan/Mobile renderer path, or MESA memory allocation failure.


## Camera preview lifecycle

Problem:
Camera preview can waste memory or keep the camera locked if it stays active after the user leaves the Camera tab.

Current fix:
Camera preview is off by default. It starts only when the user toggles Preview On.

Preview must stop when:
- the user toggles Preview Off
- the user leaves the Camera tab
- the user leaves Diagnostics
- the Godot UI stops requesting preview frames for longer than the stale timeout

The preview backend should use one persistent live worker/session while enabled, not repeated still-image process launches.

## NeXa-ToTem AP disconnects Wi-Fi or SSH

Problem:
After applying the NeXa-ToTem access point profile, the Raspberry Pi may lose normal Wi-Fi internet or SSH.

Cause:
If `wlan0` was the current internet route, turning it into the NeXa-ToTem access point can disconnect the old Wi-Fi connection.

Fix:
Use a local monitor/keyboard, Ethernet, USB tethering, or a second Wi-Fi adapter, then run:

`python3 scripts/network/rollback_nexa_ap.py --apply --i-understand-this-changes-network`

Safety rule:
Do not apply AP mode while relying on `wlan0` SSH unless you know what you are doing.

Prefer Ethernet, USB tethering, or a second Wi-Fi adapter for internet while `wlan0` is used as the NeXa-ToTem AP.

## ESP Server Mode disconnects internet

Problem:
In ESP Server Mode, the Raspberry Pi connects to `NeXa-ESP` so it can pull hardware state from `http://192.168.4.1/api/state`.

Cause:
The Pi usually has one built-in Wi-Fi adapter. While that adapter is connected to `NeXa-ESP`, it is not connected to normal home Wi-Fi.

Fix after demo:
Run:

`python3 scripts/network/reconnect_home_wifi.py --apply --i-understand-this-changes-network`

If reconnect fails:
Use the Raspberry Pi network UI or terminal to reconnect your normal home Wi-Fi manually.

Safety rule:
Dry-run first with:

`python3 scripts/network/connect_to_esp_network.py`

Only apply the ESP Wi-Fi switch when you are ready for internet/SSH to disconnect during the demo.

## ESP mode launcher is missing

Problem:
`bash scripts/run/run_nexa_totem_esp_mode.sh` does not exist.

Fix:
Update from the sprint that added the ESP mode launcher.

Start ESP mode with:

`CONFIRM_NEXA_ESP_WIFI_SWITCH=RUN bash scripts/run/run_nexa_totem_esp_mode.sh`

This intentionally disconnects normal Wi-Fi/internet while NeXa runs.

## ESP mode does not reconnect home Wi-Fi

Problem:
NeXa ESP mode closed, but the Raspberry Pi did not reconnect to home Wi-Fi.

Fix:
Run:

`python3 scripts/network/reconnect_home_wifi.py --apply --i-understand-this-changes-network`

If it still does not connect:
Use the Raspberry Pi network menu or terminal to reconnect your normal home Wi-Fi manually.
