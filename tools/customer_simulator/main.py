import argparse
import asyncio
import os
from .demo import run_interactive_demo

async def main():
    parser = argparse.ArgumentParser(description="RiskPilot Customer Simulator")
    parser.add_argument("--scenario", type=str, choices=["normal", "suspicious", "critical", "mixed", "false_positive"], required=True)
    parser.add_argument("--count", type=int, default=1, help="Number of events (default 1 for interactive demo)")
    parser.add_argument("--api-key", type=str, help="Customer API Key (or set RISKPILOT_API_KEY env var)")
    parser.add_argument("--base-url", type=str, default="http://localhost:8000")
    
    args = parser.parse_args()
    
    api_key = args.api_key or os.environ.get("RISKPILOT_API_KEY")
    if not api_key:
        print("Error: --api-key or RISKPILOT_API_KEY environment variable is required.")
        return
        
    await run_interactive_demo(args.scenario, args.count, api_key, args.base_url)

if __name__ == "__main__":
    asyncio.run(main())
