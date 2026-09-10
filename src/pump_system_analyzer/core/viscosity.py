from typing import Optional, Tuple
from pump_system_analyzer.core.pump import Pump, PumpMetadata
from pump_system_analyzer.core.curve import Curve, CurveData
from pump_system_analyzer.core.fluid import Fluid

class ViscosityCorrection:
    """
    Applies viscosity corrections to centrifugal pump curves.
    Implements a general analytical approximation based on standard public-domain
    empirical formulas for viscous fluids in centrifugal pumps.
    """
    
    @staticmethod
    def calculate_correction_factors(pump: Pump, fluid: Fluid) -> Tuple[float, float, float]:
        """
        Calculates C_Q, C_H, and C_eff based on the parameter B approximation.
        This allows calculation directly from kinematic viscosity without hardcoding tables.
        """
        if pump.bep_q is None or pump.bep_h is None:
            raise ValueError("Pump BEP must be known to calculate viscosity corrections.")
            
        if not pump.metadata.speed_rpm:
            raise ValueError("Pump RPM must be known to calculate viscosity corrections.")
            
        # Convert properties to traditional units for the empirical B parameter
        # nu (cSt) = dynamic_viscosity (Pa.s) / density (kg/m3) * 10^6
        nu_cst = (fluid.viscosity / fluid.density) * 1e6
        
        if nu_cst <= 1.0:
            # Water-like, no correction needed
            return 1.0, 1.0, 1.0
            
        q_gpm = pump.bep_q * 4.40287  # m3/h to gpm
        h_ft = pump.bep_h * 3.28084   # m to ft
        n_rpm = pump.metadata.speed_rpm
        
        # B parameter formula (generalized empirical form)
        # B = 16.5 * (nu_cst^0.5 * H_ft^0.0625) / (Q_gpm^0.25 * N_rpm^0.25)
        # We cap B to avoid unreasonable extrapolation
        b_param = 16.5 * (nu_cst**0.5 * h_ft**0.0625) / (q_gpm**0.25 * n_rpm**0.25)
        b_param = min(b_param, 40.0) # Cap for extreme viscosities
        
        # Empirical correction factors based on B
        import math
        c_q = math.exp(-0.12 * b_param)
        c_h = max(0.4, 1.0 - 0.03 * b_param)
        c_eff = max(0.1, b_param**(-0.05) if b_param > 1.0 else 1.0 - 0.01 * b_param)
        
        return c_q, c_h, c_eff

    @classmethod
    def apply_fluid(cls, pump: Pump, fluid: Fluid) -> Pump:
        """
        Automatically calculates factors and applies them.
        """
        c_q, c_h, c_eff = cls.calculate_correction_factors(pump, fluid)
        return cls.apply_factors(pump, c_q, c_h, c_eff, new_fluid_name=fluid.name)

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
