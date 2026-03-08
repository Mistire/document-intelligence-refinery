import sys
from pathlib import Path
from rich.console import Console
from tqdm import tqdm

# Add src to path so we can import models/agents
sys.path.append(str(Path(__file__).parent.parent))

from src.agents.triage import TriageAgent

console = Console()

def main():
    agent = TriageAgent()
    data_dir = Path("data")
    
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", help="Specific file to triage")
    args = parser.parse_args()
    
    # Files to process
    if args.file:
        files = [args.file]
    else:
        files = [
            "CBE ANNUAL REPORT 2023-24.pdf",
            "Audit Report - 2023.pdf",
            "fta_performance_survey_final_report_2022.pdf",
            "tax_expenditure_ethiopia_2021_22.pdf"
        ]
    
    total = len(files)
    for i, filename in enumerate(files):
        # Progress for run_pipeline.py
        print(f"[WORKING] {filename}")
        print(f"[PROGRESS] {(i/total)*100}")
        sys.stdout.flush()
        
        path = data_dir / filename
        if not path.exists():
            continue
            
        agent.triage(str(path))
    
    print("[PROGRESS] 100")
    sys.stdout.flush()

if __name__ == "__main__":
    main()
