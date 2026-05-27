# NeXa ToTem ESP Server Mode Notes

In the preferred coursework/demo mode, the ESP8266 creates its own Wi-Fi network and hosts a small HTTP server.

Network settings:

- SSID: `NeXa-ESP`
- Password: `nexa12345`
- ESP IP: `192.168.4.1`
- State endpoint: `GET http://192.168.4.1/api/state`

Expected endpoints:

- `GET /` can show a tiny status page.
- `GET /api/state` returns the latest hardware JSON.

Expected JSON shape:

```json
{
  "device": "nexa_totem_esp8266",
  "presence": true,
  "distance_cm": 10,
  "joystick": "CENTER",
  "joystick_x": 517,
  "joystick_y": 503,
  "temperature_c": 28.9,
  "humidity_percent": 41.9,
  "pressure_hpa": 1016.6,
  "gas_kohms": 21.4,
  "air_status": "VENTILATE",
  "wifi_rssi": -45,
  "last_arduino_raw": "presence=1|distance_cm=10|joystick=CENTER|x=517|y=503"
}
```

Raspberry Pi behavior:

1. Save the current Wi-Fi connection.
2. Connect to `NeXa-ESP`.
3. Pull `GET /api/state` every second.
4. Normalize the state through the Pi hardware state store.
5. Reconnect to the saved home Wi-Fi after the demo.

Warning:

The Raspberry Pi will usually lose normal Wi-Fi internet while connected to `NeXa-ESP`, unless it has another internet path. Use the reconnect script after the demo or reconnect manually from the Raspberry Pi network UI.
