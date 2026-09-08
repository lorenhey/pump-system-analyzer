from typing import Dict, Any, Optional
from pump_system_analyzer.core.fluid import Fluid

class NPSHAnalysis:
    """
    Handles NPSHa calculations and NPSH margin.
    """
    def __init__(self, 
                 fluid: Fluid,
                 suction_surface_pressure_pa: float,
                 suction_elevation_m: float,
                 pump_centerline_elevation_m: float,
                 suction_friction_loss_m: float):
        self.fluid = fluid
        self.suction_surface_pressure_pa = suction_surface_pressure_pa
        self.suction_elevation_m = suction_elevation_m
        self.pump_centerline_elevation_m = pump_centerline_elevation_m
        self.suction_friction_loss_m = suction_friction_loss_m
        self.g = 9.80665
        
    def calculate_npsha(self) -> float:
        """
        NPSHa = (P_abs / (rho * g)) + (z_source - z_pump) - h_f - (P_v / (rho * g))
        """
        head_abs = self.suction_surface_pressure_pa / (self.fluid.density * self.g)
        delta_z = self.suction_elevation_m - self.pump_centerline_elevation_m
        head_vapor = self.fluid.vapor_pressure / (self.fluid.density * self.g)
        
        npsha = head_abs + delta_z - self.suction_friction_loss_m - head_vapor
        return npsha

    def evaluate_margin(self, npshr: float, margin_ratio_criteria: float = 1.1, margin_abs_criteria_m: float = 0.5) -> Dict[str, Any]:
        """
        Evaluates NPSH margin based on absolute and ratio criteria.
        Returns a dictionary with the results.
        """
        npsha = self.calculate_npsha()
        margin_abs = npsha - npshr
        margin_ratio = npsha / npshr if npshr > 0 else float('inf')
        
        is_safe = (margin_abs >= margin_abs_criteria_m) and (margin_ratio >= margin_ratio_criteria)
        
        return {
            "npsha_m": npsha,
            "npshr_m": npshr,
            "margin_abs_m": margin_abs,
            "margin_ratio": margin_ratio,
            "criteria_abs_m": margin_abs_criteria_m,
            "criteria_ratio": margin_ratio_criteria,
            "is_safe": is_safe,
            "warning": "POTENTIAL CAVITATION RISK" if not is_safe else "OK"
        }
