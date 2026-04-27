"""Generate a self-contained HTML dashboard for a single run."""
import json
from pathlib import Path

from src.agent.evidence_store import EvidenceStore
from src.agent.states import GroupStatus, StepResult


_STEP_COLORS = {
    StepResult.NEW_EVIDENCE: "#22c55e",
    StepResult.CONFLICT_FOUND: "#ef4444",
    StepResult.REDUNDANT: "#f59e0b",
    StepResult.DEAD_END: "#6b7280",
    StepResult.NO_RETRIEVAL_RESULTS: "#475569",
    StepResult.NO_EXTRACTABLE_CLAIMS: "#0ea5e9",
}

_STEP_LABELS = {
    StepResult.NEW_EVIDENCE: "NEW",
    StepResult.CONFLICT_FOUND: "CONFLICT",
    StepResult.REDUNDANT: "REDUNDANT",
    StepResult.DEAD_END: "DEAD END",
    StepResult.NO_RETRIEVAL_RESULTS: "NO RESULTS",
    StepResult.NO_EXTRACTABLE_CLAIMS: "NO CLAIMS",
}


def generate_dashboard(store: EvidenceStore, run_trace: dict, output_path: Path) -> None:
    metrics = {
        "Coverage": run_trace.get("coverage_completeness", 0),
        "Efficiency": run_trace.get("search_efficiency", 0),
        "Conflict Surfacing": run_trace.get("conflict_surfacing_rate", 0),
        "Stopping Quality": run_trace.get("stopping_quality", 0),
    }

    html = _render(store, run_trace, metrics)
    output_path.write_text(html)


def _bar(value: float, color: str = "#6366f1") -> str:
    pct = int(value * 100)
    return f"""
      <div class="metric-bar-bg">
        <div class="metric-bar-fill" style="width:{pct}%; background:{color}"></div>
      </div>"""


def _step_timeline(store: EvidenceStore) -> str:
    if not store.step_history:
        return "<p>No steps recorded.</p>"
    pills = []
    for s in store.step_history:
        color = _STEP_COLORS.get(s.result, "#6b7280")
        label = _STEP_LABELS.get(s.result, s.result.value)
        action_type = s.action.split(":")[0]
        pills.append(
            f'<span class="pill" style="background:{color}" title="Step {s.step}: {s.action}">'
            f'{s.step} {action_type[:3].upper()} {label}</span>'
        )
    return "<div class='timeline'>" + "".join(pills) + "</div>"


def _sub_questions(store: EvidenceStore) -> str:
    rows = []
    for sq in store.sub_questions:
        groups = [g for g in store.claim_groups if g.sub_question_id == sq.id]
        disputed = sum(1 for g in groups if g.status == GroupStatus.DISPUTED)
        icon = "✓" if sq.has_evidence else "○"
        color = "#22c55e" if sq.has_evidence else "#9ca3af"
        badge = f'<span class="badge badge-red">{disputed} disputed</span>' if disputed else ""
        kind_badge = f'<span class="badge badge-{"blue" if sq.kind.value == "supporting" else "orange"}">{sq.kind.value}</span>'
        rows.append(f"""
          <tr>
            <td style="color:{color};font-weight:bold">{icon}</td>
            <td>{sq.text}</td>
            <td>{kind_badge}</td>
            <td>{len(groups)}</td>
            <td>{badge}</td>
          </tr>""")
    return "<table class='data-table'><thead><tr><th></th><th>Sub-question</th><th>Kind</th><th>Groups</th><th>Disputes</th></tr></thead><tbody>" + "".join(rows) + "</tbody></table>"


def _claim_groups(store: EvidenceStore) -> str:
    if not store.claim_groups:
        return "<p>No claim groups.</p>"
    rows = []
    for g in store.claim_groups:
        conf_color = {"high": "#22c55e", "medium": "#f59e0b", "low": "#9ca3af"}.get(g.aggregate_confidence.value, "#9ca3af")
        status_color = {"disputed": "#ef4444", "supported": "#22c55e", "weak": "#9ca3af", "speculative": "#f59e0b"}.get(g.status.value, "#9ca3af")
        domains = ", ".join(g.source_domains) if g.source_domains else "—"
        rows.append(f"""
          <tr>
            <td>{g.canonical_text[:80]}{"…" if len(g.canonical_text) > 80 else ""}</td>
            <td><span class="dot" style="background:{conf_color}"></span>{g.aggregate_confidence.value}</td>
            <td><span class="dot" style="background:{status_color}"></span>{g.status.value}</td>
            <td style="font-size:0.75rem;color:#6b7280">{domains[:60]}</td>
            <td>{len(g.supporting_claim_ids)}</td>
            <td>{len(g.contradicting_claim_ids)}</td>
          </tr>""")
    return "<table class='data-table'><thead><tr><th>Claim</th><th>Confidence</th><th>Status</th><th>Sources</th><th>Supporting</th><th>Contradicting</th></tr></thead><tbody>" + "".join(rows) + "</tbody></table>"


def _render(store: EvidenceStore, run_trace: dict, metrics: dict) -> str:
    metric_cards = ""
    colors = ["#6366f1", "#22c55e", "#ef4444", "#f59e0b"]
    for (name, val), color in zip(metrics.items(), colors):
        metric_cards += f"""
        <div class="metric-card">
          <div class="metric-value" style="color:{color}">{val:.0%}</div>
          <div class="metric-name">{name}</div>
          {_bar(val, color)}
        </div>"""

    term = run_trace.get("termination_reason", "unknown")
    term_color = "#22c55e" if term == "COVERAGE_MET" else ("#f59e0b" if term == "DIMINISHING_RETURNS" else "#6b7280")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Deep Research Agent — {run_trace.get('mode','').title()} Run</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0f172a; color: #e2e8f0; line-height: 1.5; }}
  .container {{ max-width: 1100px; margin: 0 auto; padding: 2rem; }}
  h1 {{ font-size: 1.5rem; font-weight: 700; color: #f8fafc; margin-bottom: 0.25rem; }}
  h2 {{ font-size: 1.1rem; font-weight: 600; color: #94a3b8; margin: 2rem 0 1rem; text-transform: uppercase; letter-spacing: 0.05em; }}
  .meta {{ font-size: 0.85rem; color: #64748b; margin-bottom: 2rem; }}
  .meta span {{ margin-right: 1.5rem; }}
  .tag {{ display: inline-block; padding: 0.15rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600; }}
  .metrics-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 2rem; }}
  .metric-card {{ background: #1e293b; border-radius: 8px; padding: 1.25rem; }}
  .metric-value {{ font-size: 2rem; font-weight: 700; }}
  .metric-name {{ font-size: 0.8rem; color: #64748b; margin: 0.25rem 0 0.5rem; }}
  .metric-bar-bg {{ background: #334155; border-radius: 4px; height: 6px; }}
  .metric-bar-fill {{ height: 6px; border-radius: 4px; transition: width 0.3s; }}
  .timeline {{ display: flex; flex-wrap: wrap; gap: 0.4rem; margin-bottom: 1rem; }}
  .pill {{ padding: 0.3rem 0.6rem; border-radius: 4px; font-size: 0.7rem; font-weight: 600; color: white; cursor: default; }}
  .data-table {{ width: 100%; border-collapse: collapse; font-size: 0.85rem; background: #1e293b; border-radius: 8px; overflow: hidden; }}
  .data-table th {{ background: #334155; padding: 0.6rem 0.8rem; text-align: left; font-size: 0.75rem; text-transform: uppercase; color: #94a3b8; }}
  .data-table td {{ padding: 0.6rem 0.8rem; border-bottom: 1px solid #334155; vertical-align: top; }}
  .data-table tr:last-child td {{ border-bottom: none; }}
  .badge {{ display: inline-block; padding: 0.1rem 0.4rem; border-radius: 3px; font-size: 0.7rem; font-weight: 600; }}
  .badge-red {{ background: #450a0a; color: #fca5a5; }}
  .badge-blue {{ background: #1e3a5f; color: #93c5fd; }}
  .badge-orange {{ background: #431407; color: #fdba74; }}
  .dot {{ display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 4px; vertical-align: middle; }}
  .section {{ background: #1e293b; border-radius: 8px; padding: 1.25rem; margin-bottom: 1rem; overflow-x: auto; }}
  .summary-bar {{ display: flex; gap: 1.5rem; background: #1e293b; border-radius: 8px; padding: 1rem 1.25rem; margin-bottom: 2rem; font-size: 0.85rem; }}
  .summary-item {{ display: flex; flex-direction: column; }}
  .summary-label {{ font-size: 0.7rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; }}
  .summary-val {{ font-weight: 700; color: #f8fafc; }}
</style>
</head>
<body>
<div class="container">
  <h1>{store.query}</h1>
  <div class="meta">
    <span>Mode: <strong>{run_trace.get('mode','')}</strong></span>
    <span>Model: <strong>{run_trace.get('llm_model','unknown')}</strong></span>
    <span>Termination: <strong style="color:{term_color}">{term}</strong></span>
  </div>

  <div class="summary-bar">
    <div class="summary-item"><span class="summary-label">Steps</span><span class="summary-val">{run_trace.get('total_steps',0)}</span></div>
    <div class="summary-item"><span class="summary-label">Sub-questions</span><span class="summary-val">{run_trace.get('sub_questions_covered',0)}/{run_trace.get('sub_questions_total',0)}</span></div>
    <div class="summary-item"><span class="summary-label">Claim Groups</span><span class="summary-val">{run_trace.get('claim_groups_total',0)}</span></div>
    <div class="summary-item"><span class="summary-label">Disputes</span><span class="summary-val">{run_trace.get('disputes',0)}</span></div>
  </div>

  <div class="metrics-grid">
    {metric_cards}
  </div>

  <h2>Step Timeline</h2>
  <div class="section">
    {_step_timeline(store)}
    <div style="margin-top:0.75rem;font-size:0.75rem;color:#64748b;display:flex;gap:1rem">
      <span><span class="dot" style="background:#22c55e"></span>New Evidence</span>
      <span><span class="dot" style="background:#ef4444"></span>Conflict Found</span>
      <span><span class="dot" style="background:#f59e0b"></span>Redundant</span>
      <span><span class="dot" style="background:#6b7280"></span>Dead End</span>
      <span><span class="dot" style="background:#475569"></span>No Retrieval Results</span>
      <span><span class="dot" style="background:#0ea5e9"></span>No Extractable Claims</span>
    </div>
  </div>

  <h2>Sub-questions</h2>
  <div class="section">
    {_sub_questions(store)}
  </div>

  <h2>Claim Groups ({len(store.claim_groups)})</h2>
  <div class="section">
    {_claim_groups(store)}
  </div>
</div>
</body>
</html>"""
