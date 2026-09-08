from typing import List, Optional
from pydantic import BaseModel
from pump_system_analyzer.core.solver import Solver, OperatingPoint
from pump_system_analyzer.core.pump import Pump
from pump_system_analyzer.core.system import HydraulicSystem
from pump_system_analyzer.core.fluid import Fluid
from pump_system_analyzer.core.drive import DriveSystem

class DemandPeriod(BaseModel):
    duration_hours: float
    required_flow_m3h: float
    frequency_hz: Optional[float] = None
    throttle_k_loss: Optional[float] = None

class EnergyAnalysis:
    """
    Evaluates energy consumption over a profile.
    """
    def __init__(self, 
                 pump: Pump, 
                 system: HydraulicSystem, 
                 fluid: Fluid,
                 drive: DriveSystem,
                 energy_cost_per_kwh: float = 0.15):
        self.pump = pump
        self.system = system
        self.fluid = fluid
        self.drive = drive
        self.energy_cost_per_kwh = energy_cost_per_kwh

    def evaluate_period(self, period: DemandPeriod) -> dict:
        """
        Evaluate a single period. If required_flow is given, we must achieve it
        either by VFD or throttling.
        """
        # Create modified system if throttled
        sys = HydraulicSystem(
            static_head=self.system.static_head,
            suction_pressure_pa=self.system.suction_pressure_pa,
            discharge_pressure_pa=self.system.discharge_pressure_pa,
            suction_elevation=self.system.suction_elevation,
            discharge_elevation=self.system.discharge_elevation,
            fluid_density=self.system.fluid_density
        )
        sys.k_system = self.system.k_system
        if period.throttle_k_loss:
            sys.k_system += period.throttle_k_loss
            
        # Create modified pump if speed changed
        p = self.pump
        speed_fraction = 1.0
        if period.frequency_hz:
            speed_fraction = period.frequency_hz / 50.0 # Assuming 50Hz is nominal
            new_speed = p.metadata.speed_rpm * speed_fraction
            p = p.get_affinity_pump(new_speed)
            
        op = Solver.solve(p, sys, self.fluid)
        
        # Calculate electrical power
        shaft_power = op.power_shaft or 0.0
        elec_power = self.drive.calculate_electrical_power_kw(shaft_power, speed_fraction)
        
        energy_kwh = elec_power * period.duration_hours
        cost = energy_kwh * self.energy_cost_per_kwh
        
        return {
            "flow": op.q,
            "head": op.h,
            "shaft_power_kw": shaft_power,
            "elec_power_kw": elec_power,
            "energy_kwh": energy_kwh,
            "cost": cost
        }

    def evaluate_profile(self, periods: List[DemandPeriod]) -> dict:
        results = [self.evaluate_period(p) for p in periods]
        total_energy = sum(r["energy_kwh"] for r in results)
        total_cost = sum(r["cost"] for r in results)
        
        return {
            "total_energy_kwh": total_energy,
            "total_cost": total_cost,
            "periods": results
        }
