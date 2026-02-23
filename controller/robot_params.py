"""
Global system parameters for the robot platform
================================================
Single source of truth for all monitors & controllers.
"""

# ============================================================
# Battery parameters
# ============================================================
BATTERY = {
    # Nominal capacity
    "capacity_ah": 5.0,

    # Initial state
    "init_soc": 1.0,

    # Sysfs paths (example – adjust to your platform)
    "voltage_path": "/sys/class/power_supply/BAT0/voltage_now",  # V or mV
    "current_path": "/sys/class/power_supply/BAT0/current_now",  # A or mA

    # Scaling (if sysfs uses mV / mA)
    "voltage_scale": 1000.0,   # mV → V
    "current_scale": 1000.0,   # mA → A
}

# ============================================================
# Motor / mechanical parameters
# ============================================================
MOTOR = {
    "mass_kg": 18.0,
    "rolling_coeff": 0.015,
    "drivetrain_efficiency": 0.90,
    "init_speed": 0.0,
}

# ============================================================
# Jetson / compute parameters
# ============================================================
JETSON = {
    "ina_base": "/sys/bus/i2c/drivers/ina3221x",

    # CPU
    "cpu_freq_scale": 1000.0,   # kHz → MHz

    # GPU (Orin NX GA10B)
    "gpu_load_path": "/sys/devices/gpu.0/load",
    "gpu_load_scale": 10.0,     # → %
    "gpu_freq_path": "/sys/devices/17000000.ga10b/devfreq/17000000.ga10b/cur_freq",
    "gpu_freq_scale": 1e6,      # Hz → MHz
}

# ============================================================
# Controller / logging
# ============================================================
CONTROLLER = {
    "sample_period_s": 1.0,
}
