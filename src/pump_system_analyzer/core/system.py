from typing import Union
import numpy as np
from pydantic import BaseModel
from pump_system_analyzer.core.curve import Curve, SystemCurve

class PipingComponent(BaseModel):
    name: str
    k_factor: float
    # Could be expanded with D, L, f, etc.

class HydraulicSystem:
    """
    Represents the hydraulic system.
    H_sys = (P_d - P_s)/(rho*g) + (z_d - z_s) + losses
    """
    def __init__(self, 
                 static_head: float = 0.0, 
                 suction_pressure_pa: float = 101325.0,
                 discharge_pressure_pa: float = 101325.0,
                 suction_elevation: float = 0.0,
                 discharge_elevation: float = 0.0,
                 fluid_density: float = 998.2):
        
        self.suction_pressure_pa = suction_pressure_pa
        self.discharge_pressure_pa = discharge_pressure_pa
        self.suction_elevation = suction_elevation
        self.discharge_elevation = discharge_elevation
        self.fluid_density = fluid_density
        
        # Override with explicit static head if provided, else compute
        if static_head != 0.0:
            self.static_head = static_head
        else:
            self.static_head = self._compute_static_head()
            
        self.k_system = 0.0
        self.components = []
        self.custom_curve = None
        
    def _compute_static_head(self) -> float:
        g = 9.80665
        delta_p = self.discharge_pressure_pa - self.suction_pressure_pa
        head_p = delta_p / (self.fluid_density * g)
        delta_z = self.discharge_elevation - self.suction_elevation
        return head_p + delta_z

    def add_k_loss(self, k: float, name: str = "Generic"):
        self.k_system += k
        self.components.append(PipingComponent(name=name, k_factor=k))
        
    def set_custom_curve(self, curve: Curve):
        """Allows setting a measured or complex system curve."""
        self.custom_curve = curve

    def get_curve(self) -> Union[SystemCurve, Curve]:
        if self.custom_curve:
            return self.custom_curve
        return SystemCurve(h_stat=self.static_head, k=self.k_system)

    def evaluate(self, q: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        curve = self.get_curve()
        return curve.evaluate(q)

    def __call__(self, q: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        return self.evaluate(q)
