import subprocess
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn, TimeElapsedColumn
from rich.live import Live

console = Console()

def run_script(script_path, progress, task_id, name):
    script_name = script_path.name
    progress.update(task_id, description=f"[yellow]Starting {name}...")
    
    try:
        process = subprocess.Popen(
            [sys.executable, str(script_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        output_lines = []
        for line in iter(process.stdout.readline, ""):
            line = line.strip()
            if not line:
                continue
            output_lines.append(line)
            if line.startswith("[WORKING]"):
                current_file = line.replace("[WORKING]", "").strip()
                progress.update(task_id, description=f"[cyan]{name}: [white]{current_file}")
            elif line.startswith("[PROGRESS]"):
                try:
                    perc = float(line.replace("[PROGRESS]", "").strip())
                    progress.update(task_id, completed=perc)
                except:
                    pass
            else:
                # Stream other output to console for debugging
                console.print(f"  [dim]{line}[/dim]")
            
        returncode = process.wait()
        
        if returncode == 0:
            progress.update(task_id, description=f"[green]Completed {name}", completed=100)
            return True
        else:
            progress.update(task_id, description=f"[red]Failed {name}")
            console.print(f"\n[bold red]Error in {name}:[/bold red]")
            # Print the last 15 lines of output to show the traceback
            for line in output_lines[-15:]:
                console.print(f"  [dim]{line}[/dim]")
            return False
    except Exception as e:
        progress.update(task_id, description=f"[red]Error: {str(e)}")
        return False

def main():
    root_dir = Path(__file__).parent
    scripts_dir = root_dir / "scripts"
    
    pipeline_scripts = [
        ("Triage", scripts_dir / "run_triage.py"),
        ("Extraction", scripts_dir / "run_extraction.py"),
        ("Chunking", scripts_dir / "run_chunking.py"),
        ("Indexing", scripts_dir / "run_indexing.py")
    ]
    
    console.print(Panel.fit(
        "[bold blue]DOCUMENT INTELLIGENCE REFINERY[/bold blue]\n"
        "[dim]Full Agentic Pipeline Orchestrator[/dim]",
        border_style="blue"
    ))
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeRemainingColumn(),
        TimeElapsedColumn(),
        console=console,
        transient=False
    ) as progress:
        
        overall_task = progress.add_task("[bold white]Overall Progress", total=len(pipeline_scripts))
        
        for name, script in pipeline_scripts:
            if not script.exists():
                console.print(f"[bold red]ERROR:[/bold red] Script not found: {script}")
                sys.exit(1)
            
            step_task = progress.add_task(f"[cyan]Pending: {name}", total=100)
            success = run_script(script, progress, step_task, name)
            
            if not success:
                console.print(f"\n[bold red]FATAL:[/bold red] Pipeline stopped due to failure in {name}")
                sys.exit(1)
            
            progress.advance(overall_task)
            
    print("\n" + "=" * 60)
    console.print("[bold green]PIPELINE EXECUTION COMPLETE[/bold green]".center(60))
    print("=" * 60)

if __name__ == "__main__":
    main()
