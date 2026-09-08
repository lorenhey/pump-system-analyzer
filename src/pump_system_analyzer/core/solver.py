from typing import Optional, Dict, Any, List
import numpy as np
from scipy.optimize import brentq

from pump_system_analyzer.core.pump import Pump
from pump_system_analyzer.core.system import HydraulicSystem
from pump_system_analyzer.core.fluid import Fluid

class OperatingPoint:
    def __init__(self, q: float, h: float, pump: Pump, system: HydraulicSystem, fluid: Fluid):
        self.q = q
        self.h = h
        self.pump = pump
        self.system = system
        self.fluid = fluid
        
        # Derived
        self.eff = pump.eff_curve(q) if pump.eff_curve else None
        
        # Power
        if pump.power_curve:
            self.power_shaft = pump.power_curve(q)
        elif self.eff:
            # P = rho * g * Q * H / eta
            # Q is often m3/h. Need m3/s for Watts.
            q_m3s = q / 3600.0
            g = 9.80665
            self.power_shaft = ((fluid.density * g * q_m3s * h) / (self.eff / 100.0)) / 1000.0
        else:
            self.power_shaft = None
            
        self.npshr = pump.npshr_curve(q) if pump.npshr_curve else None
        
    def export_manifest(self) -> Dict[str, Any]:
        """
        Generates a traceable manifest of the analysis.
        """
        import datetime
        import pump_system_analyzer
        return {
            "timestamp": datetime.datetime.now().isoformat(),
            "engine_version": pump_system_analyzer.__version__ if hasattr(pump_system_analyzer, '__version__') else "unknown",
            "operating_point": {
                "q_m3h": self.q,
                "h_m": self.h,
                "efficiency_pct": self.eff,
                "power_shaft_kw": self.power_shaft,
                "npshr_m": self.npshr
            },
            "fluid": {
                "name": self.fluid.name,
                "density_kg_m3": self.fluid.density,
                "viscosity_pa_s": self.fluid.viscosity,
                "temperature_k": self.fluid.temperature
            },
            "pump_metadata": self.pump.metadata.model_dump() if hasattr(self.pump.metadata, 'model_dump') else self.pump.metadata.dict(),
            "system": {
                "static_head_m": self.system.static_head,
                "k_system": self.system.k_system
            }
        }

class Solver:
    @staticmethod
    def solve(pump: Pump, system: HydraulicSystem, fluid: Fluid, q_guess: Optional[float] = None) -> OperatingPoint:
        """
        Finds the operating point where H_pump(Q) = H_system(Q)
        """
        def objective(q: float) -> float:
            # We must handle extrapolation carefully if the solver goes out of bounds.
            # brentq requires bounds. We'll set bounds based on the pump curve.
            return pump.h_curve(q) - system(q)
        
        q_min = pump.h_curve.x_min
        q_max = pump.h_curve.x_max
        
        # Check signs at boundaries
        try:
            f_min = objective(q_min)
            f_max = objective(q_max)
        except ValueError as e:
             raise RuntimeError(f"Could not evaluate at boundaries: {e}")

        if f_min * f_max > 0:
            # They have the same sign. It might not intersect, or intersects twice.
            # Usually pump H goes down, system H goes up. 
            # If f_min > 0 (Pump > Sys) and f_max > 0 (Pump > Sys), the pump is too big or curve is too short.
            # If f_min < 0 (Sys > Pump), the pump is too small.
            if f_min > 0:
                raise RuntimeError(f"No intersection found. Pump head is higher than system head at maximum curve flow ({q_max}). The pump curve may need extrapolation or the pump is oversized for this curve data.")
            else:
                raise RuntimeError(f"No intersection found. System head is higher than pump head at minimum flow ({q_min}). The pump is unable to overcome static head or system resistance.")

        # Find root
        try:
            q_op = brentq(objective, q_min, q_max, xtol=1e-6)
        except ValueError as e:
            raise RuntimeError(f"Solver failed to converge: {e}")
            
        h_op = pump.h_curve(q_op)
        
        return OperatingPoint(q=q_op, h=h_op, pump=pump, system=system, fluid=fluid)
