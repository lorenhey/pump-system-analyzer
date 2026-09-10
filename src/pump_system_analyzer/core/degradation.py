from pydantic import BaseModel
from typing import List, Dict, Optional
import datetime
from pump_system_analyzer.core.pump import Pump

class FieldMeasurement(BaseModel):
    date: datetime.date
    q_m3h: float
    h_m: float
    power_kw: Optional[float] = None
    efficiency_pct: Optional[float] = None

class DegradationAnalysis:
    """
    Compares field measurements over time against a baseline pump curve.
    """
    def __init__(self, baseline_pump: Pump):
        self.baseline_pump = baseline_pump
        self.measurements: List[FieldMeasurement] = []

    def add_measurement(self, m: FieldMeasurement):
        self.measurements.append(m)

    def analyze(self) -> List[Dict]:
        """
        Returns the degradation delta for each measurement relative to the baseline.
        """
        self.measurements.sort(key=lambda x: x.date)
        results = []
        
        for m in self.measurements:
            try:
                expected_h = self.baseline_pump.h_curve(m.q_m3h)
                delta_h_pct = ((m.h_m - expected_h) / expected_h) * 100.0
                
                res = {
                    "date": m.date.isoformat(),
                    "flow_m3h": m.q_m3h,
                    "measured_h_m": m.h_m,
                    "expected_h_m": float(expected_h),
                    "head_degradation_pct": float(delta_h_pct)
                }
                
                if m.efficiency_pct and self.baseline_pump.eff_curve:
                    expected_eff = self.baseline_pump.eff_curve(m.q_m3h)
                    delta_eff_pct = ((m.efficiency_pct - expected_eff) / expected_eff) * 100.0
                    res["measured_eff_pct"] = m.efficiency_pct
                    res["expected_eff_pct"] = float(expected_eff)
                    res["eff_degradation_pct"] = float(delta_eff_pct)
                    
                results.append(res)
            except ValueError:
                # Flow out of bounds for baseline curve
                pass
                
        return results
