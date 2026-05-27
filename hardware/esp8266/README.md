This folder contains the ESP8266 configuration notes for NeXa ToTem.

The ESP8266 will connect to the `NeXa-ToTem` Wi-Fi network and post hardware JSON to the Raspberry Pi at `http://10.42.0.1:8080/api/hardware`.

Files:

- `nexa_totem_esp8266_config_example.h` is a small example config header for the next firmware sprint.

Final ESP8266 firmware will be added later. Do not commit personal home Wi-Fi credentials here.

Run the hardware gateway for ESP testing with:

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
