import sys
import os
from src.agents.query_agent import QueryInterfaceAgent
from rich.console import Console
from rich.panel import Panel

console = Console()

def main():
    if len(sys.argv) < 3:
        console.print("[yellow]Usage: python3 scripts/ask.py <doc_id> \"your question\"[/yellow]")
        console.print("[dim]Example: python3 scripts/ask.py \"Audit Report - 2023\" \"What is the auditor's opinion?\"[/dim]")
        return

    doc_id = sys.argv[1]
    query = sys.argv[2]

    agent = QueryInterfaceAgent(doc_id)
    
    console.print(Panel(f"[bold blue]Querying:[/bold blue] {doc_id}\n[bold cyan]Question:[/bold cyan] {query}"))
    
    with console.status("[bold green]Refining answer..."):
        answer = agent.run_query(query)
    
    console.print("\n[bold green]REFINERY ANSWER:[/bold green]")
    console.print(answer)

if __name__ == "__main__":
    main()
