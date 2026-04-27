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

## Results

### Run 1: Chain-of-Thought Effectiveness

**Query:** "Is chain-of-thought prompting an effective technique?"

Compared artifacts (used for recalculation):

- Baseline: `runs/ablation_phase6_parallel/is_chain_of_thought_prompting_an_effecti/baseline/{evidence_store.json, report.md}`
- Guided: `runs/ablation_phase6_parallel_guided/is_chain_of_thought_prompting_an_effecti/guided/{evidence_store.json, report.md}`
- Search backend: tavily (both arms)

#### Metrics Snapshot

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

#### Supporting Diagnostics Snapshot

| Metric | Baseline | Guided | Delta (Guided - Baseline) |
|---|---:|---:|---:|
| Unsupported summary rate | 0.333 | 0.000 | -0.333 |
| Unresolved disclosure rate | 1.000 | 1.000 | 0.000 |
| Uncertainty calibration score | 0.500 | 0.000 | -0.500 |
| Epistemic honesty score | 0.733 | 0.800 | +0.067 |

#### Interpretation Against the Thesis

- Guided improves uncertainty-reduction efficiency (`search_efficiency`) and reaches full decomposition coverage (`coverage_completeness`) with fewer steps.
- Guided better surfaces contested evidence (`disputes` increased from 0 to 2), which aligns with the thesis requirement to expose fault lines rather than smooth them over.
- Guided improves process-faithful summary quality (`summary_grounding_rate` rose to 1.0 under traceability rules that include process metadata claims).
- `stopping_quality` now distinguishes good vs bad stopping causes (guided reached `COVERAGE_MET`; baseline hit `BUDGET_EXHAUSTED`).
- `confidence_calibration` is undefined (`n/a`) for this pair because confidence tiers lack spread, so calibration cannot be meaningfully estimated.
- `uncertainty_calibration_score` is lower for guided because the guided summary is concise and less hedged linguistically despite strong process metrics; this should be interpreted alongside the component metrics, not in isolation.

### Run 2: Inference-Time Compute Scaling

**Query:** "What is the current state of inference-time compute scaling for LLM reasoning? Separate what has been empirically validated from what is still speculative, and identify where the evidence is too thin to draw conclusions."

Compared artifacts:

- Baseline: `runs/inference_compute_baseline/what_is_the_current_state_of_inference_t/baseline/{evidence_store.json, report.md}`
- Guided: `runs/inference_compute_guided/what_is_the_current_state_of_inference_t/guided/{evidence_store.json, report.md}`
- Configs: `experiments/inference_compute_baseline.yaml`, `experiments/inference_compute_guided.yaml` (shared seed query in `experiments/inference_compute_shared.yaml`)
- Model: MiniMax-M2.7 (both arms)
- Search backend: tavily (both arms)

#### Metrics Snapshot

| Metric | Baseline | Guided | Delta (Guided - Baseline) |
|---|---:|---:|---:|
| Total steps | 10 | 8 | -2 |
| Termination reason | BUDGET_EXHAUSTED | COVERAGE_MET | n/a |
| Sub-questions covered | 3 / 5 | 5 / 5 | +2 |
| Coverage completeness | 0.600 | 1.000 | +0.400 |
| Search efficiency | 0.500 | 0.625 | +0.125 |
| Conflict surfacing rate | n/a | n/a | n/a |
| Stopping quality | 0.000 | 1.000 | +1.000 |
| Summary traceability (`summary_grounding_rate`) | 0.667 | 1.000 | +0.333 |
| Source diversity mean | 1.000 | 1.000 | 0.000 |
| Confidence calibration | n/a | n/a | n/a |
| Claim groups total | 9 | 8 | -1 |
| Disputes | 0 | 0 | 0 |
| Total LLM calls | 113 | 116 | +3 |

#### Supporting Diagnostics Snapshot

| Metric | Baseline | Guided | Delta (Guided - Baseline) |
|---|---:|---:|---:|
| Unsupported summary rate | 0.333 | 0.000 | -0.333 |
| Unresolved disclosure rate | 1.000 | 1.000 | 0.000 |
| Uncertainty calibration score | 1.000 | 1.000 | 0.000 |
| Epistemic honesty score | 0.833 | 1.000 | +0.167 |
| Adjacent claims total | 20 | 18 | -2 |
| Direct claims total | 10 | 8 | -2 |
| Direct claim conversion rate | 0.333 | 0.308 | -0.025 |
| Conflict candidates considered | 16 | 15 | -1 |
| Conflict LLM checks | 8 | 13 | +5 |
| Conflict scope-filtered | 8 | 2 | -6 |
| Contradictions found | 0 | 0 | 0 |

#### Step Trajectories

- Baseline: `NO_EXTRACTABLE_CLAIMS, DEAD_END, NEW_EVIDENCE, DEAD_END, NEW_EVIDENCE, NEW_EVIDENCE, DEAD_END, NEW_EVIDENCE, NO_EXTRACTABLE_CLAIMS, NEW_EVIDENCE` — dead-ends and zero-claim steps interleaved across the whole budget.
- Guided: `DEAD_END, DEAD_END, NO_EXTRACTABLE_CLAIMS, NEW_EVIDENCE, NEW_EVIDENCE, NEW_EVIDENCE, NEW_EVIDENCE, NEW_EVIDENCE` — failure front-loaded, then five productive steps in a row before coverage was met.

#### Interpretation Against the Thesis

- Guided reaches full decomposition coverage (`coverage_completeness` 0.60 → 1.00) at essentially flat LLM cost (113 → 116 calls). The compute envelope is the same; the terminal state is not.
- `stopping_quality` again distinguishes good vs bad stopping causes (guided `COVERAGE_MET`; baseline `BUDGET_EXHAUSTED`).
- Guided produces a fully grounded summary (`summary_grounding_rate` 1.0, `unsupported_summary_rate` 0.0) — every summary sentence traces to extracted claims. Baseline leaves ~1/3 of the summary unsupported.
- Conflict pipeline behaves materially differently in guided: `scope_filtered` drops 8 → 2, `llm_checks` rises 8 → 13. Guided's claims are landing with tighter scopes so fewer get pre-filtered as scope-mismatched, and more genuinely make it to the LLM contradiction stage.
- `confidence_calibration` is `n/a` for this pair because all extracted claims sit at `Confidence: low | Status: weak` — there is no spread across confidence tiers to calibrate against.

#### Learnings

- **Guidance trades step count for step quality at flat compute.** Two fewer steps, three more LLM calls, +0.40 coverage, +0.33 summary grounding, +0.17 epistemic honesty. The cost story is "same compute, better terminal state," not "more compute for better results."
- **Guidance helps the planner recover from bad early steps.** Baseline interleaved dead-ends across the full 10-step budget; guided concentrated failure in steps 0–2 and then ran five productive steps to coverage. Suggests the gain comes from faster pivoting after dead-ends, not from avoiding dead-ends entirely.
- **Zero contradictions on a "validated vs speculative" framing is a smell.** Both arms returned 0 disputes / 0 contradictions on a query explicitly designed to invite disagreement. Guided's increased `llm_checks` (8 → 13) shows the conflict path is being exercised more, but still resolves to no contradictions. This is either (a) a genuinely hedged corpus where everything reads as low-confidence, or (b) a conservative contradiction detector that is missing real disagreements. Worth a manual spot-check before this is treated as a property of the corpus.
- **All claims plateaued at `Confidence: low | Status: weak`.** Despite 18–20 observations per arm, no claim corroborated to `medium` or `strong`. This is identical across arms, so it is a corroboration-aggregation issue, not a guidance issue.
- **`confidence_calibration` is `n/a` again** for the same reason as Run 1: no confidence-tier spread to calibrate. Two consecutive `n/a` results suggest this metric will rarely be defined in practice unless the extractor produces medium/strong claims more often.
- **n=1 caveat.** Same query, single seed, single model. The result is consistent in direction with Run 1 (guided wins on coverage and grounding while reaching `COVERAGE_MET`), but replication across queries and seeds is required before this is a load-bearing claim.

### Run 3: Multi-Agent LLM Systems Landscape (different search backend)

**Query:** "Map the research landscape of multi-agent LLM systems. Produce a structured report that includes a visual taxonomy or design graph showing the major architectural patterns, how they relate, and where the open problems are."

Compared artifacts:

- Baseline: `runs/multi_agent_landscape_baseline/map_the_research_landscape_of_multi_agen/baseline/{evidence_store.json, report.md}`
- Guided: `runs/multi_agent_landscape_guided/map_the_research_landscape_of_multi_agen/guided/{evidence_store.json, report.md}`
- Configs: `experiments/multi_agent_landscape_baseline.yaml`, `experiments/multi_agent_landscape_guided.yaml`
- Model: MiniMax-M2.7 (both arms)
- Search backend: **minimax** (both arms) — different from Runs 1 and 2 due to tavily budget exhaustion

> Important framing: Within-pair (baseline vs guided under minimax) is a clean comparison. Cross-run comparisons against Runs 1–2 are confounded by both query type and search backend; the most interesting cross-run signal is reported in the "Cross-run observation" subsection below.

#### Metrics Snapshot

| Metric | Baseline | Guided | Delta (Guided - Baseline) |
|---|---:|---:|---:|
| Total steps | 12 | 6 | -6 |
| Termination reason | BUDGET_EXHAUSTED | COVERAGE_MET | n/a |
| Sub-questions covered | 4 / 5 | 5 / 5 | +1 |
| Coverage completeness | 0.800 | 1.000 | +0.200 |
| Search efficiency | 0.667 | 0.833 | +0.166 |
| Conflict surfacing rate | n/a | n/a | n/a |
| Stopping quality | 0.000 | 1.000 | +1.000 |
| Summary traceability (`summary_grounding_rate`) | 0.667 | 0.333 | -0.334 |
| Source diversity mean | 1.000 | 1.000 | 0.000 |
| Confidence calibration | n/a | n/a | n/a |
| Claim groups total | 14 | 14 | 0 |
| Disputes | 0 | 0 | 0 |
| Total LLM calls | 183 | 83 | -100 |

#### Supporting Diagnostics Snapshot

| Metric | Baseline | Guided | Delta (Guided - Baseline) |
|---|---:|---:|---:|
| Unsupported summary rate | 0.333 | 0.667 | +0.334 |
| Unresolved disclosure rate | 1.000 | 1.000 | 0.000 |
| Uncertainty calibration score | 1.000 | 1.000 | 0.000 |
| Epistemic honesty score | 0.833 | 0.667 | -0.166 |
| Adjacent claims total | 8 | 10 | +2 |
| Direct claims total | 15 | 15 | 0 |
| Direct claim conversion rate | 0.652 | 0.600 | -0.052 |
| Conflict candidates considered | 89 | 18 | -71 |
| Conflict LLM checks | 37 | 12 | -25 |
| Conflict scope-filtered | 52 | 6 | -46 |
| Contradictions found | 0 | 0 | 0 |

#### Step Trajectories

- Baseline: `NEW_EVIDENCE, NO_EXTRACTABLE_CLAIMS, NEW_EVIDENCE, NEW_EVIDENCE, NEW_EVIDENCE, NEW_EVIDENCE, DEAD_END, NEW_EVIDENCE, NO_EXTRACTABLE_CLAIMS, NEW_EVIDENCE, NEW_EVIDENCE, NO_EXTRACTABLE_CLAIMS` — productive overall but dilutes new evidence with three zero-claim steps and one dead-end across the full 12-step budget.
- Guided: `DEAD_END, NEW_EVIDENCE, NEW_EVIDENCE, NEW_EVIDENCE, NEW_EVIDENCE, NEW_EVIDENCE` — single failure step at the start, then five productive steps in a row before reaching `COVERAGE_MET`.

#### Interpretation Against the Thesis

- Within-pair coverage and stopping behavior are consistent with Runs 1–2: guided reaches full decomposition coverage in half the steps and stops voluntarily; baseline exhausts the step budget at 0.80 coverage.
- LLM-call envelope drops sharply (183 → 83, -55%) — driven primarily by guided running half as many steps, which roughly halves extractor / claim_filter / reranker calls. This is the inverse of Run 2's flat-compute behavior (+3 calls) and reflects fewer total steps rather than per-step efficiency.
- Conflict pipeline activity is much lower in guided (89 → 18 candidates, 37 → 12 LLM checks). With identical claim group counts (14 vs 14), this means baseline is generating many more cross-claim peer comparisons per group simply by accumulating more steps; guided's earlier stop short-circuits this. Both arms find 0 contradictions, consistent with Run 2.
- **`summary_grounding_rate` regresses sharply (0.667 → 0.333), opposite to Runs 1–2.** This is the first run in which guided produces a less-grounded summary than baseline. Two-thirds of the guided summary's sentences are not traceable to extracted claims or run metadata.
- `epistemic_honesty_score` follows the grounding metric down (0.833 → 0.667), as expected for a composite that includes summary support.

#### Cross-run Observation: Backend Sensitivity of the Writer

Across all three published runs, the **baseline `summary_grounding_rate` is constant at 0.667**, regardless of query type or search backend (tavily for Runs 1–2, minimax for Run 3). The `guided` value is what flips:

| Run | Backend | Baseline | Guided | Δ |
|---|---|---:|---:|---:|
| Run 1 (CoT) | tavily | 0.667 | 1.000 | +0.333 |
| Run 2 (Inference compute) | tavily | 0.667 | 1.000 | +0.333 |
| Run 3 (Multi-agent landscape) | **minimax** | 0.667 | 0.333 | **-0.334** |

Two changes happened simultaneously in Run 3 (query type and search backend), so this is not a controlled isolation. But the pattern is informative: baseline's report-writing behavior is unaffected by the change, while guided's flips sign by the same magnitude. This is consistent with — though does not prove — a hypothesis that guidance amplifies retrieval-quality differences in the writer stage rather than smoothing them, particularly on synthesis-heavy queries.

#### Learnings

- **Guided's stopping and coverage wins replicate under a different backend.** Coverage 0.80 → 1.00, stopping 0.0 → 1.0, and `COVERAGE_MET` termination reproduce under minimax. The within-pair structural finding is robust to the backend swap.
- **Guided's summary-grounding win does not replicate under minimax.** This is the first observed regression on the metric most directly tied to the thesis (faithful representation of evidence). It must be flagged as a real failure mode of the current writer under thinner retrieval, not waved off.
- **Guidance has lower compute cost when the run terminates earlier, but this is not a "free win."** The 100 fewer LLM calls compared to baseline come from running half as many steps, not from per-step efficiency. The cost story for this run is "less compute, full coverage, worse-grounded summary" — a different point on the trade-off curve than Run 2's "flat compute, full coverage, better-grounded summary."
- **Three baselines agree on `summary_grounding_rate = 0.667` independent of query and backend.** Baseline's report-writing pipeline is producing a stable fraction of unsupported sentences; the variance lives in the guided pipeline.
- **Confound is real and should be respected.** Without a tavily run on this query (or a minimax run on the earlier queries), this run's cross-doc comparisons are exploratory only. The within-pair comparison stands on its own.

## Scope and Caveat

These metrics evaluate honesty and process quality relative to retrieved evidence. They do not prove the retrieved evidence is globally correct or complete.

## Limitations

- **Cross-run comparisons assume identical retrieval.** Runs 1 and 2 used tavily; Run 3 used minimax. Run 3 vs Runs 1–2 differences cannot be attributed to the guided/baseline policy alone — the search backend may also account for the divergence in `summary_grounding_rate`. Treat any cross-backend delta as exploratory, not as a controlled measurement.
- **Tavily budget is exhausted; future runs use minimax.** Future cross-run claims should either be backend-matched or explicitly flagged in the entry. The `Search backend:` field in the per-run "Compared artifacts" block is the canonical place to surface this.
- **Single seed, single model per query.** No replication across seeds or models. Direction of within-pair effects has been consistent so far (Runs 1–3 all show coverage and stopping wins for guided), but absolute magnitudes should not be treated as load-bearing.
- **No ground-truth answer key.** All metrics are honesty-relative-to-store, not correctness. A run can score perfectly on summary grounding while still being globally wrong if the evidence store itself is wrong.
