from typing import Optional, Dict, Any
import numpy as np
from pydantic import BaseModel, Field

from pump_system_analyzer.core.curve import Curve, CurveData

class PumpMetadata(BaseModel):
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    size: Optional[str] = None
    impeller_diameter: Optional[float] = None
    speed_rpm: Optional[float] = None
    fluid_tested: Optional[str] = "Water"
    notes: Optional[str] = None

class Pump:
    """
    Represents a centrifugal pump with its performance curves.
    All internal calculations use SI (or consistent) units, usually m3/h for Q and m for H.
    """
    def __init__(self, 
                 h_curve: Curve, 
                 eff_curve: Optional[Curve] = None,
                 power_curve: Optional[Curve] = None,
                 npshr_curve: Optional[Curve] = None,
                 metadata: Optional[PumpMetadata] = None):
        self.h_curve = h_curve
        self.eff_curve = eff_curve
        self.power_curve = power_curve
        self.npshr_curve = npshr_curve
        self.metadata = metadata or PumpMetadata()
        
        self._calculate_bep()

    def _calculate_bep(self):
        """Finds the Best Efficiency Point (BEP) if efficiency curve is provided."""
        self.bep_q = None
        self.bep_eff = None
        self.bep_h = None
        
        if self.eff_curve:
            # Simple grid search for maximum efficiency within curve bounds
            q_vals = np.linspace(self.eff_curve.x_min, self.eff_curve.x_max, 1000)
            eff_vals = self.eff_curve.evaluate(q_vals, allow_extrapolation=False)
            max_idx = np.argmax(eff_vals)
            
            self.bep_q = float(q_vals[max_idx])
            self.bep_eff = float(eff_vals[max_idx])
            
            if self.bep_q >= self.h_curve.x_min and self.bep_q <= self.h_curve.x_max:
                self.bep_h = float(self.h_curve.evaluate(self.bep_q))

    def get_affinity_pump(self, new_speed: float) -> 'Pump':
        """
        Creates a new Pump object scaled by affinity laws.
        Q2 = Q1 * (N2/N1)
        H2 = H1 * (N2/N1)^2
        P2 = P1 * (N2/N1)^3
        """
        if not self.metadata.speed_rpm:
            raise ValueError("Base pump speed must be known to apply affinity laws.")
            
        ratio = new_speed / self.metadata.speed_rpm
        
        # Scale H Curve
        h_q_new = [q * ratio for q in self.h_curve.raw_data.x]
        h_h_new = [h * (ratio**2) for h in self.h_curve.raw_data.y]
        new_h_curve = Curve(CurveData(x=h_q_new, y=h_h_new), name=f"{self.h_curve.name} @ {new_speed} RPM")
        
        # Scale Eff Curve - Assuming efficiency remains constant at homologous points
        new_eff_curve = None
        if self.eff_curve:
            eff_q_new = [q * ratio for q in self.eff_curve.raw_data.x]
            new_eff_curve = Curve(CurveData(x=eff_q_new, y=self.eff_curve.raw_data.y), name=f"{self.eff_curve.name} @ {new_speed} RPM")
            
        # Scale Power Curve
        new_p_curve = None
        if self.power_curve:
            p_q_new = [q * ratio for q in self.power_curve.raw_data.x]
            p_p_new = [p * (ratio**3) for p in self.power_curve.raw_data.y]
            new_p_curve = Curve(CurveData(x=p_q_new, y=p_p_new), name=f"{self.power_curve.name} @ {new_speed} RPM")
            
        # NPSHr is complex, often scaled with ratio^2 but standard says ratio^x where x is 1.5 to 2.
        # Following common practice (ratio^2) but warning user.
        new_npshr_curve = None
        if self.npshr_curve:
            npshr_q_new = [q * ratio for q in self.npshr_curve.raw_data.x]
            npshr_h_new = [h * (ratio**2) for h in self.npshr_curve.raw_data.y]
            new_npshr_curve = Curve(CurveData(x=npshr_q_new, y=npshr_h_new), name=f"{self.npshr_curve.name} @ {new_speed} RPM (Approx)")
            
        new_meta = self.metadata.model_copy()
        new_meta.speed_rpm = new_speed
        
        return Pump(
            h_curve=new_h_curve,
            eff_curve=new_eff_curve,
            power_curve=new_p_curve,
            npshr_curve=new_npshr_curve,
            metadata=new_meta
        )

    def get_por(self, lower_pct: float = 0.7, upper_pct: float = 1.2) -> Optional[tuple[float, float]]:
        """
        Preferred Operating Region (POR). Typically 70% to 120% of BEP flow.
        """
        if self.bep_q:
            return (self.bep_q * lower_pct, self.bep_q * upper_pct)
        return None
