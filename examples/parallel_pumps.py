from pathlib import Path
from pump_system_analyzer.core.fluid import Water
from pump_system_analyzer.core.curve import Curve, CurveData
from pump_system_analyzer.core.pump import Pump, PumpMetadata
from pump_system_analyzer.core.configurations import PumpConfiguration
from pump_system_analyzer.core.system import HydraulicSystem
from pump_system_analyzer.core.solver import Solver

def main():
    fluid = Water(20)
    
    # Define a base pump
    q_data = [0, 20, 40, 60, 80, 100, 120]
    h_data = [45, 44, 42, 38, 32, 23, 10]
    
    base_pump = Pump(
        h_curve=Curve(CurveData(x=q_data, y=h_data), name="Pump A"),
        metadata=PumpMetadata(speed_rpm=1450)
    )
    
    # Create a parallel configuration of 2 identical pumps
    parallel_pump = PumpConfiguration.parallel([base_pump, base_pump], name="2x Pump A (Parallel)")
    
    # Define system
    sys = HydraulicSystem(static_head=20.0)
    sys.k_system = 0.0015
    
    # Solve for 1 pump
    op1 = Solver.solve(base_pump, sys, fluid)
    print(f"Single Pump Operating Point: Q = {op1.q:.1f} m3/h, H = {op1.h:.1f} m")
    
    # Solve for 2 pumps in parallel
    op2 = Solver.solve(parallel_pump, sys, fluid)
    print(f"Two Pumps Parallel Operating Point: Q = {op2.q:.1f} m3/h, H = {op2.h:.1f} m")
    
    print(f"\nNotice that Q_parallel ({op2.q:.1f}) is less than 2 * Q_single ({2*op1.q:.1f}) because system friction increases with flow.")

if __name__ == "__main__":
    main()
