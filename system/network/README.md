This folder contains safe network setup helpers for NeXa ToTem.

The scripts start in dry-run mode and do not change Raspberry Pi networking unless the user runs them with explicit apply flags.

Files and folders:

- `access_point/` contains the older Push Mode / Pi Server Mode access point plan.
- `wifi_switch/` contains the preferred ESP Server Mode switch plan, where Raspberry Pi joins `NeXa-ESP` and pulls from `http://192.168.4.1/api/state`.

Hotspot setup is manual and safety-gated because turning `wlan0` into an access point may disconnect internet/SSH.

Run the hardware gateway for ESP testing:

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

ESP Server Mode switch dry-run:

`python3 scripts/network/connect_to_esp_network.py`

Apply the ESP Wi-Fi switch only when ready:

`python3 scripts/network/connect_to_esp_network.py --apply --i-understand-this-will-disconnect-internet`

Reconnect home Wi-Fi after demo:

`python3 scripts/network/reconnect_home_wifi.py --apply --i-understand-this-changes-network`

Do not put logs, personal Wi-Fi credentials, or secrets in this folder.
