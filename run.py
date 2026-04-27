#!/usr/bin/env python3
"""
Deep Research Agent — CLI entrypoint.

Usage:
  python run.py --query "..." --mode baseline|guided [--max-steps N] [--output-dir runs/]

Environment:
  Copy .env.example to .env and fill in API keys.
  Set MOCK=true to run without any API calls.
"""
import argparse
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.agent.orchestrator import run


def main() -> None:
    parser = argparse.ArgumentParser(description="Deep Research Agent")
    parser.add_argument("--query", required=True, help="Research query")
    parser.add_argument(
        "--mode",
        choices=["baseline", "guided"],
        default="guided",
        help="baseline=fixed-order, guided=evidence-driven (default: guided)",
    )
    parser.add_argument("--max-steps", type=int, default=10, help="Max research steps (default: 10)")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory (default: runs/<timestamp>_<mode>)",
    )
    args = parser.parse_args()

    if args.output_dir is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output_dir = Path("runs") / f"{ts}_{args.mode}"

    print(f"Query: {args.query}")
    print(f"Mode:  {args.mode}")
    print(f"Steps: {args.max_steps}")
    print(f"Output: {args.output_dir}")
    print()

    trace = run(
        query=args.query,
        mode=args.mode,
        max_steps=args.max_steps,
        output_dir=args.output_dir,
    )

    print()
    print("=== Run Summary ===")
    print(f"Steps:           {trace['total_steps']}")
    print(f"Termination:     {trace['termination_reason']}")
    print(f"Coverage:        {trace['sub_questions_covered']}/{trace['sub_questions_total']} sub-questions")
    print(f"Claim groups:    {trace['claim_groups_total']}")
    print(f"Disputes found:  {trace['disputes']}")
    print(f"Step results:    {', '.join(trace['step_results'])}")


if __name__ == "__main__":
    main()
