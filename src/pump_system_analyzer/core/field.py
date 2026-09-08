import numpy as np
from typing import List, Optional
from pydantic import BaseModel
from pump_system_analyzer.core.fluid import Fluid
from pump_system_analyzer.core.curve import Curve, SystemCurve

class FieldMeasurement(BaseModel):
    flow_m3h: float
    suction_pressure_pa: float
    discharge_pressure_pa: float
    suction_elevation_m: float = 0.0
    discharge_elevation_m: float = 0.0
    suction_diameter_m: Optional[float] = None
    discharge_diameter_m: Optional[float] = None
    electrical_power_kw: Optional[float] = None
    frequency_hz: Optional[float] = None
    
class FieldAnalysis:
    @staticmethod
    def calculate_tdh(measurement: FieldMeasurement, fluid: Fluid) -> float:
        """
        TDH = (Pd - Ps)/(rho*g) + (vd^2 - vs^2)/(2g) + (zd - zs)
        """
        g = 9.80665
        
        # Pressure head
        dp = measurement.discharge_pressure_pa - measurement.suction_pressure_pa
        head_p = dp / (fluid.density * g)
        
        # Elevation head
        dz = measurement.discharge_elevation_m - measurement.suction_elevation_m
        
        # Velocity head
        head_v = 0.0
        if measurement.suction_diameter_m and measurement.discharge_diameter_m:
            q_m3s = measurement.flow_m3h / 3600.0
            
            a_s = np.pi * (measurement.suction_diameter_m / 2)**2
            v_s = q_m3s / a_s
            
            a_d = np.pi * (measurement.discharge_diameter_m / 2)**2
            v_d = q_m3s / a_d
            
            head_v = (v_d**2 - v_s**2) / (2 * g)
            
        return head_p + dz + head_v

    @staticmethod
    def estimate_system_curve(measurements: List[FieldMeasurement], fluid: Fluid, static_head_guess: float = 0.0) -> SystemCurve:
        """
        Estimates a system curve H = H_stat + K*Q^2 from field measurements.
        """
        if len(measurements) == 0:
            raise ValueError("No measurements provided.")
            
        qs = np.array([m.flow_m3h for m in measurements])
        hs = np.array([FieldAnalysis.calculate_tdh(m, fluid) for m in measurements])
        
        if len(measurements) == 1:
            # We must assume static head to find K
            q = qs[0]
            h = hs[0]
            if q == 0:
                raise ValueError("Cannot estimate K from zero flow point.")
            k = (h - static_head_guess) / (q**2)
            return SystemCurve(h_stat=static_head_guess, k=k)
        else:
            # Fit H = H_stat + K*Q^2
            # H = [1, Q^2] * [H_stat, K]^T
            A = np.vstack([np.ones(len(qs)), qs**2]).T
            # Least squares solution
            res, residuals, rank, s = np.linalg.lstsq(A, hs, rcond=None)
            h_stat, k = res
            return SystemCurve(h_stat=h_stat, k=k)
