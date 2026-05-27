This folder contains the safe Wi-Fi switch plan for ESP Server Mode.

ESP Server Mode means the ESP8266 creates the `NeXa-ESP` Wi-Fi network and the Raspberry Pi connects to it as a client. The Pi can then pull hardware state from `http://192.168.4.1/api/state`.

The scripts start in dry-run mode. They do not change Raspberry Pi networking unless the user runs them with explicit apply flags.

Files:

- `wifi_switch_plan.py` stores the ESP Wi-Fi details, previous Wi-Fi save path, and planned NetworkManager commands.

Switching to `NeXa-ESP` can disconnect normal internet or SSH while NeXa is running. The reconnect script can return to the saved home Wi-Fi after the demo.

Use the full ESP mode launcher when you want NeXa to switch Wi-Fi, start pull mode, and reconnect on exit:

`CONFIRM_NEXA_ESP_WIFI_SWITCH=RUN bash scripts/run/run_nexa_totem_esp_mode.sh`

This intentionally disconnects normal Wi-Fi/internet while NeXa runs. It should reconnect to the saved previous Wi-Fi on exit.

Use the normal development launcher when you do not want Wi-Fi switching:

`bash scripts/run/run_godot_ui_with_api_dev.sh`

Do not put personal Wi-Fi credentials, logs, or secrets in this folder.
