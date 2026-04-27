#!/usr/bin/env python3
"""
Run a structured experiment from a YAML config file.

Usage:
  python experiment.py --config experiments/rag_factuality.yaml
  python experiment.py --config experiments/rag_factuality.yaml --mock
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

load_dotenv()

from src.agent.decomposer import decompose
from src.agent.experiment_config import load_experiment
from src.agent.llm import LLMClient
from src.agent.orchestrator import _build_search_query, _should_use_research_mode
from src.agent.orchestrator import run
from src.agent.retriever import Retriever


def _slug(text: str, max_len: int = 40) -> str:
    return "".join(c if c.isalnum() else "_" for c in text.lower())[:max_len].strip("_")


def _print_comparison(results: list) -> None:
    if not results:
        return

    header = (
        f"{'query':<32} {'mode':<10} {'model':<18} {'steps':>5} "
        f"{'cov':>5} {'eff':>5} {'csr':>5} {'sq':>5} {'grnd':>5} {'div':>5} {'cal':>5} {'term':<22}"
    )
    legend = (
        "cov=coverage  eff=efficiency  csr=conflict_surfacing  sq=stopping_quality  "
        "grnd=summary_grounding  div=source_diversity_mean  cal=confidence_calibration"
    )
    print("\n" + "=" * len(header))
    print(f"Experiment Results\n{legend}")
    print("=" * len(header))
    print(header)
    print("-" * len(header))

    for r in results:
        print(
            f"{r['query'][:32]:<32} "
            f"{r['mode']:<10} "
            f"{r.get('llm_model', '')[:18]:<18} "
            f"{r['total_steps']:>5} "
            f"{r.get('coverage_completeness', 0):>5.0%} "
            f"{r.get('search_efficiency', 0):>5.0%} "
            f"{r.get('conflict_surfacing_rate', 0):>5.0%} "
            f"{r.get('stopping_quality', 0):>5.0%} "
            f"{r.get('summary_grounding_rate', 0):>5.0%} "
            f"{r.get('source_diversity_mean', 0):>5.2f} "
            f"{r.get('confidence_calibration', 0):>5.0%} "
            f"{r['termination_reason']:<22}"
        )
    print("=" * len(header))


def _build_prefetch_cache(query: str, sub_questions: list, retriever: Retriever, max_results: int) -> dict:
    """Prefetch shared sources; cache only non-empty result sets."""
    observation_cache = {}
    for sq in sub_questions:
        prefetch_query = _build_search_query(query, sq)
        research_mode = _should_use_research_mode(sq)
        results = retriever.search(
            prefetch_query,
            max_results=max_results,
            research_mode=research_mode,
        )
        if results:
            observation_cache[sq.id] = results
            print(f"  [{sq.kind.value}] {sq.text[:60]} → {len(results)} results (cached)")
        else:
            print(f"  [{sq.kind.value}] {sq.text[:60]} → 0 results (uncached)")
    return observation_cache


def main() -> None:
    parser = argparse.ArgumentParser(description="Deep Research Agent — Experiment Runner")
    parser.add_argument("--config", required=True, help="Path to experiment YAML config")
    parser.add_argument("--mock", action="store_true", help="Override to mock mode (no API calls)")
    parser.add_argument("--verbose", action="store_true", help="Print sources and claims at each step")
    args = parser.parse_args()

    experiment = load_experiment(args.config)
    config = experiment.to_agent_config()

    if args.mock:
        config.mock_mode = True
        from src.agent.config import LLMProvider, SearchBackend
        config.llm_provider = LLMProvider.MOCK
        config.search_backend = SearchBackend.MOCK

    base_output = Path(experiment.output_dir) / experiment.name
    print(f"Experiment: {experiment.name}")
    if experiment.description:
        print(f"Description: {experiment.description}")
    print(f"LLM: {config.llm_provider.value} / {config.llm_model}")
    print(f"Search: {config.search_backend.value}")
    print(f"Output: {base_output}/\n")

    all_results = []

    for run_spec in experiment.runs:
        # Pre-fetch sources once if shared_sources mode and multiple modes to compare
        shared_sqs = None
        observation_cache = None
        if run_spec.shared_sources and len(run_spec.modes) > 1:
            print(f"[shared_sources] pre-fetching for: {run_spec.query[:60]}")
            _llm = LLMClient(config)
            _retriever = Retriever(config)
            shared_sqs = decompose(run_spec.query, _llm)
            observation_cache = _build_prefetch_cache(
                run_spec.query,
                shared_sqs,
                _retriever,
                max_results=config.max_results,
            )
            print()

        for mode in run_spec.modes:
            output_dir = base_output / _slug(run_spec.query) / mode
            print(f"--- {mode} | {run_spec.query[:60]} ---")
            trace = run(
                query=run_spec.query,
                mode=mode,
                max_steps=run_spec.max_steps,
                output_dir=output_dir,
                config=config,
                verbose=args.verbose,
                shared_sub_questions=shared_sqs,
                observation_cache=observation_cache,
            )
            all_results.append(trace)
            print()

    summary_path = base_output / "summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(all_results, indent=2))
    print(f"Summary saved → {summary_path}")

    _print_comparison(all_results)


if __name__ == "__main__":
    main()
