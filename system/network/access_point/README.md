This folder contains the safe local access point setup for NeXa ToTem.

It prepares the NeXa-ToTem Wi-Fi network that the ESP8266 can join. The scripts start in dry-run mode and do not change Raspberry Pi networking unless the user runs them with `--apply` and the warning flag.

Files in this folder:

- `ap_profile.py` stores the SSID, local AP IP, hardware server URL, and generated NetworkManager command plan.

The generated commands are a plan. They are not run by this module.

Hotspot setup is manual and safety-gated. If `wlan0` is your current internet route, applying the AP may disconnect internet or SSH.

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
