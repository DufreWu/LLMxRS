import os
import psutil
from typing import Dict
import yaml


# ============================================================
# Load YAML config
# ============================================================
def load_config():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_dir, "config.yaml")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


# ============================================================
# Jetson Monitor
# ============================================================
class JetsonMonitor:

    def __init__(self, config):
        self.config = config
        self.jetson = config["jetson"]

        self.cpu_count = psutil.cpu_count()
        self.ina_base = self.jetson["ina_base"]

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
                scale=self.jetson["cpu_freq_scale"],
            )
            if f is not None:
                freqs.append(f)

        return {
            "usage": usage,
            "freq_avg_mhz": sum(freqs) / len(freqs) if freqs else None,
        }

    # ============================================================
    # GPU
    # ============================================================
    def get_gpu(self) -> Dict:

        freq = self._read_float(
            self.jetson["gpu_freq_path"],
            scale=self.jetson["gpu_freq_scale"],
        )

        temp = self._read_float(
            self.jetson["gpu_temp_path"],
            scale=self.jetson["gpu_temp_scale"],
        )

        return {
            "freq_mhz": freq,
            "temp_c": temp,
        }

# ============================================================
    # Power (Direct INA3221 Calculation)
    # ============================================================
    def _read_power_channel(self, idx: int) -> float:
        """Calculates power by reading Voltage and Current sensors."""
        # Voltage (inX_input is mV)
        v_path = os.path.join(self.ina_base, f"in{idx}_input")
        # Current (currX_input is mA)
        i_path = os.path.join(self.ina_base, f"curr{idx}_input")

        v = self._read_float(v_path, scale=1000.0)  # mV -> V
        i = self._read_float(i_path, scale=1000.0)  # mA -> A

        if v is not None and i is not None:
            return v * i * 1000.0  # Returns mW
        return 0.0

    def get_power(self) -> Dict:
        # Orin NX INA3221 Channel Mapping:
        # 1: VDD_IN (Total)
        # 2: VDD_CPU_GPU_CV (Compute)
        # 3: VDD_SOC
        return {
            "power_total_mw": self._read_power_channel(1),
            "power_compute_mw": self._read_power_channel(2),
            "power_soc_mw": self._read_power_channel(3),
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
    # Unified Snapshot
    # ============================================================
    def sample(self) -> Dict:

        cpu = self.get_cpu()
        gpu = self.get_gpu()
        mem = self.get_memory()
        pwr = self.get_power()

        return {
            "cpu_usage": cpu["usage"],
            "cpu_freq_mhz": cpu["freq_avg_mhz"],

            "gpu_freq_mhz": gpu["freq_mhz"],
            "gpu_temp_c": gpu["temp_c"],

            "mem_used_mb": mem["used_mb"],
            "mem_percent": mem["percent"],

            "power_total_mw": pwr["power_total_mw"],
            "power_compute_mw": pwr["power_compute_mw"],
            "power_soc_mw": pwr["power_soc_mw"],
        }


# ============================================================
# Standalone Test
# ============================================================
if __name__ == "__main__":

    import time

    def safe(v, fmt="{:.1f}"):
        return fmt.format(v) if v is not None else "N/A"

    config = load_config()
    monitor = JetsonMonitor(config)

    print("=" * 60)
    print("Jetson Orin NX Monitor Test")
    print("Press Ctrl+C to stop\n")

    try:
        while True:
            data = monitor.sample()
            total_power = data["power_total_mw"]

            print("-" * 60)
            print(f"CPU : {safe(data['cpu_usage'], '{:6.1f}')}% | "
                  f"{safe(data['cpu_freq_mhz'], '{:8.1f}')} MHz")

            print(f"GPU : {safe(data['gpu_freq_mhz'], '{:8.1f}')} MHz | "
                  f"{safe(data['gpu_temp_c'], '{:6.1f}')} °C")

            print(f"MEM : {safe(data['mem_percent'], '{:6.1f}')}% | "
                  f"{safe(data['mem_used_mb'], '{:8.1f}')} MB")

            print(f"Power: Total {safe(total_power, '{:8.1f}')} mW | "
                  f"Compute {safe(data['power_compute_mw'], '{:8.1f}')} mW | "
                  f"SOC {safe(data['power_soc_mw'], '{:8.1f}')} mW")

            time.sleep(config["controller"]["sample_period_s"])

    except KeyboardInterrupt:
        print("\nStopped by user.")