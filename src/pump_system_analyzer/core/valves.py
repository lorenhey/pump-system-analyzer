import numpy as np
from typing import Union
from pydantic import BaseModel, Field

class ControlValve(BaseModel):
    """
    Represents a control valve using Kv (m3/h at 1 bar pressure drop for water).
    """
    name: str = "Control Valve"
    kv_max: float = Field(..., gt=0, description="Maximum Kv value (fully open)")
    characteristic: str = Field(default="equal_percentage", description="'linear' or 'equal_percentage'")
    rangeability: float = Field(default=50.0, description="R factor for equal percentage valves (e.g., 50)")

    def get_kv(self, opening_fraction: float) -> float:
        """
        Calculate Kv at a given opening fraction (0.0 to 1.0).
        """
        if opening_fraction <= 0.0:
            return 1e-6 # Practically closed, avoid division by zero
        if opening_fraction >= 1.0:
            return self.kv_max

        if self.characteristic == "linear":
            return self.kv_max * opening_fraction
        elif self.characteristic == "equal_percentage":
            # Kv = Kv_max * R^(x - 1)
            return self.kv_max * (self.rangeability ** (opening_fraction - 1.0))
        else:
            raise ValueError(f"Unknown valve characteristic: {self.characteristic}")

    def head_loss_m(self, q_m3h: Union[float, np.ndarray], opening_fraction: float = 1.0) -> Union[float, np.ndarray]:
        """
        Calculate head loss in meters of fluid for a given flow and opening.
        Formula: delta_P (bar) = (Q / Kv)^2 * SG
        head_loss (m) = delta_P * 10^5 / (rho * g)
                      = (Q/Kv)^2 * (rho/1000) * 10^5 / (rho * 9.80665)
                      = (Q/Kv)^2 * 100 / 9.80665
                      ~ 10.197 * (Q/Kv)^2
        Notice that density cancels out when converting bar to meters of the SAME fluid.
        """
        kv = self.get_kv(opening_fraction)
        return 10.197162 * (np.array(q_m3h) / kv)**2
