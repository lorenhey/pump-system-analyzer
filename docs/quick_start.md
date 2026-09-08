# Quick Start

Welcome to the Pump System Analyzer!

## Installation

```bash
pip install pump-system-analyzer
```

## Running the Demo

```bash
pump-system demo
```

## Launching the GUI

```bash
pump-system gui
```

## Project Format

The analyzer uses YAML to define projects:

```yaml
schema_version: 1

fluid:
  name: "Water"
  temperature_c: 25.0

pump:
  curve_file: "pump.csv"
  speed_rpm: 1450
  manufacturer: "Demo Pumps"
  model: "Model-X"

system:
  suction_elevation_m: 2.0
  suction_pressure_bara: 1.01325
  discharge_elevation_m: 15.0
  discharge_pressure_bara: 1.01325
  losses_k: 0.003
```
