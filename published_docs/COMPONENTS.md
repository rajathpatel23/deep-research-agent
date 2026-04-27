# Components Reference

## Core Components

## `src/agent/config.py`

- Loads environment-backed runtime config.
- Defines enums for LLM providers and search backends.
- Holds tunables for recovery, query rewriting, parallelism, and stopping windows.

## `src/agent/experiment_config.py`

- Parses YAML experiment definitions.
- Converts experiment schema into runtime `Config`.
- Enables reproducible multi-run ablations.

## `src/agent/llm.py`

- Provider abstraction (`BaseLLMProvider`) and concrete adapters:
  - Groq, Anthropic, Nebius, MiniMax, Ollama, Mock
- Centralized retry and timeout behavior.
- Captures per-call traces through `LLMClient`.

## `src/agent/retriever.py`

- Executes web retrieval (Tavily or mock backend).
- Applies domain policy and non-text filtering.
- Supports query compression and adaptive parallelism hints.

## `src/agent/decomposer.py`

- Converts top-level query into sub-questions.
- Marks each sub-question as supporting or adversarial.

## `src/agent/planner.py`

- Defines planner actions: `SearchAction`, `ChallengeAction`, `StopAction`.
- Implements baseline and guided policies.

## `src/agent/extractor.py`

- Extracts normalized claims from retrieved observations.
- Supports batched extraction with bounded parallelism.

## `src/agent/claim_filter.py`

- Optional post-extraction filter to keep claims relevant to sub-question scope.

## `src/agent/conflict.py`

- Compares claims for compatibility vs contradiction.
- Updates dispute status on claim groups.

## `src/agent/evidence_store.py`

- Canonical runtime memory/state model.
- Tracks sub-question progress, observations, claim groups, and step history.

## `src/agent/metrics.py`

- Computes run-level KPIs:
  - coverage completeness
  - search efficiency
  - conflict surfacing rate
  - stopping quality
  - summary grounding rate
  - source diversity mean
  - confidence calibration

## `src/agent/dashboard.py`

- Generates self-contained HTML diagnostics dashboard from run state.

## `src/agent/report.py`

- Generates final markdown synthesis report from collected evidence.

## `src/agent/orchestrator.py`

- End-to-end control loop wiring all components together.
- Produces final run trace and persists artifacts.

## CLI Entrypoints

## `run.py`

- Runs one query in one mode (`baseline` or `guided`).

## `experiment.py`

- Runs YAML-defined experiment sweeps over one or more modes/queries.
- Emits aggregate summary plus per-run artifacts.

## Data and Config Directories

- `experiments/` - YAML configs for controlled runs and ablations.
- `runs/` - persisted outputs for each executed run.
- `tests/` - unit and behavior tests across components.
