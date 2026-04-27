# Deep Research Agent Architecture

## Goal

Given a complex research question, the agent should:

1. Decompose it into tractable sub-questions.
2. Retrieve diverse evidence from web sources.
3. Extract and normalize claims.
4. Detect contradictions and unresolved fault lines.
5. Stop when coverage or budget criteria are met.
6. Produce a report plus machine-readable traces.

## High-Level Pipeline

```text
Query
  -> Decomposer
  -> Planner (baseline or guided)
  -> Retriever (search + rerank + domain gating)
  -> Claim Extractor (+ optional claim filter)
  -> Conflict Engine
  -> Evidence Store update
  -> Metrics + Dashboard + Report
```

## Block Diagram

```text
+------------------------------+
| User Query / Experiment Run  |
| run.py or experiment.py      |
+--------------+---------------+
               |
               v
+------------------------------+
| Orchestrator                |
| src/agent/orchestrator.py   |
+------+-----------------------+
       |
       v
+------------------------------+       +------------------------------+
| Decomposer                  | -----> | Evidence Store              |
| src/agent/decomposer.py     |        | src/agent/evidence_store.py |
+------------------------------+       +------------------------------+
                                             ^               |
                                             | (read)        | (write)
                                             |               v
                                     +------------------------------+
                                     | Planner                      |
                                     | baseline_plan / guided_plan  |
                                     +--------------+---------------+
                                                    |
                                                    v
                                     +------------------------------+
                                     | Action                       |
                                     | Search / Challenge / Stop    |
                                     +------+-----------------------+
                                            |
                                            | if Search or Challenge
                                            v
                   +------------------------+------------------------+
                   | Retrieval + Processing Pipeline                 |
                   | Retriever -> Query Rewriter -> Reranker         |
                   | -> Extractor (+ Claim Filter) -> Conflict       |
                   +------------------------+------------------------+
                                            |
                                            v
                                     +------------------------------+
                                     | Evidence Store Update         |
                                     | observations, claims, disputes|
                                     +--------------+---------------+
                                                    |
                                                    v
                                     +------------------------------+
                                     | Stop Criteria + Metrics       |
                                     | coverage / budget / returns   |
                                     +--------------+---------------+
                                                    |
                                                    v
                                     +------------------------------+
                                     | Outputs                       |
                                     | run_trace.json                |
                                     | evidence_store.json           |
                                     | report.md + dashboard.html    |
                                     +------------------------------+
```

## Core Runtime Loop

Implemented in `src/agent/orchestrator.py`.

- Initializes config, model/search clients, and an `EvidenceStore`.
- Produces sub-questions with `src/agent/decomposer.py`.
- Selects next action via:
  - `baseline_plan` (fixed order)
  - `guided_plan` (state-aware)
- For search actions:
  - builds query
  - optionally rewrites into variants
  - retrieves and reranks sources
  - extracts claims in parallel (configurable)
  - updates coverage and claim groups
- For challenge actions:
  - searches for contradicting evidence against existing groups.
- Evaluates step outcome and stopping criteria.

## Data Model and State

Primary state lives in `src/agent/evidence_store.py`.

Major entities:

- `SubQuestion`: decomposed unit of inquiry (`supporting` or `adversarial`)
- `Observation`: retrieved source snippets tied to a sub-question
- `ClaimGroup`: clustered canonical claim with scope and confidence
- `StepRecord`: per-step action and outcome diagnostics
- `LLMCallRecord`: prompt/response trace for analysis and debugging

Why this matters:

- Separates retrieval facts (observations) from synthesis artifacts (claim groups)
- Enables reproducible post-hoc analysis (`run_trace.json`, `evidence_store.json`)

## Execution Modes

### Baseline Mode

- Deterministic, fixed progression over sub-questions.
- Useful as a control in ablation experiments.
- Tends to consume full step budget before stopping.

### Guided Mode

- Chooses next action based on evidence coverage, conflict signals, and diminishing returns.
- Can terminate early when coverage criteria are met.
- Better suited for efficiency-sensitive runs.

## Reliability and Recovery Features

Key mechanisms used during retrieval/extraction:

- query rewriting variants (`query_rewriter.py`)
- reranking of retrieved documents (`reranker.py`)
- extractor rescue pivots for dead ends
- adaptive search parallelism (`retriever.py`)
- query compression for long queries
- retries on provider/search transient failures

## Output Artifacts

Each run writes:

- `run_trace.json` - scalar metrics + detailed per-step diagnostics
- `evidence_store.json` - full structured state
- `report.md` - final narrative synthesis with sources
- `dashboard.html` - visual timeline and quality panels

## Design Trade-Offs

- **Traceability vs cost**: rich trace logs improve diagnosability but increase token usage and file size.
- **Coverage vs precision**: broader retrieval improves recall but increases low-quality claims.
- **Early stop vs thoroughness**: guided stopping reduces cost but may miss edge-case evidence.
- **Parallelism vs stability**: higher fan-out improves throughput but can increase noisy/duplicate evidence and API stress.
