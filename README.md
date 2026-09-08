# pump-system-analyzer

A comprehensive open-source tool for analyzing, comparing, diagnosing, and optimizing pump systems. 
It helps you move beyond nominal parameters to understand where your pump actually operates in its system.

## Features
- Complete system curve calculation (static head, friction losses)
- Pump curve interpolation (PCHIP to maintain monotonicity)
- Operating point solving ($H_{pump}(Q) = H_{sys}(Q)$)
- Variable speed analysis (Affinity laws, VFD efficiencies)
- Fluid properties (density, viscosity, vapor pressure tracking with temperature)
- NPSH calculations and margin checks
- Staging (Parallel, Series pumps)
- Field vs Catalog comparison
- Full programmatic Python API, Typer CLI, and Local Technical UI.

## Core Principle
A centrifugal pump has no single "flow rate" or "head"; it has curves. The system has its curve. 
The operating point is their intersection. This tool models the complete system.

## Status
Under construction.
