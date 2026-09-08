import yaml
import os
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from pathlib import Path
import pandas as pd

from pump_system_analyzer.core.fluid import Water, Fluid
from pump_system_analyzer.core.curve import Curve, CurveData
from pump_system_analyzer.core.pump import Pump, PumpMetadata
from pump_system_analyzer.core.system import HydraulicSystem
from pump_system_analyzer.core.solver import Solver, OperatingPoint
from pump_system_analyzer.core.npsh import NPSHAnalysis

class FluidDef(BaseModel):
    name: str = "Water"
    temperature_c: float = 20.0

class PumpDef(BaseModel):
    curve_file: str
    speed_rpm: float
    manufacturer: str = "Unknown"
    model: str = "Unknown"

class SystemDef(BaseModel):
    suction_elevation_m: float = 0.0
    suction_pressure_bara: float = 1.01325
    discharge_elevation_m: float = 0.0
    discharge_pressure_bara: float = 1.01325
    losses_k: float = 0.0
    static_head_override: Optional[float] = None

class ProjectDef(BaseModel):
    schema_version: int = 1
    fluid: FluidDef = FluidDef()
    pump: PumpDef
    system: SystemDef = SystemDef()

class Project:
    def __init__(self, definition: ProjectDef, base_dir: Path):
        self.definition = definition
        self.base_dir = base_dir
        
        # Initialize components
        if self.definition.fluid.name.lower() == "water":
            self.fluid = Water(temperature_c=self.definition.fluid.temperature_c)
        else:
            # Fallback to water for now if unsupported
            self.fluid = Water(temperature_c=20.0)
            
        self.pump = self._load_pump()
        self.system = self._load_system()

    def _load_pump(self) -> Pump:
        curve_path = self.base_dir / self.definition.pump.curve_file
        if not curve_path.exists():
            raise FileNotFoundError(f"Pump curve file not found: {curve_path}")
            
        # Very basic CSV loading. Expecting columns: Flow, Head, Eff, Power, NPSHr
        # We will dynamically find them based on common names.
        df = pd.read_csv(curve_path)
        df.columns = [c.strip().lower() for c in df.columns]
        
        q_col = next((c for c in df.columns if 'flow' in c or 'q' in c), None)
        h_col = next((c for c in df.columns if 'head' in c or 'h' in c), None)
        eff_col = next((c for c in df.columns if 'eff' in c or 'eta' in c), None)
        p_col = next((c for c in df.columns if 'power' in c or 'p' in c), None)
        npshr_col = next((c for c in df.columns if 'npsh' in c), None)
        
        if not q_col or not h_col:
            raise ValueError("Curve CSV must contain Flow and Head columns.")
            
        h_curve = Curve(CurveData(x=df[q_col].tolist(), y=df[h_col].tolist()), name="Head")
        
        eff_curve = None
        if eff_col:
            eff_curve = Curve(CurveData(x=df[q_col].tolist(), y=df[eff_col].tolist()), name="Efficiency")
            
        p_curve = None
        if p_col:
            p_curve = Curve(CurveData(x=df[q_col].tolist(), y=df[p_col].tolist()), name="Power")
            
        npshr_curve = None
        if npshr_col:
            npshr_curve = Curve(CurveData(x=df[q_col].tolist(), y=df[npshr_col].tolist()), name="NPSHr")

        meta = PumpMetadata(
            manufacturer=self.definition.pump.manufacturer,
            model=self.definition.pump.model,
            speed_rpm=self.definition.pump.speed_rpm
        )
        
        return Pump(h_curve, eff_curve, p_curve, npshr_curve, meta)

    def _load_system(self) -> HydraulicSystem:
        sys_def = self.definition.system
        
        static_head = sys_def.static_head_override if sys_def.static_head_override is not None else 0.0
        
        sys = HydraulicSystem(
            static_head=static_head,
            suction_pressure_pa=sys_def.suction_pressure_bara * 1e5,
            discharge_pressure_pa=sys_def.discharge_pressure_bara * 1e5,
            suction_elevation=sys_def.suction_elevation_m,
            discharge_elevation=sys_def.discharge_elevation_m,
            fluid_density=self.fluid.density
        )
        sys.add_k_loss(sys_def.losses_k)
        return sys

    def analyze(self) -> OperatingPoint:
        return Solver.solve(self.pump, self.system, self.fluid)

    @classmethod
    def from_yaml(cls, file_path: str) -> 'Project':
        path = Path(file_path)
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        definition = ProjectDef(**data)
        return cls(definition, path.parent)
