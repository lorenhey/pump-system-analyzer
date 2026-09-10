from pump_system_analyzer.core.fluid import Fluid, Water
from pump_system_analyzer.core.curve import Curve, CurveData
from pump_system_analyzer.core.pump import Pump, PumpMetadata
from pump_system_analyzer.core.valves import ControlValve
from pump_system_analyzer.core.system import HydraulicSystem
from pump_system_analyzer.core.solver import Solver
from pump_system_analyzer.core.viscosity import ViscosityCorrection

def main():
    print("--- 1. Impeller Trimming ---")
    q_data = [0, 20, 40, 60, 80, 100, 120]
    h_data = [45, 44, 42, 38, 32, 23, 10]
    eff_data = [0, 30, 55, 70, 78, 75, 50]
    
    base_pump = Pump(
        h_curve=Curve(CurveData(x=q_data, y=h_data), name="Pump"),
        eff_curve=Curve(CurveData(x=q_data, y=eff_data), name="Efficiency"),
        metadata=PumpMetadata(speed_rpm=1450, impeller_diameter=250.0)
    )
    
    trimmed_pump = base_pump.get_trimmed_pump(new_diameter=230.0)
    print(f"Base Pump H at 60 m3/h: {base_pump.h_curve(60):.2f} m")
    print(f"Trimmed Pump H at 60 m3/h: {trimmed_pump.h_curve(60):.2f} m")
    
    print("\n--- 2. Control Valve vs VFD ---")
    sys = HydraulicSystem(static_head=15.0)
    sys.k_system = 0.002
    
    valve = ControlValve(name="Discharge Valve", kv_max=100.0, characteristic="equal_percentage")
    sys.add_control_valve(valve, opening_fraction=0.5)
    
    op_throttled = Solver.solve(base_pump, sys, Water(20))
    p_throttle = f"{op_throttled.power_shaft:.1f} kW" if op_throttled.power_shaft else "N/A"
    print(f"Throttled to 50% Valve: Q = {op_throttled.q:.1f} m3/h, H = {op_throttled.h:.1f} m, Power = {p_throttle}")
    
    # Remove valve, use VFD
    sys.control_valves.clear()
    # Let's say we want to hit the same flow
    # Simple affinity logic: H_req = sys(op_throttled.q)
    # We can just manually search or let's just pick a slower speed:
    slower_pump = base_pump.get_affinity_pump(1450 * 0.8)
    op_vfd = Solver.solve(slower_pump, sys, Water(20))
    p_vfd = f"{op_vfd.power_shaft:.1f} kW" if op_vfd.power_shaft else "N/A"
    print(f"VFD at 80% speed: Q = {op_vfd.q:.1f} m3/h, H = {op_vfd.h:.1f} m, Power = {p_vfd}")
    
    print("\n--- 3. Viscosity Correction ---")
    # Simulate a highly viscous fluid (e.g. heavy oil)
    oil = Fluid(name="Heavy Oil", density=900.0, viscosity=0.5) # 0.5 Pa.s -> ~550 cSt
    visc_pump = ViscosityCorrection.apply_fluid(base_pump, oil)
    
    print(f"Base Pump (Water) at BEP ({base_pump.bep_q:.1f} m3/h): H = {base_pump.bep_h:.1f} m")
    if visc_pump.bep_q:
        print(f"Viscous Pump (Oil) at new BEP ({visc_pump.bep_q:.1f} m3/h): H = {visc_pump.bep_h:.1f} m")
    else:
        # Just evaluate at base BEP
        print(f"Viscous Pump (Oil) at base BEP flow: H = {visc_pump.h_curve(base_pump.bep_q):.1f} m")

if __name__ == "__main__":
    main()
