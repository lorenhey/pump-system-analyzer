import numpy as np
from pydantic import BaseModel, Field
from typing import Optional, Union

class Fluid(BaseModel):
    """
    Represents a fluid with basic properties.
    Properties are assumed to be in SI units internally:
    - density: kg/m³
    - viscosity (dynamic): Pa·s (or kg/(m·s))
    - vapor_pressure (absolute): Pa
    """
    name: str
    density: float = Field(..., gt=0, description="Density in kg/m³")
    viscosity: float = Field(..., gt=0, description="Dynamic viscosity in Pa·s")
    vapor_pressure: float = Field(default=0.0, ge=0, description="Absolute vapor pressure in Pa")
    temperature: Optional[float] = Field(default=None, description="Temperature in K (for reference)")

    @property
    def kinematic_viscosity(self) -> float:
        """Kinematic viscosity in m²/s"""
        return self.viscosity / self.density

class Water(Fluid):
    """
    Standard properties for liquid water at 1 atm as a function of temperature.
    Temperature input is in degrees Celsius for ease of use in instantiation,
    but we will store internal references consistently if needed.
    """
    def __init__(self, temperature_c: float = 20.0):
        # Convert C to K
        T_k = temperature_c + 273.15
        
        # Density (kg/m3) - simplified correlation for liquid water (e.g., Kell 1975 or similar engineering fit)
        # Using a reliable polynomial for 0 to 100 C
        t = temperature_c
        rho = 999.83952 + 16.945176*t - 7.9870401e-3*t**2 - 46.170461e-6*t**3 + 105.56302e-9*t**4 - 280.54253e-12*t**5
        rho = rho / (1 + 16.897850e-3*t)

        # Dynamic viscosity (Pa*s) - Correlation from Al-Shemmeri (2012) or standard reference
        # mu = 2.414e-5 * 10**(247.8 / (T_k - 140))
        # Let's use a standard Vogel-Fulcher-Tammann or similar.
        # simpler accurate empirical formula for water viscosity:
        mu = 0.001 * np.exp(1.003 - 1.479e-2 * (T_k - 273.15) + 1.982e-5 * (T_k - 273.15)**2)
        # More accurate (IAPWS 2008 simplified):
        mu_mPa_s = np.exp(0.5806436 - 3.358120e-3 * t + 1.111495e-5 * t**2 - 1.636653e-8 * t**3) # rough fit
        # Let's use the widely accepted correlation:
        # mu (Pa s) = A * 10^(B / (T - C))
        A = 2.414e-5
        B = 247.8
        C = 140.0
        mu = A * 10**(B / (T_k - C))

        # Vapor pressure (Pa) - Antoine equation or similar (e.g. Buck equation)
        # P_v (Pa)
        # Antoine for water: log10(P/mmHg) = A - B/(T_C + C)
        # A = 8.07131, B = 1730.63, C = 233.426 (for 1 to 100 C)
        A_ant = 8.07131
        B_ant = 1730.63
        C_ant = 233.426
        log10_P_mmHg = A_ant - B_ant / (t + C_ant)
        P_v_mmHg = 10**log10_P_mmHg
        P_v_pa = P_v_mmHg * 133.322368

        super().__init__(
            name=f"Water ({temperature_c} °C)",
            density=float(rho),
            viscosity=float(mu),
            vapor_pressure=float(P_v_pa),
            temperature=T_k
        )

# Useful constants
g = 9.80665 # Standard gravity m/s^2
