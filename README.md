# Deep Research Agent

A Python research agent that decomposes a complex question into sub-questions, retrieves evidence from the web, extracts and clusters claims, surfaces conflicts, and produces a grounded report with run artifacts (HTML dashboard + JSON traces).

## What This Project Does

- Supports two planning modes:
  - `baseline`: fixed-order search/extract/challenge loop
  - `guided`: evidence-driven planner that adapts next actions by state
- Tracks evidence in a structured store (sub-questions, observations, claim groups, disputes, step history)
- Computes run metrics (coverage, efficiency, conflict surfacing, stopping quality, grounding/diversity/calibration)
- Generates human-readable outputs:
  - `report.md`
  - `dashboard.html`
  - `trace.json`, `evidence_store.json`, and related artifacts
- Supports both single runs and YAML-driven experiment sweeps

## Repository Layout

```text
.
├── run.py                  # Single-query CLI entrypoint
├── experiment.py           # YAML experiment runner
├── experiments/            # Experiment configs
├── src/agent/              # Core agent modules
├── tests/                  # Pytest suite
├── published_docs/         # Commit-ready architecture and results docs
├── docs/                   # Local scratch notes (optional, not for publishing)
└── runs/                   # Generated run artifacts
```

## Published Documentation

Use these docs for sharing/publishing:

- `published_docs/ARCHITECTURE.md` - end-to-end system architecture and data flow
- `published_docs/COMPONENTS.md` - component-by-component responsibilities and interfaces
- `published_docs/RUNBOOK.md` - exact commands for local runs and experiments
- `published_docs/THESIS_AND_RESULTS.md` - thesis, baseline-vs-guided outcomes, and metrics

## Quickstart

### 1) Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2) Install dependencies

```bash
pip install -r requirements.txt
```

### 3) Configure environment variables

```bash
cp .env.example .env
```

Then edit `.env` with the providers/backends you want to use.

### 4) Run a query

```bash
python run.py \
  --query "Is chain-of-thought prompting an effective reasoning strategy for LLMs?" \
  --mode guided \
  --max-steps 10
```

By default, outputs are written to `runs/<timestamp>_<mode>/`.

## Running in Mock Mode (No API Calls)

Use mock mode for quick local iteration and tests without external credentials:

```bash
MOCK=true python run.py --query "Test query" --mode guided
```

Or with experiments:

```bash
python experiment.py --config experiments/ablation_phase6_parallel.yaml --mock
```

## Running Experiments

Run a YAML experiment config:

```bash
python experiment.py --config experiments/ablation_phase6_parallel.yaml --verbose
```

This creates outputs under:

```text
runs/<experiment_name>/<query_slug>/<mode>/
```

And writes an aggregate summary:

```text
runs/<experiment_name>/summary.json
```

## Configuration Model

The system has three main configuration layers:

- **Environment config** (`src/agent/config.py`): provider/backend selection and defaults
- **Experiment config** (`src/agent/experiment_config.py`): YAML schema for ablations and multi-run setups
- **Runtime planner config** (`src/agent/orchestrator.py`): action policy (`baseline` vs `guided`) and stopping behavior

### Supported LLM Providers

- `groq`
- `anthropic`
- `nebius`
- `minimax`
- `ollama`
- `mock`

### Supported Search Backends

- `tavily`
- `mock`

## Outputs and Artifacts

Typical run directory contents include:

- `dashboard.html`: visual timeline, sub-question coverage, claim group status
- `report.md`: narrative synthesis and conclusions
- `trace.json`: run-level metrics and step outcomes
- `evidence_store.json`: structured evidence graph/state
- `llm_trace.json`: model call trace for debugging

## Testing

Run the full test suite:

```bash
pytest
```

Run a focused subset:

```bash
pytest tests/test_orchestrator.py tests/test_retriever.py
```

## Troubleshooting

- **Missing API key errors**: check `.env` keys for selected `LLM_PROVIDER` and `SEARCH_BACKEND`.
- **No retrieval results**: try `guided` mode, increase `max_steps`, or widen domain policy in experiment YAML.
- **Rate limits / transient failures**: retries are built in for LLM/search providers; rerun if needed.
- **Unexpectedly slow runs**: reduce `max_results`, lower parallelism, or use `MOCK=true` for local debugging.

## Where Results Are Written

For each run mode:

- `runs/<experiment>/<query_slug>/<mode>/run_trace.json` - full run metrics and diagnostics
- `runs/<experiment>/<query_slug>/<mode>/report.md` - narrative synthesis
- `runs/<experiment>/<query_slug>/<mode>/dashboard.html` - visual timeline and state
- `runs/<experiment>/<query_slug>/<mode>/evidence_store.json` - structured evidence graph
