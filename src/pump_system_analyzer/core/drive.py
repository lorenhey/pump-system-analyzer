from typing import Optional
from pydantic import BaseModel, Field

class Motor(BaseModel):
    name: str = "Standard Motor"
    rated_power_kw: float
    nominal_efficiency: float = Field(..., gt=0, le=100) # In percentage
    speed_rpm: float
    
    def get_efficiency(self, load_fraction: float) -> float:
        """
        Estimate efficiency at partial load.
        Simple model or table lookup could go here.
        For now, assume constant if > 50% load, otherwise degrades.
        """
        if load_fraction >= 0.5:
            return self.nominal_efficiency
        else:
            # Simple degradation for low loads
            return self.nominal_efficiency * (0.5 + load_fraction)
            
class VFD(BaseModel):
    name: str = "Standard VFD"
    nominal_efficiency: float = 97.0 # Typical VFD efficiency in %
    min_freq_hz: float = 20.0
    max_freq_hz: float = 60.0
    nominal_freq_hz: float = 50.0
    
    def get_efficiency(self, speed_fraction: float) -> float:
        """
        VFD efficiency slightly decreases at lower speeds.
        """
        if speed_fraction >= 0.8:
            return self.nominal_efficiency
        elif speed_fraction >= 0.5:
            return self.nominal_efficiency - 2.0
        else:
            return self.nominal_efficiency - 5.0

class DriveSystem:
    def __init__(self, motor: Optional[Motor] = None, vfd: Optional[VFD] = None):
        self.motor = motor
        self.vfd = vfd
        
    def calculate_electrical_power_kw(self, shaft_power_kw: float, speed_fraction: float = 1.0) -> float:
        """
        P_elec = P_shaft / (eta_motor * eta_vfd)
        """
        eta_motor = 1.0
        if self.motor:
            # Estimate load fraction
            load_fraction = shaft_power_kw / self.motor.rated_power_kw
            eta_motor = self.motor.get_efficiency(load_fraction) / 100.0
            
        eta_vfd = 1.0
        if self.vfd:
            eta_vfd = self.vfd.get_efficiency(speed_fraction) / 100.0
            
        if eta_motor <= 0 or eta_vfd <= 0:
            raise ValueError("Efficiencies must be > 0")
            
        return shaft_power_kw / (eta_motor * eta_vfd)

    def calculate_wire_to_water_efficiency(self, pump_eff: float, speed_fraction: float = 1.0, load_fraction: float = 1.0) -> float:
        eta_motor = self.motor.get_efficiency(load_fraction) / 100.0 if self.motor else 1.0
        eta_vfd = self.vfd.get_efficiency(speed_fraction) / 100.0 if self.vfd else 1.0
        return (pump_eff / 100.0) * eta_motor * eta_vfd * 100.0
