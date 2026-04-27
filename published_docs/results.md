# Thesis and Results

## Thesis

A deep research agent has one job: improve an explicit evidence state and produce a structured, evidence-backed report that faithfully represents what the evidence actually supports, not what sounds confident.

The report is a view over an explicit evidence state, not the primary product of generation. Every claim should trace to sources, confidence should reflect evidence quality, conflicts should be surfaced, and uncertainty reduction over the evidence state should drive what to do next and when to stop.

## Evaluation Framework

There is no ground-truth answer key for open-ended research reports, so evaluation is framed as honesty relative to the evidence store the system collected.

Primary runtime metrics:

- `coverage_completeness`
- `search_efficiency`
- `conflict_surfacing_rate`
- `stopping_quality`
- `summary_grounding_rate`
- `source_diversity_mean`
- `confidence_calibration`

Supporting diagnostics:

- `termination_reason`
- `disputes`
- `conflict_diagnostics` (`candidates_considered`, `llm_checks`, `scope_filtered`, `contradictions_found`)
- `unsupported_summary_rate`
- `unresolved_disclosure_rate`
- `uncertainty_calibration_score`
- `epistemic_honesty_score`

## Results: Baseline vs Guided

Compared artifacts:

- Baseline: `runs/ablation_phase6_parallel/is_chain_of_thought_prompting_an_effecti/baseline/run_trace.json`
- Guided: `runs/ablation_phase6_parallel_guided/is_chain_of_thought_prompting_an_effecti/guided/run_trace.json`

### Metrics Snapshot

| Metric | Baseline | Guided | Delta (Guided - Baseline) |
|---|---:|---:|---:|
| Total steps | 15 | 6 | -9 |
| Termination reason | BUDGET_EXHAUSTED | COVERAGE_MET | n/a |
| Coverage completeness | 0.800 | 1.000 | +0.200 |
| Search efficiency | 0.533 | 0.833 | +0.300 |
| Conflict surfacing rate | 1.000 | 1.000 | 0.000 |
| Stopping quality | 0.000 | 0.000 | 0.000 |
| Summary grounding rate | 0.667 | 0.000 | -0.667 |
| Source diversity mean | 1.000 | 1.000 | 0.000 |
| Confidence calibration | 0.000 | 0.000 | 0.000 |
| Claim groups total | 11 | 12 | +1 |
| Disputes | 0 | 2 | +2 |

## Interpretation Against the Thesis

- Guided improves uncertainty-reduction efficiency (`search_efficiency`) and reaches full decomposition coverage (`coverage_completeness`) with fewer steps.
- Guided better surfaces contested evidence (`disputes` increased from 0 to 2), which aligns with the thesis requirement to expose fault lines rather than smooth them over.
- Honesty-floor metrics are mixed in this pair: `summary_grounding_rate` regressed for guided, so this should be treated as an explicit gap, not hidden.
- Both runs show weak calibration/stopping signals (`confidence_calibration` and `stopping_quality` at 0.0), indicating remaining work on confidence semantics and stopping policy quality.

## Scope and Caveat

These metrics evaluate honesty and process quality relative to retrieved evidence. They do not prove the retrieved evidence is globally correct or complete.
