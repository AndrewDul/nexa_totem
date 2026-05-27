This folder contains the small local hardware gateway used by NeXa ToTem.

It keeps the latest hardware state in memory and gives the Godot UI a simple state endpoint. It does not configure Wi-Fi and it does not store Wi-Fi passwords.

There are two hardware modes:

- ESP Server Mode / Pull Mode: ESP8266 creates `NeXa-ESP`, hosts `GET /api/state`, and Raspberry Pi pulls from `http://192.168.4.1/api/state`. This is the preferred coursework/demo mode.
- Push Mode / Pi Server Mode: ESP8266 posts JSON to the Raspberry Pi server. This is kept as fallback, debug, and development mode.

Files in this folder:

- `hardware_models.py` normalizes raw ESP8266 and Arduino values.
- `hardware_state.py` keeps the latest hardware state in memory.
- `esp_pull_client.py` pulls hardware JSON from the ESP8266 server.
- `__init__.py` exposes the shared `latest_hardware_state` store.

The ESP8266 can post JSON to:

- `POST /api/hardware`

The UI can read the latest state from:

- `GET /api/hardware/state`

The test dashboard is available at:

- `GET /hardware-dashboard`

The ESP pull client reads:

- `GET http://192.168.4.1/api/state`

Hardware state includes derived presence fields:

- `distance_valid` is true only when `distance_cm` is greater than zero.
- `presence_detected` is true when distance is greater than zero, or when distance is missing and the fallback presence flag is true.
- `presence_source` explains whether the value came from distance, the presence flag, or neither.

In the current ESP/Arduino convention, `distance_cm = -1` means no valid echo.

Safe pull test:

`python3 scripts/run/run_esp_pull_client_dev.py --once --json`

Full ESP mode launcher:

`CONFIRM_NEXA_ESP_WIFI_SWITCH=RUN bash scripts/run/run_nexa_totem_esp_mode.sh`

This intentionally disconnects normal Wi-Fi/internet while NeXa runs. It starts NeXa with `NEXA_HARDWARE_MODE=pull_esp_server` and should reconnect home Wi-Fi on exit.

The ESP mode launcher sets `NEXA_ESP_POLL_INTERVAL_SECONDS=0.2` so joystick and distance updates feel responsive.

Use the normal development launcher when you do not want Wi-Fi switching:

`bash scripts/run/run_godot_ui_with_api_dev.sh`

"Connected" means NeXa has received recent ESP8266 hardware data. It does not mean the internet is connected.

"Stale" means the newest hardware data is older than the configured stale timeout. The development default is 5 seconds.

Safe local development run:

`python3 scripts/run/run_hardware_gateway_dev.py`

Expose it on the LAN only when testing with the ESP8266:

`python3 scripts/run/run_hardware_gateway_dev.py --host 0.0.0.0 --port 8080`

You can also use:

`bash scripts/run/run_hardware_gateway_lan_dev.sh`

Dry-run the NeXa-ToTem AP setup:

`python3 scripts/network/setup_nexa_ap.py`

Check network safety before applying:

`python3 scripts/network/check_network_safety.py`

Apply the AP later:

`python3 scripts/network/setup_nexa_ap.py --apply --interface wlan0 --i-understand-this-may-disconnect-wifi`

If `wlan0` is the internet route, also add:

`--force-wlan0-ap`

Rollback:

`python3 scripts/network/rollback_nexa_ap.py --apply --i-understand-this-changes-network`

This server does not configure Wi-Fi. Hotspot setup is separate and safety-gated.

Do not put logs, config files, Wi-Fi passwords, or secrets in this folder.
