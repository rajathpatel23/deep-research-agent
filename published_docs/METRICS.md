# Metrics Definitions

## Purpose

These metrics evaluate process quality and epistemic honesty relative to the collected evidence state. They are not absolute truth metrics.

## Metric Semantics

### `coverage_completeness`

- **Definition:** Fraction of sub-questions that have at least one evidence-backed claim.
- **Formula:** `covered_subquestions / total_subquestions`
- **Range:** `[0, 1]`
- **Interpretation:** Higher means less decomposition drift and fewer uninvestigated threads.

### `search_efficiency`

- **Definition:** Fraction of steps that produced useful progress.
- **Productive steps:** `NEW_EVIDENCE` or `CONFLICT_FOUND`
- **Formula:** `productive_steps / total_steps`
- **Range:** `[0, 1]`
- **Interpretation:** Higher means less budget waste on dead-end/redundant actions.

### `conflict_surfacing_rate`

- **Definition:** Of detected disputed claim groups, fraction explicitly surfaced in the report's conflicts section.
- **Formula:** `surfaced_disputes / detected_disputes`
- **Range:** `[0, 1]`
- **Undefined case:** If `detected_disputes == 0`, metric is `N/A`.
- **Interpretation:** Measures whether contradictions are disclosed, not suppressed.

### `stopping_quality`

- **Definition:** Quality of run termination reason.
- **Scoring rule:**
  - `1.0` for `COVERAGE_MET` or `DIMINISHING_RETURNS`
  - `0.0` for `BUDGET_EXHAUSTED`
- **Range:** `{0, 1}`
- **Interpretation:** Distinguishes principled stopping from budget cutoff.

### `summary_grounding_rate` (shown as "Summary Traceability" in dashboards)

- **Definition:** Fraction of summary sentences traceable to either:
  1. evidence claim-group text, or
  2. run metadata facts (coverage, claim groups, conflicts, steps).
- **Formula:** `traceable_summary_sentences / summary_sentences`
- **Range:** `[0, 1]`
- **Interpretation:** Higher means less unsupported synthesis in summary.

### `source_diversity_mean`

- **Definition:** Mean number of distinct source domains per claim group.
- **Formula:** `mean(len(source_domains) for each claim_group)`
- **Range:** `[0, +inf)`
- **Interpretation:** Higher can indicate stronger cross-source corroboration.

### `confidence_calibration`

- **Definition:** Whether higher confidence tiers are supported by stronger evidence than lower tiers.
- **Current proxy:** Average source-domain counts by confidence tier (high/medium/low) and monotonic ordering check.
- **Range when defined:** `{0, 0.5, 1.0}`
- **Undefined case:** If fewer than two confidence tiers are present, metric is `N/A`.
- **Interpretation:** Keep this metric; treat as conditional. Do not force a numeric score without confidence spread.

## Supporting Diagnostics (non-primary)

### `unsupported_summary_rate`

- **Definition:** `1 - summary_grounding_rate`
- **Use:** Fast view of unsupported summary content.

### `unresolved_disclosure_rate`

- **Definition:** Fraction of uncovered sub-questions explicitly listed in "Unresolved Questions".
- **Use:** Checks disclosure honesty when coverage is incomplete.

### `uncertainty_calibration_score`

- **Definition:** Whether summary language expresses uncertainty when evidence is weak/incomplete.
- **Use:** Linguistic calibration guardrail.

### `epistemic_honesty_score`

- **Definition:** Composite score over summary grounding, unresolved disclosure, and uncertainty calibration.
- **Current weights:** `0.5 * grounding + 0.3 * unresolved + 0.2 * uncertainty`
- **Use:** Aggregate convenience metric; inspect components before drawing conclusions.

## Operational Guidance

- Render undefined metrics as `N/A`, not `0` or `1`.
- Avoid comparing `N/A` metrics as if numeric deltas exist.
- Keep `confidence_calibration` in reports as a conditional diagnostic (not removed).
