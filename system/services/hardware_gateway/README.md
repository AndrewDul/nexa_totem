This folder contains the small local hardware gateway used by NeXa ToTem.

It receives JSON from the ESP8266, keeps the latest sensor state in memory, and gives the Godot UI a simple state endpoint. It does not configure Wi-Fi and it does not store Wi-Fi passwords.

Files in this folder:

- `hardware_models.py` normalizes raw ESP8266 and Arduino values.
- `hardware_state.py` keeps the latest hardware state in memory.
- `__init__.py` exposes the shared `latest_hardware_state` store.

The ESP8266 can post JSON to:

- `POST /api/hardware`

The UI can read the latest state from:

- `GET /api/hardware/state`

The test dashboard is available at:

- `GET /hardware-dashboard`

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
