"""
vec2lang.py

Semantic mapping module:
Numerical state vector → structured language representation
(value + normalized ratio + linguistic descriptor)

Platform-specific bounds are loaded from YAML config.
"""

from typing import Dict, Any
import yaml


# ============================================================
# Platform Config Loader
# ============================================================

class PlatformConfig:

    def __init__(self, yaml_path: str):
        with open(yaml_path, "r") as f:
            self.data = yaml.safe_load(f)

    # ------------------------
    # Motion
    # ------------------------
    @property
    def max_speed(self):
        return self.data["motion"]["speed"]["max"]

    # ------------------------
    # CPU
    # ------------------------
    @property
    def cpu_freq_max(self):
        return self.data["cpu"]["freq_max"]

    @property
    def cpu_freq_min(self):
        return self.data["cpu"]["freq_min"]

    @property
    def cpu_util_thresholds(self):
        return self.data["cpu"]["utilization_thresholds"]

    # ------------------------
    # GPU
    # ------------------------
    @property
    def gpu_freq_max(self):
        return self.data["gpu"]["freq_max"]

    @property
    def gpu_freq_min(self):
        return self.data["gpu"]["freq_min"]

    @property
    def gpu_util_thresholds(self):
        return self.data["gpu"]["utilization_thresholds"]

    # ------------------------
    # Thermal
    # ------------------------
    @property
    def thermal_cfg(self):
        return self.data["thermal"]

    # ------------------------
    # Battery
    # ------------------------
    @property
    def battery_soc_thresholds(self):
        return self.data["battery"]["soc"]

    # ------------------------
    # Risk
    # ------------------------
    @property
    def risk_rules(self):
        return self.data["risk_rules"]


# ============================================================
# Vec2Lang
# ============================================================

class Vec2Lang:

    def __init__(self, config: PlatformConfig):
        self.cfg = config

    # --------------------------------------------------------
    # Utilities
    # --------------------------------------------------------

    @staticmethod
    def normalize(value: float, max_value: float):
        if max_value <= 0:
            return 0.0
        return round(value / max_value, 3)

    # --------------------------------------------------------
    # Temperature
    # --------------------------------------------------------

    def map_temperature(self, T: float):
        thermal = self.cfg.thermal_cfg
        ratio = self.normalize(T, thermal["limit"])

        if T < thermal["warning"]:
            label = "normal"
        elif T < thermal["high"]:
            label = "elevated"
        elif T < thermal["critical"]:
            label = "high"
        else:
            label = "critical"

        return {"value": f"{T}°C", "ratio": ratio, "label": label}

    # --------------------------------------------------------
    # SOC
    # --------------------------------------------------------

    def map_soc(self, soc: float):
        thresholds = self.cfg.battery_soc_thresholds
        ratio = round(soc / 100.0, 3)

        if soc >= thresholds["high"]:
            label = "high charge"
        elif soc >= thresholds["moderate"]:
            label = "moderate charge"
        elif soc >= thresholds["low"]:
            label = "low charge"
        else:
            label = "critical"

        return {"value": f"{soc}%", "ratio": ratio, "label": label}

    # --------------------------------------------------------
    # Utilization
    # --------------------------------------------------------

    def map_util(self, util: float, thresholds: Dict[str, float]):
        ratio = round(util / 100.0, 3)

        if util < thresholds["under_utilized"]:
            label = "under-utilized"
        elif util < thresholds["balanced"]:
            label = "balanced"
        elif util < thresholds["high"]:
            label = "high load"
        else:
            label = "saturated"

        return {"value": f"{util}%", "ratio": ratio, "label": label}

    # --------------------------------------------------------
    # Frequency
    # --------------------------------------------------------

    def map_freq(self, freq: float, max_freq: float):
        ratio = self.normalize(freq, max_freq)

        if ratio < 0.4:
            label = "low"
        elif ratio < 0.7:
            label = "moderate"
        elif ratio < 0.9:
            label = "high"
        else:
            label = "maximum"

        return {"value": f"{freq} GHz", "ratio": ratio, "label": label}

    # --------------------------------------------------------
    # Speed
    # --------------------------------------------------------

    def map_speed(self, speed: float):
        ratio = self.normalize(speed, self.cfg.max_speed)

        if ratio < 0.4:
            label = "conservative"
        elif ratio < 0.7:
            label = "balanced"
        elif ratio < 0.9:
            label = "aggressive"
        else:
            label = "maximum"

        return {"value": f"{speed} m/s", "ratio": ratio, "label": label}

    # --------------------------------------------------------
    # Risk Assessment
    # --------------------------------------------------------

    def assess_risk(self, temp, cpu_freq, soc, speed):
        rules = self.cfg.risk_rules
        risks = []

        if temp["label"] in ["high", "critical"] and cpu_freq["ratio"] > rules["thermal_cpu_ratio"]:
            risks.append("thermal stress risk")

        if soc["ratio"] < rules["low_soc_ratio"] and speed["ratio"] > rules["energy_speed_ratio"]:
            risks.append("energy-aggressive behavior")

        return risks

    # --------------------------------------------------------
    # Full Conversion
    # --------------------------------------------------------

    def convert(self, state: Dict[str, Any]):

        temp = self.map_temperature(state["temperature"])
        soc = self.map_soc(state["soc"])
        cpu_util = self.map_util(state["cpu_util"], self.cfg.cpu_util_thresholds)
        gpu_util = self.map_util(state["gpu_util"], self.cfg.gpu_util_thresholds)
        speed = self.map_speed(state["speed"])
        cpu_freq = self.map_freq(state["cpu_freq"], self.cfg.cpu_freq_max)
        gpu_freq = self.map_freq(state["gpu_freq"], self.cfg.gpu_freq_max)

        risks = self.assess_risk(temp, cpu_freq, soc, speed)

        return {
            "environment": {
                "terrain": state["terrain"],
                "slope": state["slope"],
                "temperature": temp
            },
            "robot_state": {
                "battery_soc": soc,
                "cpu_utilization": cpu_util,
                "gpu_utilization": gpu_util
            },
            "configuration": {
                "speed": speed,
                "cpu_frequency": cpu_freq,
                "gpu_frequency": gpu_freq
            },
            "assessment": risks
        }
