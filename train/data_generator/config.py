# ----------------------------
# Config
# ----------------------------
DATA_DIR = {
    "sys_dir": "./csv_data/pdqn_sys.csv",
    "appls_dir": "./csv_data/pdqn_appls.csv",
    "out_dir": "./../dataset/sft/sft_energy.json"
}

# thresholds (adjust once, fixed forever)
THRESHOLDS = {
    "gpu_high": 80,           # GPU utilization (%) above which compute pressure is high
    "cpu_high": 70,           # CPU utilization (%) above which compute pressure is high
    "speed_high": 4.0,        # Speed (m/s) above which mechanical load is high
    "soc_low": 0.3,           # SOC below which energy becomes critical
    "soh_degraded": 0.85,     # SOH below which battery is considered degraded
    "appls_pressure": 5       # thr - qos margin defining requirement pressure
}
