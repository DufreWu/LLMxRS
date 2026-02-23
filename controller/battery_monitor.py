import time
from typing import Dict
from robot_params import BATTERY

class BatteryMonitor:
    def __init__(self):
        self.capacity_ah = BATTERY["capacity_ah"]
        self.voltage_path = BATTERY["voltage_path"]
        self.current_path = BATTERY["current_path"]
        self.voltage_scale = BATTERY["voltage_scale"]
        self.current_scale = BATTERY["current_scale"]

        self.soc = BATTERY["init_soc"]
        self._last_time = time.time()

    @staticmethod
    def _read_float(path: str, scale: float):
        try:
            with open(path, "r") as f:
                return float(f.read().strip()) / scale
        except Exception:
            return None

    def sample(self) -> Dict:
        v = self._read_float(self.voltage_path, self.voltage_scale)
        i = self._read_float(self.current_path, self.current_scale)

        now = time.time()
        dt = now - self._last_time
        self._last_time = now

        if i is not None:
            self.soc -= (i * dt / 3600.0) / self.capacity_ah
            self.soc = max(0.0, min(1.0, self.soc))

        return {
            "battery_voltage_v": v,
            "battery_current_a": i,
            "battery_power_w": v * i if v and i else None,
            "battery_soc": self.soc,
        }
