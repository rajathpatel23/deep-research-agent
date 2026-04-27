# Thesis and Results

## Thesis

A deep research agent has one job: improve an explicit evidence state and produce a structured, evidence-backed report that faithfully represents what the evidence actually supports, not what sounds confident.

The report is a view over an explicit evidence state, not the primary product of generation. Every claim should trace to sources, confidence should reflect evidence quality, conflicts should be surfaced, and uncertainty reduction over the evidence state should drive what to do next and when to stop.

## Evaluation Framework

There is no ground-truth answer key for open-ended research reports, so evaluation is framed as honesty relative to the evidence store the system collected.

Metric definitions and `N/A` rules are documented in `published_docs/METRICS.md`.

Primary runtime metrics:

- `coverage_completeness`
- `search_efficiency`
- `conflict_surfacing_rate`
- `stopping_quality`
- `summary_grounding_rate` (reported in dashboards as "Summary Traceability")
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

Compared artifacts (used for recalculation):

- Baseline: `runs/ablation_phase6_parallel/is_chain_of_thought_prompting_an_effecti/baseline/{evidence_store.json, report.md}`
- Guided: `runs/ablation_phase6_parallel_guided/is_chain_of_thought_prompting_an_effecti/guided/{evidence_store.json, report.md}`

### Metrics Snapshot

| Metric | Baseline | Guided | Delta (Guided - Baseline) |
|---|---:|---:|---:|
| Total steps | 15 | 6 | -9 |
| Termination reason | BUDGET_EXHAUSTED | COVERAGE_MET | n/a |
| Coverage completeness | 0.800 | 1.000 | +0.200 |
| Search efficiency | 0.533 | 0.833 | +0.300 |
| Conflict surfacing rate | n/a | 1.000 | n/a |
| Stopping quality | 0.000 | 1.000 | +1.000 |
| Summary traceability (`summary_grounding_rate`) | 0.667 | 1.000 | +0.333 |
| Source diversity mean | 1.000 | 1.000 | 0.000 |
| Confidence calibration | n/a | n/a | n/a |
| Claim groups total | 11 | 12 | +1 |
| Disputes | 0 | 2 | +2 |

### Supporting Diagnostics Snapshot

| Metric | Baseline | Guided | Delta (Guided - Baseline) |
|---|---:|---:|---:|
| Unsupported summary rate | 0.333 | 0.000 | -0.333 |
| Unresolved disclosure rate | 1.000 | 1.000 | 0.000 |
| Uncertainty calibration score | 0.500 | 0.000 | -0.500 |
| Epistemic honesty score | 0.733 | 0.800 | +0.067 |

## Interpretation Against the Thesis

- Guided improves uncertainty-reduction efficiency (`search_efficiency`) and reaches full decomposition coverage (`coverage_completeness`) with fewer steps.
- Guided better surfaces contested evidence (`disputes` increased from 0 to 2), which aligns with the thesis requirement to expose fault lines rather than smooth them over.
- Guided improves process-faithful summary quality (`summary_grounding_rate` rose to 1.0 under traceability rules that include process metadata claims).
- `stopping_quality` now distinguishes good vs bad stopping causes (guided reached `COVERAGE_MET`; baseline hit `BUDGET_EXHAUSTED`).
- `confidence_calibration` is undefined (`n/a`) for this pair because confidence tiers lack spread, so calibration cannot be meaningfully estimated.
- `uncertainty_calibration_score` is lower for guided because the guided summary is concise and less hedged linguistically despite strong process metrics; this should be interpreted alongside the component metrics, not in isolation.

## Scope and Caveat

These metrics evaluate honesty and process quality relative to retrieved evidence. They do not prove the retrieved evidence is globally correct or complete.
