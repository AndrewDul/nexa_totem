This folder contains the ESP8266 configuration notes for NeXa ToTem.

The preferred coursework/demo mode is ESP Server Mode.

In ESP Server Mode, the ESP8266 creates the `NeXa-ESP` Wi-Fi network and hosts hardware state at `http://192.168.4.1/api/state`. The Raspberry Pi connects to `NeXa-ESP` and pulls the latest state.

Files:

- `nexa_totem_esp8266_config_example.h` is a small example config header for ESP Server Mode.
- `nexa_totem_esp_server_mode_notes.md` explains the expected ESP network, endpoints, and JSON.

Final ESP8266 firmware will be added later. Do not commit personal home Wi-Fi credentials here.

ESP final behavior:

- Create Wi-Fi SoftAP `NeXa-ESP`
- Use password `nexa12345`
- Use IP `192.168.4.1`
- Host `GET /`
- Host `GET /api/state`
- Read Arduino serial and BME688 values
- Return combined JSON for the Raspberry Pi to pull

Distance convention:

- `distance_cm = -1` means no valid ultrasonic echo.
- `distance_cm > 0` means a valid object/person distance was measured.
- The Raspberry Pi UI uses a short stable delay so one bad `-1` reading does not flicker between Face and Clock.

Run a safe Pi pull test with:

`python3 scripts/run/run_esp_pull_client_dev.py --once --json`

The older Push Mode / Pi Server Mode is still available for fallback and development. In that mode, run:

`python3 scripts/run/run_hardware_gateway_dev.py --host 0.0.0.0 --port 8080`

Dry-run AP setup:

`python3 scripts/network/setup_nexa_ap.py`

Check safety:

`python3 scripts/network/check_network_safety.py`

Apply later:

`python3 scripts/network/setup_nexa_ap.py --apply --interface wlan0 --i-understand-this-may-disconnect-wifi`

If `wlan0` is the internet route, also add:

`--force-wlan0-ap`

Rollback:

`python3 scripts/network/rollback_nexa_ap.py --apply --i-understand-this-changes-network`

For ESP Server Mode Wi-Fi switching, dry-run first:

`python3 scripts/network/connect_to_esp_network.py`

Apply only when ready:

`python3 scripts/network/connect_to_esp_network.py --apply --i-understand-this-will-disconnect-internet`

Start the full NeXa ESP mode launcher with:

`CONFIRM_NEXA_ESP_WIFI_SWITCH=RUN bash scripts/run/run_nexa_totem_esp_mode.sh`

This intentionally disconnects normal Wi-Fi/internet while NeXa runs. The launcher should reconnect to home Wi-Fi on exit.

The launcher uses `NEXA_ESP_POLL_INTERVAL_SECONDS=0.2` for better joystick and ultrasonic responsiveness.

Use the normal development launcher when you do not want Wi-Fi switching:

`bash scripts/run/run_godot_ui_with_api_dev.sh`

Reconnect home Wi-Fi after the demo:

`python3 scripts/network/reconnect_home_wifi.py --apply --i-understand-this-changes-network`
