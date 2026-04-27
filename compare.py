#!/usr/bin/env python3
"""
Aggregate and compare metrics across all completed runs.

Usage:
  python compare.py                    # reads from runs/
  python compare.py --dir runs/        # explicit directory
  python compare.py --mode guided      # filter by mode
  python compare.py --pairs            # also generate rich side-by-side HTML for each baseline+guided pair
"""
import argparse
import json
from pathlib import Path


def load_traces(runs_dir: Path, mode_filter: str = None) -> list:
    traces = []
    for trace_file in sorted(runs_dir.rglob("run_trace.json")):
        try:
            data = json.loads(trace_file.read_text())
            if mode_filter and data.get("mode") != mode_filter:
                continue
            data["_path"] = str(trace_file.parent.relative_to(runs_dir))
            data["_run_dir"] = str(trace_file.parent)
            traces.append(data)
        except Exception:
            continue
    return traces


def generate_pair_comparisons(traces: list, runs_dir: Path) -> None:
    """For each query that has both baseline and guided runs, generate a rich comparison dashboard."""
    from src.agent.comparison_dashboard import generate_comparison

    # Group by parent directory (the query-slug dir contains baseline/ and guided/ as siblings)
    by_parent: dict = {}
    for t in traces:
        run_dir = Path(t["_run_dir"])
        if run_dir.name in ("baseline", "guided"):
            parent = run_dir.parent
            key = str(parent)
            if key not in by_parent:
                by_parent[key] = {}
            by_parent[key][run_dir.name] = run_dir

    pairs_generated = 0
    for parent_key, modes in by_parent.items():
        if "baseline" not in modes or "guided" not in modes:
            continue
        parent = Path(parent_key)
        output_path = parent / "comparison.html"
        try:
            generate_comparison(modes["baseline"], modes["guided"], output_path)
            pairs_generated += 1
        except Exception as e:
            print(f"  Could not generate comparison for {parent.name}: {e}")

    if pairs_generated == 0:
        print("No baseline+guided pairs found. Run an ablation experiment first:"
              "\n  python experiment.py --config experiments/ablation.yaml")


def print_table(traces: list) -> None:
    if not traces:
        print("No completed runs found.")
        return

    header = (
        f"{'path':<40} {'mode':<10} {'model':<18} {'steps':>5} "
        f"{'cov':>5} {'eff':>5} {'ehs':>5} {'sgr':>5} {'udr':>5} {'disputes':>8} {'term':<22}"
    )
    print("=" * len(header))
    print("Cross-Run Comparison")
    print("  cov=coverage_completeness  eff=search_efficiency  ehs=epistemic_honesty_score  sgr=summary_grounding_rate  udr=unresolved_disclosure_rate")
    print("=" * len(header))
    print(header)
    print("-" * len(header))

    for r in traces:
        print(
            f"{r['_path'][:40]:<40} "
            f"{r.get('mode', ''):<10} "
            f"{r.get('llm_model', 'unknown')[:18]:<18} "
            f"{r.get('total_steps', 0):>5} "
            f"{r.get('coverage_completeness', 0):>5.0%} "
            f"{r.get('search_efficiency', 0):>5.0%} "
            f"{r.get('epistemic_honesty_score', 0):>5.0%} "
            f"{r.get('summary_grounding_rate', 0):>5.0%} "
            f"{r.get('unresolved_disclosure_rate', 0):>5.0%} "
            f"{r.get('disputes', 0):>8} "
            f"{r.get('termination_reason', ''):<22}"
        )

    print("=" * len(header))

    modes = {}
    for r in traces:
        m = r.get("mode", "unknown")
        if m not in modes:
            modes[m] = []
        modes[m].append(r)

    if len(modes) > 1:
        print("\nAverage by mode:")
        metrics = [
            "coverage_completeness",
            "search_efficiency",
            "epistemic_honesty_score",
            "summary_grounding_rate",
            "unresolved_disclosure_rate",
        ]
        print(f"  {'mode':<12}", end="")
        for m in metrics:
            print(f"  {m[:6]:>6}", end="")
        print()
        for mode, runs in sorted(modes.items()):
            print(f"  {mode:<12}", end="")
            for m in metrics:
                avg = sum(r.get(m, 0) for r in runs) / len(runs)
                print(f"  {avg:>6.0%}", end="")
            print()


def generate_comparison_html(traces: list, output_path: Path) -> None:
    metrics = [
        "coverage_completeness",
        "search_efficiency",
        "epistemic_honesty_score",
        "summary_grounding_rate",
        "unresolved_disclosure_rate",
    ]
    metric_labels = [
        "Coverage",
        "Efficiency",
        "Epistemic Honesty",
        "Summary Grounding",
        "Unresolved Disclosure",
    ]
    colors = {"baseline": "#6366f1", "guided": "#22c55e"}

    rows = ""
    for r in traces:
        mode = r.get("mode", "")
        color = colors.get(mode, "#94a3b8")
        rows += f"""<tr>
          <td style="font-size:0.75rem;color:#94a3b8">{r['_path'][:45]}</td>
          <td><span style="color:{color};font-weight:600">{mode}</span></td>
          <td style="font-size:0.8rem">{r.get('llm_model','')[:18]}</td>
          <td>{r.get('total_steps',0)}</td>
          {''.join(f"<td style='color:{'#22c55e' if r.get(m,0)>=0.7 else '#f59e0b' if r.get(m,0)>=0.4 else '#ef4444'};font-weight:600'>{r.get(m,0):.0%}</td>" for m in metrics)}
          <td style="font-size:0.75rem">{r.get('termination_reason','')}</td>
        </tr>"""

    chart_data = json.dumps([
        {
            "label": f"{r.get('mode','')} / {r.get('llm_model','')[:12]} / {r['_path'].split('/')[0]}",
            "values": [round(r.get(m, 0) * 100) for m in metrics],
            "color": colors.get(r.get("mode", ""), "#94a3b8"),
        }
        for r in traces
    ])

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Deep Research Agent — Comparison Dashboard</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0f172a; color: #e2e8f0; }}
  .container {{ max-width: 1200px; margin: 0 auto; padding: 2rem; }}
  h1 {{ font-size: 1.5rem; font-weight: 700; color: #f8fafc; margin-bottom: 0.25rem; }}
  h2 {{ font-size: 1rem; font-weight: 600; color: #94a3b8; margin: 2rem 0 1rem; text-transform: uppercase; letter-spacing: 0.05em; }}
  .data-table {{ width: 100%; border-collapse: collapse; font-size: 0.85rem; background: #1e293b; border-radius: 8px; overflow: hidden; }}
  .data-table th {{ background: #334155; padding: 0.6rem 0.8rem; text-align: left; font-size: 0.72rem; text-transform: uppercase; color: #94a3b8; }}
  .data-table td {{ padding: 0.6rem 0.8rem; border-bottom: 1px solid #334155; }}
  .data-table tr:last-child td {{ border-bottom: none; }}
  .chart-container {{ background: #1e293b; border-radius: 8px; padding: 1.5rem; margin-bottom: 1.5rem; }}
  canvas {{ max-height: 320px; }}
</style>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
</head>
<body>
<div class="container">
  <h1>Deep Research Agent — Cross-Run Comparison</h1>
  <p style="color:#64748b;margin-bottom:2rem;font-size:0.85rem">{len(traces)} runs loaded</p>

  <h2>Metrics Chart</h2>
  <div class="chart-container">
    <canvas id="chart"></canvas>
  </div>

  <h2>All Runs</h2>
  <table class="data-table">
    <thead><tr>
      <th>Path</th><th>Mode</th><th>Model</th><th>Steps</th>
      {''.join(f'<th>{l}</th>' for l in metric_labels)}
      <th>Termination</th>
    </tr></thead>
    <tbody>{rows}</tbody>
  </table>
</div>
<script>
const data = {chart_data};
const labels = {json.dumps(metric_labels)};
new Chart(document.getElementById('chart'), {{
  type: 'bar',
  data: {{
    labels: labels,
    datasets: data.map(d => ({{
      label: d.label,
      data: d.values,
      backgroundColor: d.color + 'cc',
      borderColor: d.color,
      borderWidth: 1,
      borderRadius: 4,
    }}))
  }},
  options: {{
    responsive: true,
    plugins: {{ legend: {{ labels: {{ color: '#e2e8f0' }} }} }},
    scales: {{
      x: {{ ticks: {{ color: '#94a3b8' }}, grid: {{ color: '#334155' }} }},
      y: {{ min: 0, max: 100, ticks: {{ color: '#94a3b8', callback: v => v + '%' }}, grid: {{ color: '#334155' }} }}
    }}
  }}
}});
</script>
</body>
</html>"""
    output_path.write_text(html)
    print(f"Comparison dashboard → {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare metrics across all completed runs")
    parser.add_argument("--dir", default="runs", help="Root runs directory")
    parser.add_argument("--mode", help="Filter by mode (baseline or guided)")
    parser.add_argument("--html", help="Write aggregate comparison dashboard to this HTML file")
    parser.add_argument("--pairs", action="store_true",
                        help="Generate rich side-by-side comparison for each baseline+guided pair")
    args = parser.parse_args()

    runs_dir = Path(args.dir)
    if not runs_dir.exists():
        print(f"No runs directory found at {runs_dir}")
        return

    traces = load_traces(runs_dir, mode_filter=args.mode)
    print_table(traces)

    html_out = Path(args.html) if args.html else runs_dir / "comparison.html"
    if traces:
        generate_comparison_html(traces, html_out)

    if args.pairs:
        print("\nGenerating side-by-side pair comparisons…")
        generate_pair_comparisons(traces, runs_dir)


if __name__ == "__main__":
    main()
