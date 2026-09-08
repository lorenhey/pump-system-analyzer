import pytest
from pump_system_analyzer.core.fluid import Water
from pump_system_analyzer.core.curve import Curve, CurveData, SystemCurve
from pump_system_analyzer.core.pump import Pump, PumpMetadata
from pump_system_analyzer.core.system import HydraulicSystem
from pump_system_analyzer.core.solver import Solver

def test_water_properties():
    w = Water(20)
    assert 997.0 < w.density < 999.0
    
def test_curve_interpolation():
    c = Curve(CurveData(x=[0, 50, 100], y=[50, 40, 20]))
    assert c(0) == pytest.approx(50)
    assert c(100) == pytest.approx(20)
    # Check intermediate
    assert 20 < c(75) < 40

def test_solver_intersection():
    w = Water(20)
    pump = Pump(h_curve=Curve(CurveData(x=[0, 50, 100], y=[50, 40, 20])))
    # System: H = 10 + K*Q^2. Let's make it intersect exactly at 50,40
    # 40 = 10 + K*(50^2) -> 30 = K*2500 -> K = 30/2500 = 0.012
    sys = HydraulicSystem(static_head=10)
    sys.k_system = 0.012
    
    op = Solver.solve(pump, sys, w)
    
    assert op.q == pytest.approx(50.0, rel=1e-3)
    assert op.h == pytest.approx(40.0, rel=1e-3)

def test_affinity_laws():
    pump = Pump(h_curve=Curve(CurveData(x=[0, 50, 100], y=[50, 40, 20])), 
                metadata=PumpMetadata(speed_rpm=1500))
    
    p2 = pump.get_affinity_pump(3000)
    # Q -> 2x, H -> 4x
    assert p2.h_curve(0) == pytest.approx(200)
    assert p2.h_curve(100) == pytest.approx(160)
    assert p2.h_curve(200) == pytest.approx(80)
