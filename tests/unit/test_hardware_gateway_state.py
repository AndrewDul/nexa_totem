import time
import unittest

from system.services.hardware_gateway.hardware_state import HardwareStateStore, parse_arduino_raw_line


SAMPLE = {
    "device": "nexa_totem_esp8266",
    "presence": 1,
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
    "last_arduino_raw": "presence=1|distance_cm=10|joystick=CENTER|x=517|y=503",
}


class HardwareGatewayStateTests(unittest.TestCase):
    def test_empty_state_is_disconnected_and_stale(self):
        state = HardwareStateStore().as_dict()
        self.assertFalse(state["connected"])
        self.assertTrue(state["stale"])
        self.assertEqual(state["advice"], "Waiting for live data")

    def test_valid_esp_json_updates_connected_state(self):
        state = HardwareStateStore().update(SAMPLE)
        self.assertTrue(state["connected"])
        self.assertFalse(state["stale"])
        self.assertEqual(state["device"], "nexa_totem_esp8266")
        self.assertEqual(state["distance_cm"], 10.0)

    def test_stale_state_becomes_disconnected(self):
        store = HardwareStateStore(stale_after_seconds=0.01)
        store.update(SAMPLE)
        time.sleep(0.02)
        state = store.as_dict()
        self.assertFalse(state["connected"])
        self.assertTrue(state["stale"])

    def test_joystick_normalization(self):
        store = HardwareStateStore()
        self.assertEqual(store.update({"joystick": "left"})["joystick"], "LEFT")
        self.assertEqual(store.update({"joystick": "bad"})["joystick"], "UNKNOWN")

    def test_presence_normalization(self):
        store = HardwareStateStore()
        self.assertTrue(store.update({"presence": "1"})["presence"])
        self.assertFalse(store.update({"presence": "false"})["presence"])

    def test_bme688_values_normalized(self):
        state = HardwareStateStore().update(SAMPLE)
        self.assertEqual(state["temperature_c"], 28.9)
        self.assertEqual(state["humidity_percent"], 41.9)
        self.assertEqual(state["pressure_hpa"], 1016.6)
        self.assertEqual(state["gas_kohms"], 21.4)

    def test_air_status_advice(self):
        store = HardwareStateStore()
        self.assertEqual(store.update({"air_status": "OK"})["advice"], "Air looks okay")
        self.assertEqual(store.update({"air_status": "VENTILATE"})["advice"], "Open the window")

    def test_partial_data_does_not_crash(self):
        state = HardwareStateStore().update({"presence": "bad", "temperature_c": "bad"})
        self.assertFalse(state["presence"])
        self.assertIsNone(state["temperature_c"])
        self.assertEqual(state["joystick"], "UNKNOWN")

    def test_parse_arduino_raw_line(self):
        parsed = parse_arduino_raw_line("presence=1|distance_cm=10|joystick=CENTER|x=517|y=503")
        self.assertEqual(parsed, {
            "presence": True,
            "distance_cm": 10.0,
            "joystick": "CENTER",
            "joystick_x": 517,
            "joystick_y": 503,
        })

    def test_distance_minus_one_is_no_valid_presence(self):
        state = HardwareStateStore().update({"distance_cm": -1, "presence": True})
        self.assertEqual(state["distance_cm"], -1.0)
        self.assertFalse(state["distance_valid"])
        self.assertFalse(state["presence_detected"])
        self.assertEqual(state["presence_source"], "distance")

    def test_positive_distance_is_presence(self):
        state = HardwareStateStore().update({"distance_cm": 10, "presence": False})
        self.assertTrue(state["distance_valid"])
        self.assertTrue(state["presence_detected"])
        self.assertEqual(state["presence_source"], "distance")

    def test_missing_distance_uses_presence_fallback(self):
        store = HardwareStateStore()
        present = store.update({"presence": True})
        absent = store.update({"presence": False})
        self.assertFalse(present["distance_valid"])
        self.assertTrue(present["presence_detected"])
        self.assertEqual(present["presence_source"], "presence_flag")
        self.assertFalse(absent["presence_detected"])
        self.assertEqual(absent["presence_source"], "presence_flag")


if __name__ == "__main__":
    unittest.main()
