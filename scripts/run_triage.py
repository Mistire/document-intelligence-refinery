import sys
from pathlib import Path

# Add src to path so we can import models/agents
sys.path.append(str(Path(__file__).parent.parent))

from src.agents.triage import TriageAgent

def main():
    agent = TriageAgent()
    data_dir = Path("data")
    
    # Files to process
    files = [
        "CBE ANNUAL REPORT 2023-24.pdf",
        "Audit Report - 2023.pdf",
        "fta_performance_survey_final_report_2022.pdf",
        "tax_expenditure_ethiopia_2021_22.pdf"
    ]
    
    print(f"🚀 Starting Triage for {len(files)} documents...")
    
    for filename in files:
        path = data_dir / filename
        if not path.exists():
            print(f"⚠️ Skipping {filename} (not found)")
            continue
            
        print(f"🔍 Triaging {filename}...")
        profile = agent.triage(str(path))
        
        print(f"   -> Result: {profile.origin_type} | {profile.extraction_cost}")
    
    print("\n✨ Batch Triage Complete! Check .refinery/profiles/ for results.")

if __name__ == "__main__":
    main()
