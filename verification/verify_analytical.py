"""
Verification Suite for pump-system-analyzer.
These tests verify the core engine against exact analytical solutions to ensure physical and mathematical correctness.
"""

from pump_system_analyzer.core.fluid import Fluid
from pump_system_analyzer.core.curve import Curve, CurveData
from pump_system_analyzer.core.pump import Pump, PumpMetadata
from pump_system_analyzer.core.system import HydraulicSystem
from pump_system_analyzer.core.solver import Solver

def test_linear_pump_quadratic_system():
    """
    Test a linear pump curve against a quadratic system curve where the intersection is analytically known.
    
    Pump: H = 100 - Q
    System: H = 10 + 0.1 * Q^2
    
    Intersection:
    100 - Q = 10 + 0.1 Q^2
    0.1 Q^2 + Q - 90 = 0
    Q^2 + 10Q - 900 = 0
    
    Q = (-10 + sqrt(100 - 4(1)(-900))) / 2
    Q = (-10 + sqrt(3700)) / 2
    Q = (-10 + 60.8276) / 2
    Q = 25.4138
    
    H = 100 - 25.4138 = 74.5862
    """
    fluid = Fluid(name="TestFluid", density=1000, viscosity=0.001)
    
    # Generate linear data
    q_data = [0, 50, 100]
    h_data = [100, 50, 0]
    
    pump = Pump(
        h_curve=Curve(CurveData(x=q_data, y=h_data), name="Linear Pump")
    )
    
    sys = HydraulicSystem(static_head=10.0)
    sys.k_system = 0.1
    
    op = Solver.solve(pump, sys, fluid)
    
    expected_q = 25.413812651491097
    expected_h = 74.5861873485089
    
    assert abs(op.q - expected_q) < 1e-4, f"Q mismatch: {op.q} != {expected_q}"
    assert abs(op.h - expected_h) < 1e-4, f"H mismatch: {op.h} != {expected_h}"
    
    print("Linear vs Quadratic intersection: PASS")

if __name__ == "__main__":
    test_linear_pump_quadratic_system()
