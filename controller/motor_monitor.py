import time
from typing import Dict
from robot_params import MOTOR

class MotorMonitor:
    def __init__(self):
        self.mass = MOTOR["mass_kg"]
        self.c_rr = MOTOR["rolling_coeff"]
        self.eta = MOTOR["drivetrain_efficiency"]

        self.speed = MOTOR["init_speed"]
        self.distance = 0.0
        self.energy = 0.0
        self._last_time = time.time()

    def update_speed(self, speed: float):
        self.speed = speed

    def _compute_power(self) -> float:
        g = 9.81
        force = self.c_rr * self.mass * g
        return force * self.speed / self.eta

    def sample(self) -> Dict:
        now = time.time()
        dt = now - self._last_time
        self._last_time = now

        power = self._compute_power()
        self.distance += self.speed * dt
        self.energy += power * dt

        return {
            "speed_mps": self.speed,
            "mech_power_w": power,
            "distance_m": self.distance,
            "mech_energy_j": self.energy,
        }
