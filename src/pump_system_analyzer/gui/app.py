import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from pathlib import Path

from pump_system_analyzer.core.fluid import Water
from pump_system_analyzer.core.curve import Curve, CurveData
from pump_system_analyzer.core.pump import Pump, PumpMetadata
from pump_system_analyzer.core.system import HydraulicSystem
from pump_system_analyzer.core.solver import Solver

st.set_page_config(page_title="Pump System Analyzer", layout="wide")

st.title("Pump System Analyzer")
st.markdown("Analyze, compare, and optimize pump systems with traceable calculations.")

# --- Sidebar Configuration ---
st.sidebar.header("Configuration")

# 1. Fluid
st.sidebar.subheader("Fluid")
temp_c = st.sidebar.slider("Temperature (°C)", min_value=0.0, max_value=100.0, value=20.0, step=1.0)
fluid = Water(temp_c)
st.sidebar.caption(f"Density: {fluid.density:.1f} kg/m³")
st.sidebar.caption(f"Viscosity: {fluid.viscosity:.2e} Pa·s")
st.sidebar.caption(f"Vapor Press: {fluid.vapor_pressure:.0f} Pa")

# 2. System
st.sidebar.subheader("System")
static_head = st.sidebar.number_input("Static Head (m)", value=15.0, step=1.0)
k_loss = st.sidebar.number_input("System Resistance K", value=0.002, format="%.5f", step=0.0001)
sys = HydraulicSystem(static_head=static_head)
sys.k_system = k_loss

# 3. Pump (Demo for now)
st.sidebar.subheader("Pump Operation")
speed_freq = st.sidebar.slider("VFD Frequency (Hz)", min_value=20.0, max_value=60.0, value=50.0, step=1.0)
nominal_freq = 50.0

# Base Pump
base_pump = Pump(
    h_curve=Curve(CurveData(x=[0, 20, 40, 60, 80, 100, 120], y=[45, 44, 42, 38, 32, 23, 10]), name="Catalog Head"),
    eff_curve=Curve(CurveData(x=[0, 20, 40, 60, 80, 100, 120], y=[0, 30, 55, 70, 78, 75, 50]), name="Efficiency"),
    power_curve=Curve(CurveData(x=[0, 20, 40, 60, 80, 100, 120], y=[4.0, 5.0, 6.2, 7.5, 8.5, 9.1, 9.0]), name="Power"),
    npshr_curve=Curve(CurveData(x=[0, 20, 40, 60, 80, 100, 120], y=[1.5, 1.5, 1.8, 2.5, 3.8, 5.5, 8.0]), name="NPSHr"),
    metadata=PumpMetadata(speed_rpm=1450, manufacturer="Demo Pumps")
)

# Apply Affinity Laws if speed changed
speed_ratio = speed_freq / nominal_freq
current_speed = base_pump.metadata.speed_rpm * speed_ratio
pump = base_pump.get_affinity_pump(current_speed)

# --- Analysis ---
try:
    op = Solver.solve(pump, sys, fluid)
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Operating Flow", f"{op.q:.1f} m³/h")
    col2.metric("Operating Head", f"{op.h:.1f} m")
    if op.eff:
        col3.metric("Efficiency", f"{op.eff:.1f} %")
    if op.power_shaft:
        col4.metric("Shaft Power", f"{op.power_shaft:.1f} kW")
        
    # --- Plotting ---
    st.subheader("Performance Curves")
    
    q_plot = np.linspace(0, pump.h_curve.x_max * 1.1, 200)
    
    fig = go.Figure()
    
    # Base Curve (for reference if speed changed)
    if speed_ratio != 1.0:
        fig.add_trace(go.Scatter(x=base_pump.h_curve.raw_data.x, y=base_pump.h_curve.raw_data.y, 
                                 mode='lines', line=dict(dash='dot', color='gray'), name="Base Curve (50 Hz)"))
    
    # Actual Pump Curve
    try:
        h_vals = pump.h_curve(q_plot)
        fig.add_trace(go.Scatter(x=q_plot, y=h_vals, mode='lines', line=dict(color='blue', width=3), name=f"Pump H-Q ({speed_freq} Hz)"))
    except ValueError:
         st.warning("Plotting hit extrapolation limit for pump curve.")
         
    # System Curve
    sys_h = sys(q_plot)
    fig.add_trace(go.Scatter(x=q_plot, y=sys_h, mode='lines', line=dict(color='orange', width=2), name="System Curve"))
    
    # Operating Point
    fig.add_trace(go.Scatter(x=[op.q], y=[op.h], mode='markers', marker=dict(color='red', size=12, symbol='x'), name="Operating Point"))
    
    fig.update_layout(
        xaxis_title="Flow Rate (m³/h)",
        yaxis_title="Head (m)",
        hovermode="x unified",
        template="plotly_white",
        height=600
    )
    
    st.plotly_chart(fig, use_container_width=True)

    # Secondary plots: Power and Efficiency
    col_p, col_e = st.columns(2)
    with col_p:
        st.subheader("Power")
        fig_p = go.Figure()
        if pump.power_curve:
            p_vals = pump.power_curve(q_plot)
            fig_p.add_trace(go.Scatter(x=q_plot, y=p_vals, mode='lines', line=dict(color='green'), name="Shaft Power"))
            if op.power_shaft:
                fig_p.add_trace(go.Scatter(x=[op.q], y=[op.power_shaft], mode='markers', marker=dict(color='red', size=10), name="Op Point"))
        fig_p.update_layout(xaxis_title="Flow", yaxis_title="Power (kW)", template="plotly_white")
        st.plotly_chart(fig_p, use_container_width=True)
        
    with col_e:
        st.subheader("Efficiency")
        fig_e = go.Figure()
        if pump.eff_curve:
            e_vals = pump.eff_curve(q_plot)
            fig_e.add_trace(go.Scatter(x=q_plot, y=e_vals, mode='lines', line=dict(color='purple'), name="Efficiency"))
            if op.eff:
                fig_e.add_trace(go.Scatter(x=[op.q], y=[op.eff], mode='markers', marker=dict(color='red', size=10), name="Op Point"))
        fig_e.update_layout(xaxis_title="Flow", yaxis_title="Efficiency (%)", template="plotly_white")
        st.plotly_chart(fig_e, use_container_width=True)

except Exception as e:
    st.error(f"Error in analysis: {e}")
