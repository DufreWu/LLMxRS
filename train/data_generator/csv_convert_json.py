#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import json
from config import DATA_DIR, THRESHOLDS

# ============================================================
# Load logs
# ============================================================

sys_df = pd.read_csv(DATA_DIR["sys_dir"])
app_df = pd.read_csv(DATA_DIR["appls_dir"])
out_dir = DATA_DIR["out_dir"]

# Merge on common timestep key
df = sys_df.merge(app_df, on="ITERATION")

def requirement_pressure(thr, qos):
    margin = thr - qos
    if margin >= THRESHOLDS["appls_pressure"]:
        return "low"
    elif margin >= 0:
        return "moderate"
    else:
        return "high"

def reasoning_text(speed, gpu, pressure):
    parts = []

    if speed > THRESHOLDS["speed_high"]:
        parts.append("a high driving speed increases mechanical power consumption")

    if gpu > THRESHOLDS["gpu_high"]:
        parts.append("high GPU utilization increases computational power consumption")

    if parts:
        prefix = f"The robot is operating at {' and '.join(parts)}. "
    else:
        prefix = "The robot is operating under moderate mechanical and computational load. "

    if pressure == "high":
        suffix = (
            "Given the high application requirement pressure, "
            "resource adjustments should be conservative to avoid QoS violations."
        )
    else:
        suffix = (
            f"Given the {pressure} application requirement pressure and medium task urgency, "
            "energy-efficient adjustments can be applied without violating QoS constraints."
        )

    return prefix + suffix


def behavior_change(speed, cpu_f, gpu_f, pressure):
    cpu_ghz = cpu_f / 1e6
    gpu_ghz = gpu_f / 1e6

    if pressure == "high":
        return (
            f"- Speed: {speed:.1f} m/s\n"
            f"- CPU frequency: {cpu_ghz:.2f} GHz\n"
            f"- GPU frequency: {gpu_ghz:.2f} GHz"
        )

    return (
        f"- Speed: {max(speed - 1.5, 2.5):.1f} m/s\n"
        f"- CPU frequency: {min(cpu_ghz, 1.0):.2f} GHz\n"
        f"- GPU frequency: {min(gpu_ghz, 0.8):.2f} GHz"
    )

# ============================================================
# Convert to conversation-style JSON (single array)
# ============================================================

all_samples = []
with open(out_dir, "w") as f:
    for _, r in df.iterrows():

        if r.SOC <= 0 or r.SOH <= 0:
            continue

        pressure = requirement_pressure(r.THR1, r.REF1)

        # ----------------------------
        # robot: objective state
        # ----------------------------
        robot_msg = (
            "Robot state:\n"
            f"- Speed: {r.SPEED:.1f} m/s\n"
            f"- CPU utilization: {r.UTIL0:.0f}%\n"
            f"- GPU utilization: {r.GPU_UTIL:.0f}%\n"
            f"- Application requirement pressure: {pressure}\n"
            f"- Battery SOC: {r.SOC * 100:.0f}%\n"
            f"- Battery SOH: {r.SOH * 100:.0f}%"
        )

        # ----------------------------
        # human: task instruction
        # ----------------------------
        human_msg = (
            "You are an energy-efficiency advisor.\n"
            "Your task is to minimize energy consumption while satisfying application QoS."
        )

        # ----------------------------
        # gpt: reasoning + action
        # ----------------------------
        gpt_msg = (
            "Reasoning:\n"
            f"{reasoning_text(r.SPEED, r.GPU_UTIL, pressure)}\n\n"
            "Change behavior:\n"
            f"{behavior_change(r.SPEED, r.FREQ_L, r.FREQ_G, pressure)}"
        )

        sample = {
            "conversations": [
                {
                    "from": "robot", 
                    "value": robot_msg
                },
                {
                    "from": "human", 
                    "value": human_msg
                },
                {
                    "from": "gpt",   
                    "value": gpt_msg
                },
            ]
        }

        all_samples.append(sample)

with open(out_dir, "w") as f:
    json.dump(all_samples, f, indent=2)

print(f"[OK] Saved {len(all_samples)} samples to {out_dir}")
