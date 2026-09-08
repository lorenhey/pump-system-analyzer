import numpy as np
from typing import List
from pump_system_analyzer.core.pump import Pump
from pump_system_analyzer.core.curve import Curve, CurveData

class PumpConfiguration:
    """
    Handles parallel and series configurations of multiple pumps.
    Produces a composite Pump object that can be used with the Solver.
    """
    @staticmethod
    def parallel(pumps: List[Pump], name: str = "Parallel Pumps") -> Pump:
        """
        Combines multiple pumps in parallel. Q_total = sum(Q_i) at a given H.
        """
        if not pumps:
            raise ValueError("Must provide at least one pump.")
        if len(pumps) == 1:
            return pumps[0]
            
        # Find the common head range
        h_max_common = max(p.h_curve.evaluate(p.h_curve.x_min) for p in pumps)
        h_min_common = max(p.h_curve.evaluate(p.h_curve.x_max) for p in pumps)
        
        # We need a monotonic array of heads to evaluate
        # PCHIP is monotonic, so we can invert the relationship for evaluation.
        # Let's generate a dense array of H values
        h_vals = np.linspace(h_min_common, h_max_common, 200)
        
        q_totals = np.zeros_like(h_vals)
        
        for p in pumps:
            # We need to find Q for a given H. 
            # Since H(Q) is decreasing, we can use bisection or just interpolate the inverted data.
            h_data = p.h_curve.raw_data.y
            q_data = p.h_curve.raw_data.x
            
            # PCHIP requires strictly increasing x, so we reverse if necessary
            if h_data[0] > h_data[-1]:
                h_data = h_data[::-1]
                q_data = q_data[::-1]
                
            inv_curve = Curve(CurveData(x=h_data, y=q_data), name="Inv")
            
            # Add Qs, but only where H is within the pump's capability
            q_p = np.zeros_like(h_vals)
            valid_mask = (h_vals >= min(h_data)) & (h_vals <= max(h_data))
            q_p[valid_mask] = inv_curve(h_vals[valid_mask])
            q_totals += q_p

        # Re-invert to get H(Q) composite
        q_totals_sorted, h_vals_sorted = zip(*sorted(zip(q_totals, h_vals)))
        
        composite_h_curve = Curve(CurveData(x=list(q_totals_sorted), y=list(h_vals_sorted)), name=name)
        
        # Construct a synthetic Pump object
        # Eff and Power curves are more complex for non-identical parallel pumps,
        # but we provide the H curve so the solver works.
        return Pump(h_curve=composite_h_curve, metadata=pumps[0].metadata)

    @staticmethod
    def series(pumps: List[Pump], name: str = "Series Pumps") -> Pump:
        """
        Combines multiple pumps in series. H_total = sum(H_i) at a given Q.
        """
        if not pumps:
            raise ValueError("Must provide at least one pump.")
        if len(pumps) == 1:
            return pumps[0]
            
        # Find common flow range
        q_min = max(p.h_curve.x_min for p in pumps)
        q_max = min(p.h_curve.x_max for p in pumps)
        
        if q_min >= q_max:
            raise ValueError("Pumps do not have an overlapping flow range.")
            
        q_vals = np.linspace(q_min, q_max, 200)
        h_totals = np.zeros_like(q_vals)
        
        for p in pumps:
            h_totals += p.h_curve(q_vals)
            
        composite_h_curve = Curve(CurveData(x=list(q_vals), y=list(h_totals)), name=name)
        return Pump(h_curve=composite_h_curve, metadata=pumps[0].metadata)
