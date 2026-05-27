"""Wi-Fi switch plan for ESP Server Mode."""

from __future__ import annotations


NEXA_ESP_SSID = "NeXa-ESP"
NEXA_ESP_PASSWORD = "nexa12345"
NEXA_ESP_IP = "192.168.4.1"
NEXA_ESP_STATE_URL = "http://192.168.4.1/api/state"
PREVIOUS_WIFI_CONNECTION_PATH = "var/data/network/previous_wifi_connection.json"


def build_connect_commands(interface: str = "wlan0") -> list[str]:
    iface = interface.strip() or "wlan0"
    return [
        f"nmcli connection add type wifi ifname {iface} con-name {NEXA_ESP_SSID} ssid {NEXA_ESP_SSID}",
        f"nmcli connection modify {NEXA_ESP_SSID} wifi-sec.key-mgmt wpa-psk",
        f"nmcli connection modify {NEXA_ESP_SSID} wifi-sec.psk {NEXA_ESP_PASSWORD}",
        f"nmcli connection up {NEXA_ESP_SSID}",
    ]


def build_reconnect_commands(previous_connection_name: str | None = None, delete_esp_profile: bool = False) -> list[str]:
    commands = [f"nmcli connection down {NEXA_ESP_SSID}"]
    if previous_connection_name:
        commands.append(f"nmcli connection up {previous_connection_name}")
    if delete_esp_profile:
        commands.append(f"nmcli connection delete {NEXA_ESP_SSID}")
    return commands


def mode_summary() -> dict[str, str]:
    return {
        "hardware_mode": "pull_esp_server",
        "ssid": NEXA_ESP_SSID,
        "password": NEXA_ESP_PASSWORD,
        "esp_ip": NEXA_ESP_IP,
        "state_url": NEXA_ESP_STATE_URL,
        "previous_wifi_connection_path": PREVIOUS_WIFI_CONNECTION_PATH,
    }
