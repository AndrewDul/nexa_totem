This folder contains safe network setup helpers for NeXa ToTem.

The current work prepares a local NeXa-ToTem Wi-Fi access point that the ESP8266 can join. The scripts start in dry-run mode and do not change Raspberry Pi networking unless the user runs them with explicit apply flags.

Files and folders:

- `access_point/` contains the generated access point profile and command plan.

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

Do not put logs, personal Wi-Fi credentials, or secrets in this folder.
