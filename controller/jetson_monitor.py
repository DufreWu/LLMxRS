import os
import psutil
from typing import Dict
from robot_params import JETSON


class JetsonMonitor:
    """
    Jetson Orin NX compute & power monitor
    -------------------------------------
    Collects:
      - CPU usage & average frequency
      - GPU utilization & frequency
      - Memory usage
      - Power rails via INA3221

    All parameters are defined in controller/params.py
    """

    def __init__(self):
        self.cpu_count = psutil.cpu_count()
        self.ina_base = JETSON["ina_base"]

    # ============================================================
    # Utility
    # ============================================================
    @staticmethod
    def _read_float(path: str, scale: float = 1.0):
        try:
            with open(path, "r") as f:
                return float(f.read().strip()) / scale
        except Exception:
            return None

    # ============================================================
    # CPU
    # ============================================================
    def get_cpu(self) -> Dict:
        usage = psutil.cpu_percent(interval=None)

        freqs = []
        for i in range(self.cpu_count):
            f = self._read_float(
                f"/sys/devices/system/cpu/cpu{i}/cpufreq/scaling_cur_freq",
                scale=JETSON["cpu_freq_scale"],  # kHz → MHz
            )
            if f is not None:
                freqs.append(f)

        return {
            "usage": usage,
            "freq_avg_mhz": sum(freqs) / len(freqs) if freqs else None,
            "freq_list_mhz": freqs,
        }

    # ============================================================
    # GPU (GA10B, Orin NX)
    # ============================================================
    def get_gpu(self) -> Dict:
        util = self._read_float(
            JETSON["gpu_load_path"],
            scale=JETSON["gpu_load_scale"],
        )

        freq = self._read_float(
            JETSON["gpu_freq_path"],
            scale=JETSON["gpu_freq_scale"],  # Hz → MHz
        )

        return {
            "util": util,
            "freq_mhz": freq,
        }

    # ============================================================
    # Memory
    # ============================================================
    @staticmethod
    def get_memory() -> Dict:
        mem = psutil.virtual_memory()
        return {
            "used_mb": mem.used / 1024 / 1024,
            "percent": mem.percent,
        }

    # ============================================================
    # Power (INA3221)
    # ============================================================
    def get_power(self) -> Dict:
        """
        Typical Orin NX mapping:
          in_power0 → CPU
          in_power1 → GPU
          in_power2 → SOC
        """
        rails = {}

        for root, _, files in os.walk(self.ina_base):
            for f in files:
                if f.endswith("_power_input"):
                    try:
                        with open(os.path.join(root, f)) as fp:
                            name = f.replace("_power_input", "")
                            rails[name] = int(fp.read().strip()) / 1000.0  # mW
                    except Exception:
                        pass

        return {
            "cpu_mw": rails.get("in_power0"),
            "gpu_mw": rails.get("in_power1"),
            "soc_mw": rails.get("in_power2"),
        }

    # ============================================================
    # Unified snapshot (controller-facing)
    # ============================================================
    def sample(self) -> Dict:
        cpu = self.get_cpu()
        gpu = self.get_gpu()
        mem = self.get_memory()
        pwr = self.get_power()

        return {
            # CPU
            "cpu_usage": cpu["usage"],
            "cpu_freq_mhz": cpu["freq_avg_mhz"],

            # GPU
            "gpu_util": gpu["util"],
            "gpu_freq_mhz": gpu["freq_mhz"],

            # Memory
            "mem_used_mb": mem["used_mb"],
            "mem_percent": mem["percent"],

            # Power
            "power_cpu_mw": pwr["cpu_mw"],
            "power_gpu_mw": pwr["gpu_mw"],
            "power_soc_mw": pwr["soc_mw"],
        }
