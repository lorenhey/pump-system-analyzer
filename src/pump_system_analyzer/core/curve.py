import numpy as np
from scipy.interpolate import PchipInterpolator
from typing import List, Tuple, Optional, Union
from pydantic import BaseModel, Field

class CurveData(BaseModel):
    """
    Holds the raw data points for a curve to preserve provenance.
    """
    x: List[float] = Field(..., description="X values (e.g., Flow)")
    y: List[float] = Field(..., description="Y values (e.g., Head, Efficiency, Power)")
    
    def __post_init__(self):
        if len(self.x) != len(self.y):
            raise ValueError("x and y arrays must have the same length")
        # Ensure it is sorted by x
        pts = sorted(zip(self.x, self.y))
        self.x = [p[0] for p in pts]
        self.y = [p[1] for p in pts]

class Curve:
    """
    Represents a relationship Y = f(X).
    Uses PCHIP (Piecewise Cubic Hermite Interpolating Polynomial) 
    to guarantee monotonic behavior between points and prevent overshoot.
    """
    def __init__(self, data: CurveData, name: str = "Curve"):
        self.raw_data = data
        self.name = name
        
        # Sort data
        pts = sorted(zip(data.x, data.y))
        self._x = np.array([p[0] for p in pts], dtype=float)
        self._y = np.array([p[1] for p in pts], dtype=float)
        
        if len(self._x) < 2:
            raise ValueError("At least two points are required to define a curve.")
            
        self._interpolator = PchipInterpolator(self._x, self._y)

    @property
    def x_min(self) -> float:
        return self._x[0]

    @property
    def x_max(self) -> float:
        return self._x[-1]

    def evaluate(self, x: Union[float, np.ndarray], allow_extrapolation: bool = False) -> Union[float, np.ndarray]:
        """
        Evaluate the curve at x.
        Raises ValueError if extrapolation is attempted and allow_extrapolation is False.
        """
        x_is_scalar = np.isscalar(x)
        x_arr = np.atleast_1d(x)
        
        if not allow_extrapolation:
            if np.any(x_arr < self.x_min) or np.any(x_arr > self.x_max):
                # Calculate extent of extrapolation
                min_val = np.min(x_arr)
                max_val = np.max(x_arr)
                if min_val < self.x_min:
                    diff = self.x_min - min_val
                    pct = (diff / self.x_max) * 100 if self.x_max != 0 else float('inf')
                    raise ValueError(f"Extrapolation warning: x={min_val} is {diff:.2f} units ({pct:.1f}%) below minimum x={self.x_min}")
                if max_val > self.x_max:
                    diff = max_val - self.x_max
                    pct = (diff / self.x_max) * 100 if self.x_max != 0 else float('inf')
                    raise ValueError(f"Extrapolation warning: x={max_val} is {diff:.2f} units ({pct:.1f}%) above maximum x={self.x_max}")
        
        # Pchip interpolator naturally extrapolates using the end derivatives.
        y_arr = self._interpolator(x_arr)
        
        return float(y_arr[0]) if x_is_scalar else y_arr

    def __call__(self, x: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        # Default to strict evaluation
        return self.evaluate(x, allow_extrapolation=False)


class SystemCurve:
    """
    Represents a system curve H(Q) = H_stat + K * Q^2
    Or an experimental curve.
    """
    def __init__(self, h_stat: float = 0.0, k: float = 0.0):
        self.h_stat = h_stat
        self.k = k

    def evaluate(self, q: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        return self.h_stat + self.k * (np.array(q) ** 2)

    def __call__(self, q: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        return self.evaluate(q)
