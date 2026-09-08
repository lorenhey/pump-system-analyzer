from typing import Optional
from pump_system_analyzer.core.pump import Pump, PumpMetadata
from pump_system_analyzer.core.curve import Curve, CurveData

class ViscosityCorrection:
    """
    Applies viscosity corrections to centrifugal pump curves.
    Due to copyright on standards like ANSI/HI 9.6.7, this module 
    allows users to provide the correction factors (C_Q, C_H, C_eta)
    to generate the viscous performance curve.
    """
    
    @staticmethod
    def apply_factors(pump: Pump, 
                      c_q: float, 
                      c_h: float, 
                      c_eff: float, 
                      new_fluid_name: str = "Viscous Fluid") -> Pump:
        """
        Applies correction factors to the pump curves.
        Q_visc = Q_water * c_q
        H_visc = H_water * c_h
        Eff_visc = Eff_water * c_eff
        """
        if c_q <= 0 or c_h <= 0 or c_eff <= 0:
            raise ValueError("Correction factors must be positive.")
            
        # Scale H Curve
        h_q_new = [q * c_q for q in pump.h_curve.raw_data.x]
        h_h_new = [h * c_h for h in pump.h_curve.raw_data.y]
        new_h_curve = Curve(CurveData(x=h_q_new, y=h_h_new), name=f"{pump.h_curve.name} (Viscous)")
        
        # Scale Eff Curve
        new_eff_curve = None
        if pump.eff_curve:
            eff_q_new = [q * c_q for q in pump.eff_curve.raw_data.x]
            eff_e_new = [e * c_eff for e in pump.eff_curve.raw_data.y]
            new_eff_curve = Curve(CurveData(x=eff_q_new, y=eff_e_new), name=f"{pump.eff_curve.name} (Viscous)")
            
        # Recalculate power curve based on new H, Q, Eff
        # We don't just scale power, it's a derived result, but standard says P_visc = P_water * (C_H * C_Q / C_Eff)
        # Assuming density doesn't change here, just the pure pump performance. 
        # Actual power will depend on the new fluid's density.
        new_p_curve = None
        if pump.power_curve:
            p_q_new = [q * c_q for q in pump.power_curve.raw_data.x]
            # Wait, power also depends on density! 
            # P_shaft = rho * g * Q * H / eta
            # So if we just scale the WATER power to VISCOUS WATER power:
            # P_visc_water = P_water * (C_Q * C_H / C_Eff)
            # The solver will compute actual power using fluid density.
            # Let's drop the power curve and rely on Eff and Fluid density for power in viscous mode,
            # which is much safer and physically sound.
            pass
            
        new_meta = pump.metadata.model_copy()
        new_meta.fluid_tested = new_fluid_name
        new_meta.notes = f"Viscosity corrected: Cq={c_q}, Ch={c_h}, Ceff={c_eff}"
        
        return Pump(
            h_curve=new_h_curve,
            eff_curve=new_eff_curve,
            power_curve=None, # Dropped to force calculation from density and eff
            npshr_curve=pump.npshr_curve, # NPSHr usually increases but hard to predict simply
            metadata=new_meta
        )
