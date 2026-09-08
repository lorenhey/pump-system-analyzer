from pathlib import Path
import json
from pump_system_analyzer.core.fluid import Water
from pump_system_analyzer.core.curve import Curve, CurveData
from pump_system_analyzer.core.pump import Pump, PumpMetadata
from pump_system_analyzer.core.system import HydraulicSystem
from pump_system_analyzer.core.drive import DriveSystem, Motor, VFD
from pump_system_analyzer.core.energy import EnergyAnalysis, DemandPeriod

def main():
    fluid = Water(20)
    
    # Define a base pump
    q_data = [0, 20, 40, 60, 80, 100, 120]
    h_data = [45, 44, 42, 38, 32, 23, 10]
    eff_data = [0, 30, 55, 70, 78, 75, 50]
    
    pump = Pump(
        h_curve=Curve(CurveData(x=q_data, y=h_data), name="Pump"),
        eff_curve=Curve(CurveData(x=q_data, y=eff_data), name="Eff"),
        metadata=PumpMetadata(speed_rpm=1450)
    )
    
    sys = HydraulicSystem(static_head=15.0)
    sys.k_system = 0.002
    
    motor = Motor(rated_power_kw=15.0, nominal_efficiency=92.0, speed_rpm=1450)
    vfd = VFD(nominal_efficiency=97.0)
    drive = DriveSystem(motor, vfd)
    
    energy_analyzer = EnergyAnalysis(pump, sys, fluid, drive, energy_cost_per_kwh=0.12)
    
    # Profile:
    # 4000 hours at 50Hz (Full speed)
    # 4000 hours at 40Hz (Reduced speed via VFD)
    # 760 hours off
    
    periods = [
        DemandPeriod(duration_hours=4000, required_flow_m3h=0, frequency_hz=50.0),
        DemandPeriod(duration_hours=4000, required_flow_m3h=0, frequency_hz=40.0)
    ]
    
    res = energy_analyzer.evaluate_profile(periods)
    
    print("Energy Analysis Results:")
    print(json.dumps(res, indent=2))
    print(f"\nTotal Annual Cost: ${res['total_cost']:,.2f}")

if __name__ == "__main__":
    main()
