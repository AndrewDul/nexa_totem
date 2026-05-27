"""Generated access point profile values for NeXa ToTem."""

from __future__ import annotations


NEXA_AP_SSID = "NeXa-ToTem"
NEXA_AP_PASSWORD = "nexa12345"
NEXA_AP_IP = "10.42.0.1"
NEXA_AP_PREFIX = 24
NEXA_HARDWARE_SERVER_PORT = 8080
NEXA_HARDWARE_POST_URL = "http://10.42.0.1:8080/api/hardware"


def build_nmcli_commands(interface: str = "wlan0") -> list[str]:
    iface = interface.strip() or "wlan0"
    return [
        f"nmcli connection add type wifi ifname {iface} con-name {NEXA_AP_SSID} autoconnect yes ssid {NEXA_AP_SSID}",
        f"nmcli connection modify {NEXA_AP_SSID} 802-11-wireless.mode ap",
        f"nmcli connection modify {NEXA_AP_SSID} 802-11-wireless.band bg",
        f"nmcli connection modify {NEXA_AP_SSID} ipv4.method shared",
        f"nmcli connection modify {NEXA_AP_SSID} ipv4.addresses {NEXA_AP_IP}/{NEXA_AP_PREFIX}",
        f"nmcli connection modify {NEXA_AP_SSID} wifi-sec.key-mgmt wpa-psk",
        f"nmcli connection modify {NEXA_AP_SSID} wifi-sec.psk {NEXA_AP_PASSWORD}",
        f"nmcli connection up {NEXA_AP_SSID}",
    ]


def build_server_command(host: str = "0.0.0.0", port: int = NEXA_HARDWARE_SERVER_PORT) -> str:
    return f"python3 scripts/run/run_hardware_gateway_dev.py --host {host} --port {int(port)}"


def esp_config_summary() -> str:
    return "\n".join([
        f"SSID: {NEXA_AP_SSID}",
        f"Password: {NEXA_AP_PASSWORD}",
        f"Raspberry Pi AP IP: {NEXA_AP_IP}",
        f"Hardware server port: {NEXA_HARDWARE_SERVER_PORT}",
        f"ESP8266 POST URL: {NEXA_HARDWARE_POST_URL}",
    ])
