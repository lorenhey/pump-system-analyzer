import typer
from rich.console import Console
from rich.table import Table

console = Console()
app = typer.Typer(help="Pump System Analyzer CLI")

@app.command()
def demo():
    """Runs a flagship demo to showcase the tool's capabilities."""
    console.print("[bold green]Starting Pump System Analyzer Demo...[/bold green]")
    from pump_system_analyzer.core.fluid import Water
    from pump_system_analyzer.core.curve import Curve, CurveData
    from pump_system_analyzer.core.pump import Pump, PumpMetadata
    from pump_system_analyzer.core.system import HydraulicSystem
    from pump_system_analyzer.core.solver import Solver
    
    fluid = Water(20.0)
    
    pump = Pump(
        h_curve=Curve(CurveData(x=[0, 20, 40, 60, 80, 100, 120], 
                                y=[45, 44, 42, 38, 32, 23, 10]), name="Demo Pump"),
        eff_curve=Curve(CurveData(x=[0, 20, 40, 60, 80, 100, 120], 
                                  y=[0, 30, 55, 70, 78, 75, 50]), name="Demo Eff"),
        power_curve=Curve(CurveData(x=[0, 20, 40, 60, 80, 100, 120], 
                                    y=[4.0, 5.0, 6.2, 7.5, 8.5, 9.1, 9.0]), name="Demo Power"),
        npshr_curve=Curve(CurveData(x=[0, 20, 40, 60, 80, 100, 120], 
                                    y=[1.5, 1.5, 1.8, 2.5, 3.8, 5.5, 8.0]), name="Demo NPSHr"),
        metadata=PumpMetadata(speed_rpm=1450, manufacturer="OpenSource Pumps")
    )
    
    sys = HydraulicSystem(static_head=15.0)
    sys.k_system = 0.002 # H = 15 + 0.002*Q^2
    
    console.print(f"\n[bold]Fluid:[/bold] {fluid.name}, Density={fluid.density:.1f} kg/m³, Viscosity={fluid.viscosity:.2e} Pa·s")
    console.print(f"[bold]System:[/bold] Static Head = {sys.static_head} m, K = {sys.k_system}")
    
    try:
        op = Solver.solve(pump, sys, fluid)
        console.print("\n[bold green]Operating Point Found:[/bold green]")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Parameter", style="dim")
        table.add_column("Value")
        
        table.add_row("Flow (Q)", f"{op.q:.1f} m³/h")
        table.add_row("Head (H)", f"{op.h:.1f} m")
        if op.eff:
            table.add_row("Efficiency (eta)", f"{op.eff:.1f} %")
            if pump.bep_q:
                bep_ratio = op.q / pump.bep_q
                table.add_row("Q / Q_BEP", f"{bep_ratio:.2f}")
        if op.power_shaft:
            table.add_row("Shaft Power", f"{op.power_shaft:.1f} kW")
        if op.npshr:
            table.add_row("NPSHr", f"{op.npshr:.1f} m")
            
        console.print(table)
        
    except Exception as e:
        console.print(f"[bold red]Error solving for operating point:[/bold red] {e}")

@app.command()
def analyze(project_file: str):
    """Analyzes a full project from a YAML definition."""
    console.print(f"[bold blue]Loading project from {project_file}...[/bold blue]")
    
    from pump_system_analyzer.core.project import Project
    from pathlib import Path
    
    if not Path(project_file).exists():
        console.print(f"[bold red]File not found: {project_file}[/bold red]")
        raise typer.Exit(1)
        
    try:
        project = Project.from_yaml(project_file)
        console.print(f"[green]Project loaded successfully.[/green]")
        console.print(f"Fluid: {project.fluid.name} @ {project.fluid.temperature - 273.15:.1f} °C")
        console.print(f"Pump: {project.pump.metadata.manufacturer} - {project.pump.metadata.model} @ {project.pump.metadata.speed_rpm} RPM")
        console.print(f"System: Static Head = {project.system.static_head:.2f} m, K = {project.system.k_system:.4f}\n")
        
        op = project.analyze()
        
        console.print("[bold green]Operating Point Found:[/bold green]")
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Parameter", style="dim")
        table.add_column("Value")
        
        table.add_row("Flow (Q)", f"{op.q:.2f} m³/h")
        table.add_row("Head (H)", f"{op.h:.2f} m")
        
        if op.eff:
            table.add_row("Efficiency (eta)", f"{op.eff:.1f} %")
            if project.pump.bep_q:
                table.add_row("Q / Q_BEP", f"{op.q / project.pump.bep_q:.2f}")
        
        if op.power_shaft:
            table.add_row("Shaft Power", f"{op.power_shaft:.2f} kW")
            
        if op.npshr:
            table.add_row("NPSHr", f"{op.npshr:.2f} m")
            
        console.print(table)
        
        # Export manifest if requested
        import json
        manifest = op.export_manifest()
        manifest_path = Path("analysis-manifest.json")
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)
        console.print(f"[dim]Analysis manifest written to {manifest_path}[/dim]")
        
    except Exception as e:
        console.print(f"[bold red]Analysis failed:[/bold red] {e}")
        raise typer.Exit(1)

@app.command()
def gui():
    """Launches the interactive local technical interface."""
    import subprocess
    from pathlib import Path
    import pump_system_analyzer
    
    # Find the path to the app.py file
    pkg_dir = Path(pump_system_analyzer.__file__).parent
    app_path = pkg_dir / "gui" / "app.py"
    
    console.print(f"[bold green]Starting local GUI...[/bold green]")
    try:
        subprocess.run(["streamlit", "run", str(app_path)])
    except KeyboardInterrupt:
        console.print("\n[yellow]GUI stopped by user.[/yellow]")
    except Exception as e:
        console.print(f"[bold red]Failed to start GUI:[/bold red] {e}")

if __name__ == "__main__":
    app()
