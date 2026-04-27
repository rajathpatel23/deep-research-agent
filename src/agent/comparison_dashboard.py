"""Generate a rich side-by-side comparison dashboard for baseline vs guided runs."""
import json
import re
from pathlib import Path

from src.agent.evidence_store import EvidenceStore
from src.agent.metrics import compute_metrics
from src.agent.states import StepResult


_STEP_COLOR = {
    "NEW_EVIDENCE": "#22c55e",
    "CONFLICT_FOUND": "#ef4444",
    "REDUNDANT": "#f59e0b",
    "DEAD_END": "#6b7280",
    "NO_RETRIEVAL_RESULTS": "#475569",
    "NO_EXTRACTABLE_CLAIMS": "#0ea5e9",
}

_METRIC_EXPLANATIONS = {
    "coverage_completeness": (
        "Coverage",
        "Fraction of sub-questions that got at least one evidence-backed claim. "
        "Low = the system left research threads uninvestigated."
    ),
    "search_efficiency": (
        "Search Efficiency",
        "Fraction of steps that produced new evidence or surfaced a conflict. "
        "Low = wasting budget on redundant or dead-end searches."
    ),
    "conflict_surfacing_rate": (
        "Conflict Surfacing",
        "When contradictions are detected, did the report surface them? "
        "If no contradictions are detected, this metric is N/A."
    ),
    "stopping_quality": (
        "Stopping Quality",
        "Did the run stop for a good reason? "
        "COVERAGE_MET or DIMINISHING_RETURNS = 100%; BUDGET_EXHAUSTED = 0%."
    ),
    "summary_grounding_rate": (
        "Summary Traceability",
        "Fraction of summary sentences traceable to evidence claims or run metadata "
        "(coverage, claim groups, conflicts, steps)."
    ),
    "source_diversity_mean": (
        "Source Diversity",
        "Average number of distinct source domains per claim group. "
        "Higher = claims corroborated by independent sources, not just one outlet."
    ),
    "confidence_calibration": (
        "Confidence Calibration",
        "Are higher-confidence claims backed by stronger evidence than lower-confidence ones? "
        "If claims only use one confidence tier, this metric is N/A."
    ),
}


def load_run(run_dir: Path) -> dict:
    trace = json.loads((run_dir / "run_trace.json").read_text())
    store_data = json.loads((run_dir / "evidence_store.json").read_text())
    store = EvidenceStore(**store_data)
    report = (run_dir / "report.md").read_text() if (run_dir / "report.md").exists() else ""
    trace.update(compute_metrics(store, report))
    return {"trace": trace, "store": store, "report": report, "path": run_dir}


def generate_comparison(baseline_dir: Path, guided_dir: Path, output_path: Path) -> None:
    b = load_run(baseline_dir)
    g = load_run(guided_dir)
    html = _render(b, g)
    output_path.write_text(html)
    print(f"Comparison dashboard → {output_path}")


def _step_journey(run: dict, side: str) -> str:
    store: EvidenceStore = run["store"]
    trace = run["trace"]
    step_results = trace.get("step_results", [])

    sq_map = {sq.id: sq.text for sq in store.sub_questions}

    cards = []
    for record in store.step_history:
        result = record.result.value
        color = _STEP_COLOR.get(result, "#6b7280")
        action_parts = record.action.split(":", 1)
        action_type = action_parts[0]
        action_id = action_parts[1] if len(action_parts) > 1 else ""
        sq_text = sq_map.get(record.sub_question_id, record.sub_question_id)

        icon = {"search": "⟳", "challenge": "⚡", "stop": "■"}.get(action_type, "?")

        cards.append(f"""
        <div class="step-card" style="border-left: 3px solid {color}">
          <div class="step-header">
            <span class="step-num">Step {record.step}</span>
            <span class="step-action">{icon} {action_type.upper()}</span>
            <span class="step-result" style="color:{color}">{result}</span>
          </div>
          <div class="step-question">{sq_text[:100]}{"…" if len(sq_text) > 100 else ""}</div>
        </div>""")

    term = trace.get("termination_reason", "")
    term_color = {"COVERAGE_MET": "#22c55e", "DIMINISHING_RETURNS": "#f59e0b", "BUDGET_EXHAUSTED": "#6b7280"}.get(term, "#6b7280")
    cards.append(f"""
        <div class="step-card" style="border-left: 3px solid {term_color}; opacity: 0.8">
          <div class="step-header">
            <span class="step-num">END</span>
            <span class="step-result" style="color:{term_color}">{term}</span>
          </div>
          <div class="step-question">{_termination_explanation(term)}</div>
        </div>""")

    return "".join(cards)


def _termination_explanation(reason: str) -> str:
    return {
        "COVERAGE_MET": "All sub-questions covered, no unchallenged high-confidence claims remaining.",
        "DIMINISHING_RETURNS": "Last 3 steps were redundant or dead-ends with full coverage — evidence exhausted.",
        "BUDGET_EXHAUSTED": "Hit step limit before evidence was exhausted — would benefit from more budget.",
    }.get(reason, reason)


def _metric_comparison(b: dict, g: dict) -> str:
    def _format_metric(value):
        if value is None:
            return {"text": "N/A", "bar": 0, "defined": False}
        if isinstance(value, float) and value <= 1.0:
            return {"text": f"{value:.0%}", "bar": int(value * 100), "defined": True}
        return {"text": f"{value:.2f}", "bar": min(int(value * 33), 100), "defined": True}

    rows = ""
    for key, (label, explanation) in _METRIC_EXPLANATIONS.items():
        bv = b["trace"].get(key)
        gv = g["trace"].get(key)
        b_data = _format_metric(bv)
        g_data = _format_metric(gv)

        delta_str = "n/a"
        delta_color = "#6b7280"
        if isinstance(bv, (int, float)) and isinstance(gv, (int, float)):
            delta = gv - bv
            delta_str = f"+{delta:.0%}" if isinstance(delta, float) and delta > 0 else f"{delta:.0%}"
            delta_color = "#22c55e" if delta > 0 else ("#ef4444" if delta < 0 else "#6b7280")

        rows += f"""
        <div class="metric-row">
          <div class="metric-label">
            <strong>{label}</strong>
            <span class="metric-explain">{explanation}</span>
          </div>
          <div class="metric-bars">
            <div class="bar-group">
              <span class="bar-label">Baseline</span>
              <div class="bar-track"><div class="bar-fill" style="width:{b_data["bar"]}%;background:#6366f1;opacity:{1 if b_data["defined"] else 0.25}"></div></div>
              <span class="bar-val">{b_data["text"]}</span>
            </div>
            <div class="bar-group">
              <span class="bar-label">Guided</span>
              <div class="bar-track"><div class="bar-fill" style="width:{g_data["bar"]}%;background:#22c55e;opacity:{1 if g_data["defined"] else 0.25}"></div></div>
              <span class="bar-val">{g_data["text"]} <span style="color:{delta_color};font-size:0.75rem">{delta_str}</span></span>
            </div>
          </div>
        </div>"""
    return rows


def _strip_think(text: str) -> str:
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def _md_to_html(text: str) -> str:
    """Minimal markdown → HTML: headers, bold, list items, blank lines."""
    lines = []
    for line in text.split("\n"):
        # Headers
        if line.startswith("### "):
            lines.append(f'<h4 class="r-h4">{line[4:].strip()}</h4>')
        elif line.startswith("## "):
            lines.append(f'<h3 class="r-h3">{line[3:].strip()}</h3>')
        elif line.startswith("# "):
            lines.append(f'<h2 class="r-h2">{line[2:].strip()}</h2>')
        elif line.startswith("- "):
            content = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line[2:])
            lines.append(f'<li>{content}</li>')
        elif line.strip() == "":
            lines.append('<div class="r-gap"></div>')
        else:
            content = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line)
            lines.append(f'<p class="r-p">{content}</p>')
    return "\n".join(lines)


def _render_report(run: dict) -> str:
    report = _strip_think(run["report"])
    if not report:
        return "<p class='dim'>(No report generated)</p>"
    return _md_to_html(report)


def _disputes_section(run: dict) -> str:
    store: EvidenceStore = run["store"]
    disputed = [g for g in store.claim_groups if g.status.value == "disputed"]
    if not disputed:
        return "<p class='dim'>No conflicts detected.</p>"
    items = ""
    for g in disputed:
        items += f"""
        <div class="conflict-card">
          <div class="conflict-claim">{g.canonical_text}</div>
          <div class="conflict-meta">
            Supporting: {len(g.supporting_claim_ids)} &nbsp;|&nbsp;
            Contradicting: {len(g.contradicting_claim_ids)} &nbsp;|&nbsp;
            Sources: {", ".join(g.source_domains)}
          </div>
        </div>"""
    return items


def _render(b: dict, g: dict) -> str:
    query = b["trace"].get("query", "")
    b_steps = b["trace"].get("total_steps", 0)
    g_steps = g["trace"].get("total_steps", 0)
    b_groups = b["trace"].get("claim_groups_total", 0)
    g_groups = g["trace"].get("claim_groups_total", 0)
    b_disputes = b["trace"].get("disputes", 0)
    g_disputes = g["trace"].get("disputes", 0)
    b_model = b["trace"].get("llm_model", "unknown")
    g_model = g["trace"].get("llm_model", "unknown")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Deep Research Agent — Baseline vs Guided</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0f172a; color: #e2e8f0; line-height: 1.5; }}
  .container {{ max-width: 1300px; margin: 0 auto; padding: 2rem; }}
  h1 {{ font-size: 1.3rem; font-weight: 700; color: #f8fafc; margin-bottom: 0.5rem; }}
  h2 {{ font-size: 0.9rem; font-weight: 600; color: #94a3b8; margin: 2rem 0 1rem; text-transform: uppercase; letter-spacing: 0.08em; }}
  .query-box {{ background: #1e293b; border-radius: 8px; padding: 1rem 1.25rem; margin-bottom: 2rem; font-size: 1rem; color: #f1f5f9; border-left: 3px solid #6366f1; }}
  .cols {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }}
  .col-header {{ display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem; }}
  .mode-badge {{ padding: 0.2rem 0.6rem; border-radius: 4px; font-size: 0.75rem; font-weight: 700; }}
  .badge-baseline {{ background: #312e81; color: #a5b4fc; }}
  .badge-guided {{ background: #14532d; color: #86efac; }}
  .stat-row {{ display: flex; gap: 1.5rem; margin-bottom: 1rem; }}
  .stat {{ background: #1e293b; border-radius: 6px; padding: 0.6rem 1rem; flex: 1; }}
  .stat-val {{ font-size: 1.4rem; font-weight: 700; }}
  .stat-label {{ font-size: 0.7rem; color: #64748b; text-transform: uppercase; }}
  .step-card {{ background: #1e293b; border-radius: 6px; padding: 0.75rem 1rem; margin-bottom: 0.5rem; }}
  .step-header {{ display: flex; gap: 0.75rem; align-items: center; margin-bottom: 0.3rem; }}
  .step-num {{ font-size: 0.7rem; color: #475569; font-weight: 600; min-width: 40px; }}
  .step-action {{ font-size: 0.75rem; font-weight: 600; color: #94a3b8; }}
  .step-result {{ font-size: 0.7rem; font-weight: 700; margin-left: auto; }}
  .step-question {{ font-size: 0.78rem; color: #64748b; line-height: 1.4; }}
  .metric-row {{ background: #1e293b; border-radius: 8px; padding: 1rem 1.25rem; margin-bottom: 0.75rem; }}
  .metric-label strong {{ display: block; font-size: 0.85rem; margin-bottom: 0.2rem; }}
  .metric-explain {{ font-size: 0.72rem; color: #475569; line-height: 1.4; display: block; margin-bottom: 0.75rem; }}
  .bar-group {{ display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.4rem; }}
  .bar-label {{ font-size: 0.7rem; color: #64748b; min-width: 55px; }}
  .bar-track {{ flex: 1; background: #334155; border-radius: 3px; height: 8px; }}
  .bar-fill {{ height: 8px; border-radius: 3px; }}
  .bar-val {{ font-size: 0.78rem; font-weight: 600; min-width: 55px; }}
  .report-box {{ background: #1e293b; border-radius: 8px; padding: 1.25rem; font-size: 0.82rem; color: #cbd5e1; line-height: 1.7; max-height: 600px; overflow-y: auto; scrollbar-width: thin; scrollbar-color: #334155 transparent; }}
  .r-h2 {{ font-size: 1rem; font-weight: 700; color: #f1f5f9; margin: 1.2rem 0 0.4rem; border-bottom: 1px solid #334155; padding-bottom: 0.25rem; }}
  .r-h3 {{ font-size: 0.88rem; font-weight: 700; color: #a5b4fc; margin: 1rem 0 0.3rem; }}
  .r-h4 {{ font-size: 0.82rem; font-weight: 600; color: #7dd3fc; margin: 0.8rem 0 0.2rem; }}
  .r-p {{ margin-bottom: 0.5rem; }}
  .r-gap {{ height: 0.4rem; }}
  li {{ margin-left: 1.2rem; margin-bottom: 0.25rem; }}
  .conflict-card {{ background: #1e293b; border-radius: 6px; padding: 0.75rem 1rem; margin-bottom: 0.5rem; border-left: 3px solid #ef4444; }}
  .conflict-claim {{ font-size: 0.82rem; margin-bottom: 0.3rem; }}
  .conflict-meta {{ font-size: 0.72rem; color: #64748b; }}
  .dim {{ color: #475569; font-size: 0.82rem; }}
  .section {{ margin-bottom: 2.5rem; }}
  .full-width {{ grid-column: 1 / -1; }}
  .insight-box {{ background: #172033; border: 1px solid #334155; border-radius: 8px; padding: 1rem 1.25rem; margin-bottom: 2rem; }}
  .insight-box h3 {{ font-size: 0.8rem; color: #6366f1; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.5rem; }}
  .insight-box p {{ font-size: 0.85rem; color: #94a3b8; line-height: 1.6; }}
</style>
</head>
<body>
<div class="container">

  <h1>Deep Research Agent — Baseline vs. Guided Comparison</h1>
  <div class="query-box">{query}</div>

  <div class="insight-box">
    <h3>What this comparison shows</h3>
    <p>
      Both modes ran on the same query with the same model ({b_model}).
      <strong>Baseline</strong> cycles sub-questions in fixed order, never challenges claims, stops only when budget runs out.
      <strong>Guided</strong> reads the evidence state at each step — prioritizing uncovered angles, challenging high-confidence claims,
      and stopping when evidence is genuinely exhausted.
      The step journeys below show where they diverged and why the metrics differ.
    </p>
  </div>

  <h2>Step Journey</h2>
  <div class="cols section">
    <div>
      <div class="col-header">
        <span class="mode-badge badge-baseline">BASELINE</span>
        <span style="font-size:0.8rem;color:#64748b">{b_steps} steps · {b_groups} claim groups · {b_disputes} disputes</span>
      </div>
      {_step_journey(b, "baseline")}
    </div>
    <div>
      <div class="col-header">
        <span class="mode-badge badge-guided">GUIDED</span>
        <span style="font-size:0.8rem;color:#64748b">{g_steps} steps · {g_groups} claim groups · {g_disputes} disputes</span>
      </div>
      {_step_journey(g, "guided")}
    </div>
  </div>

  <h2>Evaluation Metrics — What Each Number Means</h2>
  <div class="section">
    {_metric_comparison(b, g)}
  </div>

  <h2>Conflicts Surfaced</h2>
  <div class="cols section">
    <div>
      <div class="col-header"><span class="mode-badge badge-baseline">BASELINE</span></div>
      {_disputes_section(b)}
    </div>
    <div>
      <div class="col-header"><span class="mode-badge badge-guided">GUIDED</span></div>
      {_disputes_section(g)}
    </div>
  </div>

  <h2>Generated Reports</h2>
  <div class="cols section">
    <div>
      <div class="col-header"><span class="mode-badge badge-baseline">BASELINE</span></div>
      <div class="report-box">{_render_report(b)}</div>
    </div>
    <div>
      <div class="col-header"><span class="mode-badge badge-guided">GUIDED</span></div>
      <div class="report-box">{_render_report(g)}</div>
    </div>
  </div>

</div>
</body>
</html>"""
