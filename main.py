import os
import sys
import subprocess
import time
import json
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align
from rich.prompt import Prompt, IntPrompt
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.tree import Tree
from src.agents.query_agent import QueryInterfaceAgent

console = Console()

BANNER = """
[bold cyan]
██████╗  ██████╗  ██████╗    ██████╗ ███████╗███████╗██╗███╗   ██╗███████╗██████╗ ██╗   ██╗
██╔══██╗██╔═══██╗██╔════╝    ██╔══██╗██╔════╝██╔════╝██║████╗  ██║██╔════╝██╔══██╗╚██╗ ██╔╝
██║  ██║██║   ██║██║         ██████╔╝█████╗  █████╗  ██║██╔██╗ ██║█████╗  ██████╔╝ ╚████╔╝ 
██║  ██║██║   ██║██║         ██╔══██╗██╔══╝  ██╔══╝  ██║██║╚██╗██║██╔══╝  ██╔══██╗  ╚██╔╝  
██████╔╝╚██████╔╝╚██████╗    ██║  ██║███████╗██║     ██║██║ ╚████║███████╗██║  ██║   ██║   
╚═════╝  ╚═════╝  ╚═════╝    ╚═╝  ╚═╝╚══════╝╚═╝     ╚═╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝   ╚═╝   
[/bold cyan]
[bold white]                         DOCUMENT INTELLIGENCE REFINERY v1.0[/bold white]
"""

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def show_header():
    clear_screen()
    console.print(Align.center(BANNER))
    console.print(Align.center("[italic dim]Forward Deployed Engineering - 10 Academy Week 3 Challenge[/italic dim]"))
    console.print()

def run_pipeline():
    show_header()
    console.print(Panel("[bold yellow]STARTING PIPELINE SCAN...[/bold yellow]\n[dim]Initializing Triage, Extraction, Chunking, and Indexing stages.[/dim]", border_style="yellow"))
    
    # Run run_pipeline.py as a subprocess and stream output
    process = subprocess.Popen(
        [sys.executable, "run_pipeline.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    for line in iter(process.stdout.readline, ""):
        line_strip = line.strip()
        if not line_strip or "[PROGRESS]" in line:
            continue
            
        # FILTER NOISE (RapidOCR/ONNX/Docling internal logs)
        noise_keywords = ["RapidOCR", "onnxruntime", "detection result is empty", "File exists and is valid", "Using engine_name"]
        if any(k in line_strip for k in noise_keywords):
            continue
            
        console.print(f"  [dim]│[/dim] {line_strip}")
    
    process.wait()
    console.print("\n[bold green]PIPELINE SCAN COMPLETE![/bold green]")
    Prompt.ask("\nPress [bold]Enter[/bold] to return to menu")

def query_interface():
    while True:
        show_header()
        indexes_path = Path(".refinery/indexes")
        if not indexes_path.exists():
            console.print("[bold red]No indexed documents found. Please run the Pipeline Scan first.[/bold red]")
            time.sleep(2)
            break
            
        docs = list(indexes_path.glob("*.json"))
        if not docs:
            console.print("[bold red]No indexed documents found. Please run the Pipeline Scan first.[/bold red]")
            time.sleep(2)
            break

        table = Table(title="[bold cyan]Available Intel Sources[/bold cyan]", box=None)
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Document Name", style="white")
        
        doc_list = []
        for i, doc in enumerate(docs):
            doc_name = doc.stem
            doc_list.append(doc_name)
            table.add_row(f"[{i+1}]", doc_name)
        
        console.print(table)
        console.print("\n[dim]Enter [bold]0[/bold] to return to main menu[/dim]")
        
        choice = IntPrompt.ask("\n[bold]Select Document ID[/bold]", default=0)
        if choice == 0:
            break
        
        if 1 <= choice <= len(doc_list):
            selected_doc = doc_list[choice-1]
            start_chat(selected_doc)
        else:
            console.print("[bold red]Invalid selection.[/bold red]")
            time.sleep(1)

def start_chat(doc_id):
    agent = QueryInterfaceAgent(doc_id)
    show_header()
    console.print(Panel(f"[bold green]Connected to Intelligence Agent[/bold green]\n[cyan]Source:[/cyan] {doc_id}", border_style="green"))
    console.print("[dim]Ask anything about this document. Type 'exit' or 'back' to leave.[/dim]\n")
    
    while True:
        query = Prompt.ask("[bold cyan]Query[/bold cyan]")
        if query.lower() in ["exit", "back", "quit"]:
            break
            
        with console.status("[italic cyan]Searching indexes and auditing claims...[/italic cyan]"):
            try:
                answer = agent.run_query(query)
                console.print(f"\n[bold green]REFINERY ANSWER:[/bold green]")
                console.print(Panel(answer, border_style="blue"))
            except Exception as e:
                console.print(f"[bold red]System Error:[/bold red] {str(e)}")
        console.print()

def main_menu():
    while True:
        show_header()
        
        menu = Table.grid(padding=1)
        menu.add_column(style="cyan", justify="right")
        menu.add_column(style="white")
        
        menu.add_row("[1]", "Refine Documents (Start Pipeline Scan)")
        menu.add_row("[2]", "Query Intelligence Agent (Q&A Interface)")
        menu.add_row("[3]", "Review Extraction Artifacts (Demo Browser)")
        menu.add_row("[4]", "Guided Demo Walkthrough (Step-by-Step Recording Mode)")
        menu.add_row("[x]", "Exit Refinery")
        
        console.print(Panel(menu, title="[bold white]MAIN DASHBOARD[/bold white]", border_style="cyan", expand=False))
        
        choice = Prompt.ask("\n[bold]Command[/bold]", choices=["1", "2", "3", "4", "x"], default="1")
        
        if choice == "1":
            run_pipeline()
        elif choice == "2":
            query_interface()
        elif choice == "3":
            demo_artifacts_viewer()
        elif choice == "4":
            interactive_demo_walkthrough()
        elif choice == "x":
            console.print("\n[bold yellow]Shutting down Refinery... Goodbye.[/bold yellow]")
            break

def demo_artifacts_viewer():
    while True:
        show_header()
        menu = Table.grid(padding=1)
        menu.add_column(style="green")
        menu.add_row("[1]", "View Triage Profiles (Step 1)")
        menu.add_row("[2]", "View Extraction Ledger (Step 2)")
        menu.add_row("[3]", "Visualize PageIndex Tree (Step 3)")
        menu.add_row("[0]", "Back to Main Menu")
        
        console.print(Panel(menu, title="[bold white]ARTEFACT BROWSER[/bold white]", border_style="green", expand=False))
        choice = Prompt.ask("\n[bold]Select Artifact[/bold]", choices=["1", "2", "3", "0"], default="1")
        
        if choice == "1":
            view_triage_profiles()
        elif choice == "2":
            view_extraction_ledger()
        elif choice == "3":
            visualize_page_index()
        elif choice == "0":
            break

def view_triage_profiles():
    profiles = list(Path(".refinery/profiles").glob("*.json"))
    if not profiles:
        console.print("[red]No profiles found.[/red]")
        time.sleep(1)
        return
        
    for p in profiles:
        with open(p, "r") as f:
            data = json.load(f)
            console.print(Panel(
                f"[bold cyan]Document:[/bold cyan] {data['filename']}\n"
                f"[bold yellow]Classification:[/bold yellow] {data['origin_type']} | {data['layout_complexity']}\n"
                f"[bold green]Suggested Strategy:[/bold green] {data['extraction_cost']}",
                title=f"Profile: {data['doc_id']}"
            ))
    Prompt.ask("\nPress Enter to return")

def view_extraction_ledger():
    ledger_path = Path("extraction_ledger.jsonl")
    if not ledger_path.exists():
        console.print("[red]Ledger not found. Run pipeline first.[/red]")
        time.sleep(1)
        return
        
    table = Table(title="Extraction Ledger")
    table.add_column("Doc ID")
    table.add_column("Strategy", style="yellow")
    table.add_column("Cost", style="green")
    table.add_column("Tables", justify="right")
    
    with open(ledger_path, "r") as f:
        for line in f:
            d = json.loads(line)
            table.add_row(d['doc_id'], d['final_strategy'], f"${d['total_cost_usd']:.4f}", str(d['tables_found']))
            
    console.print(table)
    Prompt.ask("\nPress Enter to return")

def visualize_page_index():
    indexes = list(Path(".refinery/indexes").glob("*.json"))
    if not indexes:
        console.print("[red]No indexes found.[/red]")
        time.sleep(1)
        return
        
    for i, idx in enumerate(indexes):
        console.print(f"[{i+1}] {idx.stem}")
    choice = IntPrompt.ask("Select index to visualize", default=1)
    
    if 1 <= choice <= len(indexes):
        target = indexes[choice-1]
        with open(target, "r") as f:
            try:
                data = json.load(f)
                tree = Tree(f":file_folder: [bold blue]{data['doc_id']} PageIndex")
                
                def add_nodes(parent_tree, nodes):
                    for node in nodes:
                        p_start = node.get('page_start', '?')
                        p_end = node.get('page_end', '?')
                        pg_suffix = f" (Pg {p_start}-{p_end})" if p_start != p_end else f" (Pg {p_start})"
                        
                        branch_label = f":page_facing_up: [cyan]{node['title']}[/cyan] [dim]{pg_suffix}[/dim]"
                        branch = parent_tree.add(branch_label)
                        
                        if node.get('child_nodes'):
                            add_nodes(branch, node['child_nodes'])
                
                add_nodes(tree, data['root_nodes'])
                console.print(tree)
            except Exception as e:
                console.print(f"[red]Failed to parse index: {e}[/red]")
        Prompt.ask("\nPress Enter to return")

def run_single_step(name, script_name, file_arg):
    console.print(Panel(f"[bold yellow]Executing Stage: {name}...[/bold yellow]", border_style="yellow"))
    process = subprocess.Popen(
        [sys.executable, f"scripts/{script_name}", "--file", file_arg],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    for line in iter(process.stdout.readline, ""):
        line_strip = line.strip()
        if not line_strip:
            continue
            
        # FILTER NOISE (RapidOCR/ONNX/Docling internal logs)
        noise_keywords = ["RapidOCR", "onnxruntime", "detection result is empty", "File exists and is valid", "Using engine_name"]
        if any(k in line_strip for k in noise_keywords):
            continue
            
        console.print(f"  [dim]│[/dim] {line_strip}")
    process.wait()
    if process.returncode == 0:
        console.print(f"\n[bold green]✅ Stage {name} Complete![/bold green]")
    else:
        console.print(Panel(f"[bold red]❌ Stage {name} Failed![/bold red]\n[dim]Process exited with code {process.returncode}. Check logs above.[/dim]", border_style="red"))
        Prompt.ask("\nPress Enter to return to menu (or continue at your own risk)")

def interactive_demo_walkthrough():
    show_header()
    data_dir = Path("data")
    files = list(data_dir.glob("*.pdf"))
    
    if not files:
        console.print("[red]No PDF files found in 'data/' directory.[/red]")
        time.sleep(2)
        return
        
    table = Table(title="Select PDF for Guided Demo", box=None)
    table.add_column("ID", style="cyan")
    table.add_column("File Name")
    
    for i, f in enumerate(files):
        table.add_row(f"[{i+1}]", f.name)
        
    console.print(table)
    choice = IntPrompt.ask("\nSelect File ID", default=1)
    
    if not (1 <= choice <= len(files)):
        return
        
    selected_file = files[choice-1].name
    doc_id = files[choice-1].stem
    
    # STEP 1: TRIAGE
    show_header()
    console.print(Panel("[bold white]🎬 STEP 1: THE TRIAGE[/bold white]\n[dim]'Drop' the document into the pipeline and see the profile.[/dim]", border_style="blue"))
    
    console.print(Panel(
        "First, we drop the raw PDF into our [bold cyan]Triage Agent[/bold cyan]. Instead of just starting a heavy extraction, "
        "the system 'profiles' the document. It detects if the PDF is scanned (requiring heavy OCR) or native text. "
        "It also analyzes layout complexity—looking for dense tables or multi-column grids.",
        border_style="dim"
    ))
    
    run_single_step("Triage", "run_triage.py", selected_file)
    # Automatically show the profile
    profile_path = Path(".refinery/profiles") / f"{doc_id}.json"
    if profile_path.exists():
        with open(profile_path, "r") as f:
            data = json.load(f)
            console.print("\n[bold cyan]DOCUMENT PROFILE RESULT:[/bold cyan]")
            console.print(Panel(
                f"[bold cyan]File:[/bold cyan] {data['filename']}\n"
                f"[bold yellow]Type:[/bold yellow] {data['origin_type']}\n"
                f"[bold green]Suggested Strategy:[/bold green] {data['extraction_cost']}\n"
                f"[bold white]Reasoning:[/bold white] {data['layout_complexity']}",
                border_style="cyan"
            ))
            
            console.print(Panel(
                "[dim]Efficiency Insight:[/dim] This stage saves costs by only using expensive Vision models when absolutely necessary.",
                border_style="green"
            ))
    Prompt.ask("\n[bold]Ready for Step 2: Extraction?[/bold] (Press Enter)")

    # STEP 2: EXTRACTION
    show_header()
    console.print(Panel("[bold white]🎬 STEP 2: THE EXTRACTION[/bold white]\n[dim]Extracting structured data and updating the ledger.[/dim]", border_style="blue"))
    
    console.print(Panel(
        "Next, we run the [bold cyan]Extraction Stage[/bold cyan]. We're using [bold white]Docling[/bold white] combined with a robust escalation router. "
        "Our strategy meticulously parses the PDF coordinates. It doesn't just 'scrape' text; it [bold green]reconstructs table headers and values[/bold green] into structured JSON.",
        border_style="dim"
    ))
    
    run_single_step("Extraction", "run_extraction.py", doc_id)
    # Show Ledger Entry
    ledger_path = Path("extraction_ledger.jsonl")
    if ledger_path.exists():
        console.print("\n[bold yellow]EXTRACTION LEDGER UPDATE:[/bold yellow]")
        with open(ledger_path, "r") as f:
            lines = f.readlines()
            for line in lines:
                if doc_id in line:
                    d = json.loads(line)
                    console.print(f"  [green]• Strategy:[/green] {d['final_strategy']}")
                    console.print(f"  [green]• Cost:[/green] ${d['total_cost_usd']:.4f}")
                    console.print(f"  [green]• Tables Found:[/green] {d['tables_found']}")
                    break
            
            console.print(Panel(
                "[dim]Accuracy Insight:[/dim] Reconstructing tables into JSON allows us to query them logically and reliably later.",
                border_style="green"
            ))
    Prompt.ask("\n[bold]Ready for Step 3: PageIndex Tree?[/bold] (Press Enter)")

    # STEP 3: PAGEINDEX
    show_header()
    console.print(Panel("[bold white]🎬 STEP 3: THE PAGEINDEX[/bold white]\n[dim]Building the hierarchical navigation tree.[/dim]", border_style="blue"))
    
    console.print(Panel(
        "Now we generate the [bold cyan]PageIndex[/bold cyan]. Unlike a simple search index, this builds a hierarchical tree of the document's structure. "
        "It uses an LLM to summarize each chapter and section into a single sentence. This tree allows us to navigate the document's 'mental map' "
        "without even performing a vector search. It's essentially an [bold green]automated, intelligent table of contents[/bold green].",
        border_style="dim"
    ))
    
    run_single_step("Chunking", "run_chunking.py", doc_id)
    run_single_step("Indexing", "run_indexing.py", doc_id)
    # Show Tree
    index_path = Path(".refinery/indexes") / f"{doc_id}.json"
    if index_path.exists():
        console.print("\n[bold blue]PAGEINDEX TREE:[/bold blue]")
        with open(index_path, "r") as f:
            data = json.load(f)
            tree = Tree(f":file_folder: [bold blue]{data['doc_id']} Index")
            def add_nodes(pt, nodes):
                for n in nodes:
                    p_start = n.get('page_start', '?')
                    p_end = n.get('page_end', '?')
                    pg_info = f" [dim](Pg {p_start}-{p_end})[/dim]" if p_start != p_end else f" [dim](Pg {p_start})[/dim]"
                    
                    b = pt.add(f":page_facing_up: [cyan]{n['title']}[/cyan]{pg_info}")
                    if n.get('child_nodes'): add_nodes(b, n['child_nodes'])
            add_nodes(tree, data['root_nodes'])
            console.print(tree)
            
            console.print(Panel(
                "[dim]Context Insight:[/dim] This provides the Query Agent a structured way to 'browse' the document before generating answers.",
                border_style="green"
            ))
    Prompt.ask("\n[bold]Ready for Step 4: Final Query?[/bold] (Press Enter)")

    # STEP 4: QUERY
    show_header()
    console.print(Panel(
        "Finally, let's ask a question. The [bold cyan]Intelligence Agent[/bold cyan] uses our PageIndex to find the exact location and then generates a verified answer. "
        "Most importantly, look at the [bold green]Provenance Chain[/bold green]—it doesn't just give an answer; it provides a 'citation' with the specific page and bounding box.",
        border_style="dim"
    ))
    
    console.print(Panel(
        "[dim]Trust Insight:[/dim] Provenance eliminates LLM hallucinations by forcing the model to cite its sources explicitly.",
        border_style="green"
    ))
    Prompt.ask("\n[bold]Ready to enter the Q&A Interface?[/bold] (Press Enter)")
    
    start_chat(doc_id)

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        console.print("\n\n[bold yellow]Refinery session interrupted.[/bold yellow]")
        sys.exit(0)
