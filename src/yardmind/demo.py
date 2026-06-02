from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

from yardmind.loader import load_instance
from yardmind.official import OfficialSupportError
from yardmind.official_compare import generate_official_constructive_comparison
from yardmind.solver.feasibility import FeasibilityChecker
from yardmind.solver.local_search import LocalSearchSolver
from yardmind.solver.constructive import ConstructiveSolver
from yardmind.solver.state import ObjectiveBreakdown, SolutionState


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a static YardMind demo report.")
    parser.add_argument(
        "--instance",
        type=Path,
        default=Path("examples/realistic-improvement-instance.json"),
        help="Development instance to visualize.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/demo/index.html"),
        help="Output HTML path for the generated demo report.",
    )
    parser.add_argument("--iterations", type=int, default=8, help="Local-search iterations for the demo.")
    parser.add_argument("--seed", type=int, default=11, help="Seed for the demo local-search run.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    output_path = generate_demo_report(
        instance_path=args.instance,
        output_path=args.output,
        iterations=args.iterations,
        seed=args.seed,
    )
    print(f"Wrote demo report to {output_path}")


def generate_demo_report(
    instance_path: Path,
    output_path: Path,
    *,
    iterations: int = 8,
    seed: int = 11,
) -> Path:
    repo_root = Path(__file__).resolve().parents[2]
    instance = load_instance(instance_path)
    checker = FeasibilityChecker(instance)
    constructive_state = ConstructiveSolver(checker=checker).solve(instance)
    search_solver = LocalSearchSolver(checker=checker, iterations=iterations, seed=seed)
    search_state = search_solver.solve(instance)
    official_error: str | None = None
    official_summary: dict[str, object] | None = None
    report_evidence = _load_report_evidence(repo_root)

    try:
        official_summary = generate_official_constructive_comparison(
            repo_root,
            output_root=output_path.parent / "official-comparison",
        )
    except OfficialSupportError as exc:
        official_error = str(exc)

    html_output = _build_demo_html(
        instance_name=instance.name or instance_path.stem,
        yard_width=instance.yard.width,
        yard_height=instance.yard.height,
        block_count=len(instance.blocks),
        constructive_state=constructive_state,
        search_state=search_state,
        search_iterations=iterations,
        seed=seed,
        diagnostics=search_solver.last_diagnostics,
        official_summary=official_summary,
        official_error=official_error,
        report_evidence=report_evidence,
    )
    demo_snapshot = _build_demo_snapshot(
        instance_name=instance.name or instance_path.stem,
        yard_width=instance.yard.width,
        yard_height=instance.yard.height,
        block_count=len(instance.blocks),
        constructive_state=constructive_state,
        search_state=search_state,
        search_iterations=iterations,
        seed=seed,
        diagnostics=search_solver.last_diagnostics,
        official_summary=official_summary,
        official_error=official_error,
        report_evidence=report_evidence,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_output, encoding="utf-8")
    output_path.with_name("demo-data.json").write_text(
        json.dumps(demo_snapshot, indent=2),
        encoding="utf-8",
    )
    web_public_path = repo_root / "web" / "public" / "demo-data.json"
    if web_public_path.parent.exists():
        web_public_path.write_text(json.dumps(demo_snapshot, indent=2), encoding="utf-8")
    return output_path


def _build_demo_snapshot(
    *,
    instance_name: str,
    yard_width: int,
    yard_height: int,
    block_count: int,
    constructive_state: SolutionState,
    search_state: SolutionState,
    search_iterations: int,
    seed: int,
    diagnostics,
    official_summary: dict[str, object] | None,
    official_error: str | None,
    report_evidence: dict[str, object] | None,
) -> dict[str, object]:
    return {
        "instance_name": instance_name,
        "yard": {"width": yard_width, "height": yard_height},
        "block_count": block_count,
        "search": {
            "iterations": search_iterations,
            "seed": seed,
            "delta": search_state.objective_value - constructive_state.objective_value,
            "history": [
                {
                    "iteration": record.iteration,
                    "destroy_operator": record.destroy_operator,
                    "repair_operator": record.repair_operator,
                    "candidate_feasible": record.candidate_feasible,
                    "candidate_objective": record.candidate_objective,
                    "best_objective": record.best_objective,
                    "accepted": record.accepted,
                }
                for record in diagnostics.history
            ],
        },
        "constructive": _serialize_solution_state(constructive_state),
        "search_solution": _serialize_solution_state(search_state),
        "allocation_trace": _build_allocation_trace(constructive_state, search_state),
        "official": {
            "summary": official_summary,
            "error": official_error,
        },
        "report_evidence": report_evidence,
    }


def _load_report_evidence(repo_root: Path) -> dict[str, object] | None:
    development_evidence = _load_development_report_evidence(repo_root)
    official_evidence = _load_official_report_evidence(repo_root)
    if development_evidence is None and official_evidence is None:
        return None

    return {
        "development": development_evidence,
        "official": official_evidence,
    }


def _load_development_report_evidence(repo_root: Path) -> dict[str, object] | None:
    summary = _read_summary_block(repo_root / "artifacts" / "report" / "realistic_default" / "summary.json")
    if summary is None:
        return None

    return {
        "runs": summary.get("runs"),
        "constructive_mean": summary.get("constructive_mean"),
        "search_mean": summary.get("search_mean"),
        "search_best": summary.get("search_best"),
        "improved_runs": summary.get("improved_runs"),
    }


def _load_official_report_evidence(repo_root: Path) -> dict[str, object] | None:
    public_sample = _load_official_report_summary(repo_root / "artifacts" / "report" / "official_default" / "summary.json")
    proof_case = _load_official_report_summary(repo_root / "artifacts" / "report" / "official_search_proof" / "summary.json")
    quality_case = _load_official_report_summary(repo_root / "artifacts" / "report" / "official_search_quality" / "summary.json")
    if public_sample is None and proof_case is None and quality_case is None:
        return None

    return {
        "public_sample": public_sample,
        "proof_case": proof_case,
        "quality_case": quality_case,
    }


def _load_official_report_summary(summary_path: Path) -> dict[str, object] | None:
    payload = _read_json_payload(summary_path)
    if payload is None:
        return None

    summary = payload.get("summary")
    if not isinstance(summary, dict):
        return None

    return {
        "instance": payload.get("instance"),
        "runs": summary.get("runs"),
        "delegated_feasible_runs": summary.get("delegated_feasible_runs"),
        "native_feasible_runs": summary.get("native_feasible_runs"),
        "search_feasible_runs": summary.get("search_feasible_runs"),
        "delegated_objective_mean": summary.get("delegated_objective_mean"),
        "native_objective_mean": summary.get("native_objective_mean"),
        "search_objective_mean": summary.get("search_objective_mean"),
        "objective_delta_mean": summary.get("objective_delta_mean"),
        "search_vs_delegated_delta_mean": summary.get("search_vs_delegated_delta_mean"),
        "search_vs_native_delta_mean": summary.get("search_vs_native_delta_mean"),
        "delegated_runtime_mean": summary.get("delegated_runtime_mean"),
        "native_runtime_mean": summary.get("native_runtime_mean"),
        "search_runtime_mean": summary.get("search_runtime_mean"),
        "native_better_or_equal_runs": summary.get("native_better_or_equal_runs"),
        "native_faster_runs": summary.get("native_faster_runs"),
        "search_better_or_equal_than_delegated_runs": summary.get("search_better_or_equal_than_delegated_runs"),
        "search_better_or_equal_than_native_runs": summary.get("search_better_or_equal_than_native_runs"),
        "search_faster_than_delegated_runs": summary.get("search_faster_than_delegated_runs"),
    }


def _read_summary_block(summary_path: Path) -> dict[str, object] | None:
    payload = _read_json_payload(summary_path)
    if payload is None:
        return None

    summary = payload.get("summary")
    return summary if isinstance(summary, dict) else None


def _read_json_payload(summary_path: Path) -> dict[str, object] | None:
    if not summary_path.exists():
        return None

    try:
        payload = json.loads(summary_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    return payload if isinstance(payload, dict) else None


def _serialize_solution_state(state: SolutionState) -> dict[str, object]:
    return {
        "objective_value": state.objective_value,
        "objective_breakdown": {
            "area_utilization": state.objective_breakdown.area_utilization,
            "lateness_penalty": state.objective_breakdown.lateness_penalty,
            "retrieval_risk_penalty": state.objective_breakdown.retrieval_risk_penalty,
            "congestion_penalty": state.objective_breakdown.congestion_penalty,
        },
        "placements": [
            {
                "block_id": placement.block_id,
                "x": placement.x,
                "y": placement.y,
                "start_time": placement.start_time,
                "end_time": placement.end_time,
                "rotation": placement.rotation,
                "width": state.instance.block_by_id(placement.block_id).rotated_dimensions(placement.rotation)[0],
                "height": state.instance.block_by_id(placement.block_id).rotated_dimensions(placement.rotation)[1],
            }
            for placement in state.placements
        ],
    }


def _build_allocation_trace(constructive_state: SolutionState, search_state: SolutionState) -> list[dict[str, object]]:
    constructive_placements = _build_state_placements(constructive_state)
    search_placements = _build_state_placements(search_state)
    constructive_by_id = {placement["block_id"]: placement for placement in constructive_placements}

    core_center_x = sum(float(placement["x"]) + float(placement["width"]) / 2.0 for placement in search_placements) / max(1, len(search_placements))
    core_center_y = sum(float(placement["y"]) + float(placement["height"]) / 2.0 for placement in search_placements) / max(1, len(search_placements))

    rows: list[dict[str, object]] = []
    for placement in search_placements:
        original = constructive_by_id.get(str(placement["block_id"]))
        if original is None:
            continue

        moved = int(original["x"]) != int(placement["x"]) or int(original["y"]) != int(placement["y"])
        access_delta = int(placement["x"]) - int(original["x"])
        conflict_delta = _overlap_count(original, constructive_placements) - _overlap_count(placement, search_placements)
        original_core_distance = abs((int(original["x"]) + int(original["width"]) / 2.0) - core_center_x) + abs((int(original["y"]) + int(original["height"]) / 2.0) - core_center_y)
        current_core_distance = abs((int(placement["x"]) + int(placement["width"]) / 2.0) - core_center_x) + abs((int(placement["y"]) + int(placement["height"]) / 2.0) - core_center_y)
        core_delta = original_core_distance - current_core_distance
        signal_score = access_delta * 0.7 + conflict_delta * 1.2 + core_delta * 0.25

        if moved:
            if conflict_delta > 0:
                reason = "reduced overlapping pressure in a busy zone"
            elif access_delta > 0:
                reason = "opened more access-edge space for future retrieval"
            elif core_delta > 0:
                reason = "tightened the storage core without adding conflict"
            else:
                reason = "repositioned to maintain a more stable yard shape"
        elif signal_score >= 0:
            reason = "kept stable because the constructive placement already aligned with the target structure"
        else:
            reason = "kept stable because moving it would not improve the local structure"

        rows.append(
            {
                "block_id": placement["block_id"],
                "from_x": original["x"],
                "from_y": original["y"],
                "to_x": placement["x"],
                "to_y": placement["y"],
                "moved": moved,
                "access_delta": access_delta,
                "conflict_delta": conflict_delta,
                "core_delta": core_delta,
                "signal_score": signal_score,
                "reason": reason,
            }
        )

    return rows


def _build_state_placements(state: SolutionState) -> list[dict[str, object]]:
    return [
        {
            "block_id": placement.block_id,
            "x": placement.x,
            "y": placement.y,
            "start_time": placement.start_time,
            "end_time": placement.end_time,
            "width": state.instance.block_by_id(placement.block_id).rotated_dimensions(placement.rotation)[0],
            "height": state.instance.block_by_id(placement.block_id).rotated_dimensions(placement.rotation)[1],
        }
        for placement in state.placements
    ]


def _overlap_count(target: dict[str, object], placements: list[dict[str, object]]) -> int:
    count = 0
    for candidate in placements:
        if candidate["block_id"] == target["block_id"]:
            continue

        time_overlap = int(target["start_time"]) < int(candidate["end_time"]) and int(candidate["start_time"]) < int(target["end_time"])
        x_overlap = int(target["x"]) < int(candidate["x"]) + int(candidate["width"]) and int(candidate["x"]) < int(target["x"]) + int(target["width"])
        y_overlap = int(target["y"]) < int(candidate["y"]) + int(candidate["height"]) and int(candidate["y"]) < int(target["y"]) + int(target["height"])
        if time_overlap and x_overlap and y_overlap:
            count += 1

    return count


def _build_demo_html(
    *,
    instance_name: str,
    yard_width: int,
    yard_height: int,
    block_count: int,
    constructive_state: SolutionState,
    search_state: SolutionState,
    search_iterations: int,
    seed: int,
    diagnostics,
    official_summary: dict[str, object] | None,
    official_error: str | None,
    report_evidence: dict[str, object] | None,
) -> str:
    search_delta = search_state.objective_value - constructive_state.objective_value
    official_section = _render_official_comparison(official_summary, official_error)
    iteration_rows = "\n".join(
        (
            "<tr>"
            f"<td>{record.iteration}</td>"
            f"<td>{html.escape(record.destroy_operator)}</td>"
            f"<td>{html.escape(record.repair_operator)}</td>"
            f"<td>{'yes' if record.candidate_feasible else 'no'}</td>"
            f"<td>{record.candidate_objective:.4f}</td>"
            f"<td>{record.best_objective:.4f}</td>"
            f"<td>{'yes' if record.accepted else 'no'}</td>"
            "</tr>"
        )
        for record in diagnostics.history
    )

    return f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>YardMind Demo</title>
  <style>
    :root {{
      --bg: #f5f1e8;
      --panel: #fffaf1;
      --ink: #1f2933;
      --muted: #52606d;
      --accent: #0b6e4f;
      --accent-2: #f08a24;
      --edge: #d9cbb6;
      --good: #1f7a4c;
      --warn: #a65a00;
      --shadow: 0 18px 40px rgba(31, 41, 51, 0.08);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(240, 138, 36, 0.16), transparent 30%),
        radial-gradient(circle at top right, rgba(11, 110, 79, 0.12), transparent 24%),
        linear-gradient(180deg, #f8f5ef 0%, var(--bg) 100%);
    }}
    .shell {{ max-width: 1180px; margin: 0 auto; padding: 32px 24px 56px; }}
    .hero {{ display: grid; gap: 20px; margin-bottom: 28px; }}
    .eyebrow {{ text-transform: uppercase; letter-spacing: 0.16em; font-size: 12px; color: var(--accent); font-weight: 700; }}
    h1 {{ margin: 0; font-size: clamp(38px, 6vw, 72px); line-height: 0.94; }}
    .lead {{ margin: 0; max-width: 760px; color: var(--muted); font-size: 18px; line-height: 1.5; }}
    .grid {{ display: grid; gap: 18px; }}
    .cards {{ grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); margin-bottom: 28px; }}
    .card, .panel {{ background: var(--panel); border: 1px solid var(--edge); border-radius: 22px; box-shadow: var(--shadow); }}
    .card {{ padding: 18px 18px 16px; }}
    .metric {{ font-size: 30px; font-weight: 700; margin-top: 8px; }}
    .label {{ color: var(--muted); font-size: 13px; text-transform: uppercase; letter-spacing: 0.08em; }}
    .panels {{ grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); margin-bottom: 28px; }}
    .panel {{ padding: 18px; }}
    .panel h2 {{ margin: 0 0 8px; font-size: 24px; }}
    .panel p {{ margin: 0 0 16px; color: var(--muted); line-height: 1.45; }}
    .yard {{ width: 100%; height: auto; border-radius: 18px; background: #fcf7ef; border: 1px solid var(--edge); }}
    .legend {{ display: flex; flex-wrap: wrap; gap: 10px; margin-top: 12px; color: var(--muted); font-size: 13px; }}
    .pill {{ padding: 6px 10px; border-radius: 999px; background: rgba(11, 110, 79, 0.08); }}
    .official-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 14px; margin-top: 14px; }}
    .bay-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; margin-top: 12px; }}
    .bay-card {{ border: 1px solid var(--edge); border-radius: 18px; padding: 12px; background: #fffdf8; }}
    .bay-title {{ margin: 0 0 8px; font-size: 15px; font-weight: 700; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
    th, td {{ padding: 10px 8px; border-bottom: 1px solid var(--edge); text-align: left; }}
    th {{ color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: 0.08em; }}
    .delta-positive {{ color: var(--good); }}
    .delta-negative {{ color: var(--warn); }}
    .footer {{ margin-top: 18px; color: var(--muted); font-size: 14px; }}
  </style>
</head>
<body>
  <main class=\"shell\">
    <section class=\"hero\">
      <div class=\"eyebrow\">YardMind Presentation Layer</div>
      <h1>Retrieval-aware yard planning you can actually show.</h1>
      <p class=\"lead\">This static demo page visualizes the current development solver path for <strong>{html.escape(instance_name)}</strong>, compares constructive versus local-search results, and turns the CLI-first prototype into something you can open in a browser for demos and pitch reviews.</p>
    </section>

    <section class=\"grid cards\">
      <article class=\"card\"><div class=\"label\">Instance</div><div class=\"metric\">{html.escape(instance_name)}</div></article>
      <article class=\"card\"><div class=\"label\">Blocks</div><div class=\"metric\">{block_count}</div></article>
      <article class=\"card\"><div class=\"label\">Constructive Objective</div><div class=\"metric\">{constructive_state.objective_value:.4f}</div></article>
      <article class=\"card\"><div class=\"label\">Search Objective</div><div class=\"metric\">{search_state.objective_value:.4f}</div></article>
      <article class=\"card\"><div class=\"label\">Search Delta</div><div class=\"metric {'delta-positive' if search_delta >= 0 else 'delta-negative'}\">{search_delta:+.4f}</div></article>
      <article class=\"card\"><div class=\"label\">Search Config</div><div class=\"metric\">{search_iterations} iters / seed {seed}</div></article>
    </section>

    <section class=\"grid panels\">
      <article class=\"panel\">
        <h2>Constructive Baseline</h2>
        <p>Fast feasibility-first placement for the development yard.</p>
        {_render_yard_svg(yard_width, yard_height, constructive_state)}
        {_render_breakdown(constructive_state.objective_breakdown)}
      </article>
      <article class="panel">
        <h2>Official Constructive Comparison</h2>
        <p>The same browser view now summarizes delegated versus YardMind-native official constructive results on the public official sample.</p>
        {official_section}
      </article>
      <article class=\"panel\">
        <h2>Local Search Incumbent</h2>
        <p>Destroy/repair search with best feasible incumbent preservation.</p>
        {_render_yard_svg(yard_width, yard_height, search_state)}
        {_render_breakdown(search_state.objective_breakdown)}
      </article>
    </section>

    <section class=\"panel\">
      <h2>Search Trace</h2>
      <p>The current development search loop is still heuristic, but this makes the operator flow visible for demos.</p>
      <table>
        <thead>
          <tr>
            <th>Iter</th>
            <th>Destroy</th>
            <th>Repair</th>
            <th>Feasible</th>
            <th>Candidate Obj</th>
            <th>Best Obj</th>
            <th>Accepted</th>
          </tr>
        </thead>
        <tbody>
          {iteration_rows}
        </tbody>
      </table>
        <div class="footer">The demo now combines the development solver story with the current official constructive comparison story in one browser-viewable artifact.</div>
    </section>
  </main>
</body>
</html>
"""


def _render_official_comparison(
    official_summary: dict[str, object] | None,
    official_error: str | None,
) -> str:
    if official_summary is None:
        return (
            '<div class="legend">'
            f'<span class="pill">Official comparison unavailable: {html.escape(official_error or "unknown error")}</span>'
            "</div>"
        )

    delegated = official_summary["delegated_baseline"]
    native = official_summary["native_constructive"]
    bays = official_summary.get("bays", [])
    objective_delta = float(native["objective"]) - float(delegated["objective"])
    runtime_ratio = float(delegated["runtime_seconds"]) / max(float(native["runtime_seconds"]), 1e-9)

    return (
        '<div class="legend">'
        f'<span class="pill">Official instance {html.escape(str(official_summary["instance"]))}</span>'
        f'<span class="pill">Delegated Baseline obj {float(delegated["objective"]):.4f}</span>'
        f'<span class="pill">Native Constructive obj {float(native["objective"]):.4f}</span>'
        f'<span class="pill">Objective delta {objective_delta:+.4f}</span>'
        f'<span class="pill">Delegated runtime {float(delegated["runtime_seconds"]):.6f}s</span>'
        f'<span class="pill">Native runtime {float(native["runtime_seconds"]):.6f}s</span>'
        f'<span class="pill">Runtime ratio {runtime_ratio:.2f}x</span>'
        f'<span class="pill">Native feasible {"yes" if native["feasible"] else "no"}</span>'
        "</div>"
        '<div class="official-grid">'
        + _render_official_variant("Delegated Baseline", delegated, bays)
        + _render_official_variant("Native Constructive", native, bays)
        + "</div>"
    )


def _render_official_variant(
    label: str,
    variant: dict[str, object],
    bays: list[dict[str, object]],
) -> str:
    assignments = variant.get("assignments", [])
    assignment_count = int(variant.get("assignment_count", len(assignments)))
    bay_cards = "".join(_render_official_bay_card(bay, assignments) for bay in bays)
    return (
        '<div class="bay-card">'
        f'<div class="bay-title">{html.escape(label)}</div>'
        f'<div class="legend"><span class="pill">Assignments {assignment_count}</span><span class="pill">Stage {variant["stage"]}</span></div>'
        f'<div class="bay-grid">{bay_cards}</div>'
        "</div>"
    )


def _render_official_bay_card(
    bay: dict[str, object],
    assignments: list[dict[str, object]],
) -> str:
    bay_id = int(bay["bay_id"])
    bay_assignments = [assignment for assignment in assignments if int(assignment["bay_id"]) == bay_id]
    return (
        '<div class="bay-card">'
        f'<div class="bay-title">Bay {bay_id}</div>'
        + _render_official_bay_svg(int(bay["width"]), int(bay["height"]), bay_assignments)
        + "</div>"
    )


def _render_official_bay_svg(
    bay_width: int,
    bay_height: int,
    assignments: list[dict[str, object]],
) -> str:
    scale = max(22, min(34, int(220 / max(bay_width, 1))))
    width = bay_width * scale
    height = bay_height * scale
    palette = ["#0b6e4f", "#f08a24", "#8f5ea2", "#2d6cdf", "#c44536", "#3a7d44"]
    blocks_markup: list[str] = []

    for index, assignment in enumerate(assignments):
        rect_width = int(assignment["width"]) * scale
        rect_height = int(assignment["height"]) * scale
        x = int(assignment["x"]) * scale
        y = height - (int(assignment["y"]) + int(assignment["height"])) * scale
        fill = palette[index % len(palette)]
        blocks_markup.append(
            (
                f'<g><rect x="{x}" y="{y}" width="{rect_width}" height="{rect_height}" '
                f'fill="{fill}" fill-opacity="0.88" rx="8" />'
                f'<text x="{x + 8}" y="{y + 18}" font-size="11" fill="#fff" font-weight="700">'
                f'Block {int(assignment["block_id"])}'
                f'</text>'
                f'<text x="{x + 8}" y="{y + 34}" font-size="10" fill="#fff">'
                f't={int(assignment["entry_time"])}-{assignment["exit_time"]}</text></g>'
            )
        )

    return (
        f'<svg class="yard" viewBox="0 0 {width} {height}" role="img" aria-label="Official bay layout">'
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#f7efe2" stroke="#d9cbb6" stroke-width="2" rx="14" />'
        + "".join(blocks_markup)
        + "</svg>"
    )

def _render_breakdown(breakdown: ObjectiveBreakdown) -> str:
    return (
        '<div class="legend">'
        f'<span class="pill">Area {breakdown.area_utilization:.4f}</span>'
        f'<span class="pill">Lateness {breakdown.lateness_penalty:.2f}</span>'
        f'<span class="pill">Retrieval Risk {breakdown.retrieval_risk_penalty:.2f}</span>'
        f'<span class="pill">Congestion {breakdown.congestion_penalty:.2f}</span>'
        "</div>"
    )


def _render_yard_svg(yard_width: int, yard_height: int, state: SolutionState) -> str:
    scale = 34
    width = yard_width * scale
    height = yard_height * scale
    blocks_markup: list[str] = []
    palette = ["#0b6e4f", "#f08a24", "#8f5ea2", "#2d6cdf", "#c44536", "#3a7d44"]

    for index, placement in enumerate(state.placements):
        block = state.instance.block_by_id(placement.block_id)
        block_width, block_height = block.rotated_dimensions(placement.rotation)
        x = placement.x * scale
        y = height - (placement.y + block_height) * scale
        fill = palette[index % len(palette)]
        blocks_markup.append(
            f'<g><rect x="{x}" y="{y}" width="{block_width * scale}" height="{block_height * scale}" fill="{fill}" fill-opacity="0.88" rx="10" />'
            f'<text x="{x + 10}" y="{y + 24}" font-size="16" fill="#fff" font-weight="700">{html.escape(block.block_id)}</text>'
            f'<text x="{x + 10}" y="{y + 44}" font-size="12" fill="#fff">t={placement.start_time}-{placement.end_time}</text></g>'
        )

    return (
        f'<svg class="yard" viewBox="0 0 {width} {height}" role="img" aria-label="Yard layout">'
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#f7efe2" stroke="#d9cbb6" stroke-width="3" rx="18" />'
        + "".join(blocks_markup)
        + "</svg>"
    )


if __name__ == "__main__":
    main()