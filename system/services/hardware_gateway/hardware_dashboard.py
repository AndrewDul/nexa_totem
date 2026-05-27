"""Simple HTML dashboard for the hardware gateway."""

from __future__ import annotations

import html
import json
from typing import Any


def _value(state: dict[str, Any], key: str, suffix: str = "") -> str:
    value = state.get(key)
    if value is None or value == "":
        return "Waiting"
    return html.escape(str(value)) + suffix


def render_dashboard(state: dict[str, Any]) -> str:
    status = "Connected" if bool(state.get("connected", False)) and not bool(state.get("stale", True)) else "Disconnected"
    status_class = "ok" if status == "Connected" else "bad"
    raw_json = html.escape(json.dumps(state, indent=2, sort_keys=True))
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>NeXa ToTem Hardware Dashboard</title>
  <style>
    body {{ background: #08090d; color: #eef2f7; font-family: system-ui, sans-serif; margin: 32px; }}
    h1 {{ font-size: 24px; margin: 0 0 18px; }}
    .status {{ color: #0f1720; display: inline-block; border-radius: 18px; padding: 6px 12px; font-weight: 700; }}
    .ok {{ background: #58d68d; }}
    .bad {{ background: #f06a6a; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin-top: 20px; }}
    .card {{ background: #11151d; border: 1px solid #263041; border-radius: 8px; padding: 14px; }}
    .label {{ color: #93a0b2; font-size: 12px; }}
    .value {{ font-size: 19px; margin-top: 4px; }}
    pre {{ background: #11151d; border: 1px solid #263041; border-radius: 8px; padding: 14px; overflow: auto; }}
  </style>
</head>
<body>
  <h1>NeXa ToTem Hardware Dashboard</h1>
  <p>Environment, Presence, and joystick state from the ESP8266 gateway.</p>
  <div class="status {status_class}">Local network status: {status}</div>
  <div class="grid">
    <div class="card"><div class="label">Last seen</div><div class="value">{_value(state, "last_seen_at")}</div></div>
    <div class="card"><div class="label">Presence</div><div class="value">{html.escape(str(state.get("presence", False)))}</div></div>
    <div class="card"><div class="label">Distance</div><div class="value">{_value(state, "distance_cm", " cm")}</div></div>
    <div class="card"><div class="label">Joystick</div><div class="value">{_value(state, "joystick")}</div></div>
    <div class="card"><div class="label">Temperature</div><div class="value">{_value(state, "temperature_c", " C")}</div></div>
    <div class="card"><div class="label">Humidity</div><div class="value">{_value(state, "humidity_percent", "%")}</div></div>
    <div class="card"><div class="label">Pressure</div><div class="value">{_value(state, "pressure_hpa", " hPa")}</div></div>
    <div class="card"><div class="label">Gas</div><div class="value">{_value(state, "gas_kohms", " kOhm")}</div></div>
    <div class="card"><div class="label">Air status</div><div class="value">{_value(state, "air_status")}</div></div>
    <div class="card"><div class="label">Advice</div><div class="value">{_value(state, "advice")}</div></div>
  </div>
  <h2>Raw JSON</h2>
  <pre>{raw_json}</pre>
</body>
</html>"""
