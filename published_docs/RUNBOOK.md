# Runbook

## Environment Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set keys/provider in `.env`:

- `LLM_PROVIDER` (`groq|anthropic|nebius|minimax|ollama|mock`)
- `LLM_MODEL`
- `SEARCH_BACKEND` (`tavily|mock`)
- provider keys (`GROQ_API_KEY`, `ANTHROPIC_API_KEY`, `NEBIUS_API_KEY`, `MINIMAX_API_KEY`, `TAVILY_API_KEY`)

## Single Query Run

Guided mode:

```bash
python run.py \
  --query "Is chain-of-thought prompting an effective reasoning strategy for LLMs?" \
  --mode guided \
  --max-steps 15
```

Baseline mode:

```bash
python run.py \
  --query "Is chain-of-thought prompting an effective reasoning strategy for LLMs?" \
  --mode baseline \
  --max-steps 15
```

## Experiment Run (YAML)

```bash
python experiment.py --config experiments/ablation_phase6_parallel.yaml --verbose
```

Guided-only variant:

```bash
python experiment.py --config experiments/ablation_phase6_parallel_guided.yaml --verbose
```

## Mock Mode (No External Calls)

```bash
MOCK=true python run.py --query "mock check" --mode guided
MOCK=true python experiment.py --config experiments/ablation_phase6_parallel.yaml
```

## Validate and Test

```bash
pytest
```

Targeted:

```bash
pytest tests/test_orchestrator.py tests/test_retriever.py tests/test_metrics.py
```

## Run Output Locations

Per run mode:

- `runs/<experiment>/<query_slug>/<mode>/run_trace.json`
- `runs/<experiment>/<query_slug>/<mode>/report.md`
- `runs/<experiment>/<query_slug>/<mode>/dashboard.html`
- `runs/<experiment>/<query_slug>/<mode>/evidence_store.json`

Aggregate:

- `runs/<experiment>/summary.json` (when produced by experiment runner)

## Common Failure Modes

- Missing key/provider mismatch: verify `.env` values against selected provider/backend.
- Empty retrieval: increase `max_steps`, loosen domain policy, or switch to `guided`.
- Slow execution: lower `max_results`, lower parallelism, or run in mock mode for debug loops.
