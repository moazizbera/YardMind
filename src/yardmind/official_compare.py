from __future__ import annotations

import json
from pathlib import Path
from time import perf_counter

from yardmind.loader import load_instance
from yardmind.official import (
    solve_official_constructive,
    solve_official_constructive_native,
    solve_official_search,
    validate_official_solution,
)


def generate_official_constructive_comparison(
    repo_root: Path,
    output_root: Path | None = None,
    instance_path: Path | None = None,
    timelimit: float = 5.0,
) -> dict[str, object]:
    if instance_path is None:
        instance_path = repo_root / "examples" / "official-search-quality-instance.json"
    if output_root is None:
        output_root = repo_root / "artifacts" / "official" / "comparison"

    instance = load_instance(instance_path, input_format="official")
    problem = instance.metadata["raw_problem"]

    delegated_solution, delegated_runtime = _timed_run(
        lambda: solve_official_constructive(problem, timelimit=timelimit)
    )
    native_solution, native_runtime = _timed_run(
        lambda: solve_official_constructive_native(problem, timelimit=timelimit)
    )
    search_solution, search_runtime = _timed_run(
        lambda: solve_official_search(problem, timelimit=timelimit)
    )

    delegated_result = validate_official_solution(problem, delegated_solution)
    native_result = validate_official_solution(problem, native_solution)
    search_result = validate_official_solution(problem, search_solution)

    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "delegated_baseline_solution.json").write_text(
        json.dumps(delegated_solution, indent=2),
        encoding="utf-8",
    )
    (output_root / "native_constructive_solution.json").write_text(
        json.dumps(native_solution, indent=2),
        encoding="utf-8",
    )
    (output_root / "official_search_solution.json").write_text(
        json.dumps(search_solution, indent=2),
        encoding="utf-8",
    )

    summary = {
        "instance": instance.name,
        "bays": [
            {"bay_id": bay_id, "width": bay["width"], "height": bay["height"]}
            for bay_id, bay in enumerate(problem["bays"])
        ],
        "delegated_baseline": _serialize_result(
            delegated_result,
            delegated_runtime,
            problem=problem,
            solution=delegated_solution,
        ),
        "native_constructive": _serialize_result(
            native_result,
            native_runtime,
            problem=problem,
            solution=native_solution,
        ),
        "official_search": _serialize_result(
            search_result,
            search_runtime,
            problem=problem,
            solution=search_solution,
        ),
    }
    (output_root / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def benchmark_official_constructive_comparison(
    repo_root: Path,
    output_root: Path | None = None,
    instance_path: Path | None = None,
    timelimit: float = 5.0,
    runs: int = 6,
) -> dict[str, object]:
    if instance_path is None:
        instance_path = repo_root / "examples" / "official-search-quality-instance.json"
    if output_root is None:
        output_root = repo_root / "artifacts" / "report" / "official_default"

    instance = load_instance(instance_path, input_format="official")
    problem = instance.metadata["raw_problem"]
    run_count = max(1, runs)
    run_rows: list[dict[str, object]] = []

    for run_index in range(run_count):
        delegated_solution, delegated_runtime = _timed_run(
            lambda: solve_official_constructive(problem, timelimit=timelimit)
        )
        native_solution, native_runtime = _timed_run(
            lambda: solve_official_constructive_native(problem, timelimit=timelimit)
        )
        search_solution, search_runtime = _timed_run(
            lambda: solve_official_search(problem, timelimit=timelimit)
        )
        delegated_result = validate_official_solution(problem, delegated_solution)
        native_result = validate_official_solution(problem, native_solution)
        search_result = validate_official_solution(problem, search_solution)
        delegated_objective = delegated_result["objective"]
        native_objective = native_result["objective"]
        search_objective = search_result["objective"]

        run_rows.append(
            {
                "run": run_index + 1,
                "delegated_baseline": {
                    "feasible": delegated_result["feasible"],
                    "stage": delegated_result["stage"],
                    "objective": delegated_objective,
                    "runtime_seconds": delegated_runtime,
                },
                "native_constructive": {
                    "feasible": native_result["feasible"],
                    "stage": native_result["stage"],
                    "objective": native_objective,
                    "runtime_seconds": native_runtime,
                },
                "official_search": {
                    "feasible": search_result["feasible"],
                    "stage": search_result["stage"],
                    "objective": search_objective,
                    "runtime_seconds": search_runtime,
                },
                "objective_delta": None
                if delegated_objective is None or native_objective is None
                else float(native_objective) - float(delegated_objective),
                "search_vs_delegated_delta": None
                if delegated_objective is None or search_objective is None
                else float(search_objective) - float(delegated_objective),
                "search_vs_native_delta": None
                if native_objective is None or search_objective is None
                else float(search_objective) - float(native_objective),
            }
        )

    delegated_objectives = [
        float(run["delegated_baseline"]["objective"])
        for run in run_rows
        if run["delegated_baseline"]["objective"] is not None
    ]
    native_objectives = [
        float(run["native_constructive"]["objective"])
        for run in run_rows
        if run["native_constructive"]["objective"] is not None
    ]
    search_objectives = [
        float(run["official_search"]["objective"])
        for run in run_rows
        if run["official_search"]["objective"] is not None
    ]
    objective_deltas = [float(run["objective_delta"]) for run in run_rows if run["objective_delta"] is not None]
    search_vs_delegated_deltas = [
        float(run["search_vs_delegated_delta"])
        for run in run_rows
        if run["search_vs_delegated_delta"] is not None
    ]
    search_vs_native_deltas = [
        float(run["search_vs_native_delta"])
        for run in run_rows
        if run["search_vs_native_delta"] is not None
    ]

    payload = {
        "instance": instance.name,
        "summary": {
            "runs": run_count,
            "delegated_feasible_runs": sum(1 for run in run_rows if bool(run["delegated_baseline"]["feasible"])),
            "native_feasible_runs": sum(1 for run in run_rows if bool(run["native_constructive"]["feasible"])),
            "search_feasible_runs": sum(1 for run in run_rows if bool(run["official_search"]["feasible"])),
            "delegated_objective_mean": _mean_or_none(delegated_objectives),
            "native_objective_mean": _mean_or_none(native_objectives),
            "search_objective_mean": _mean_or_none(search_objectives),
            "objective_delta_mean": _mean_or_none(objective_deltas),
            "search_vs_delegated_delta_mean": _mean_or_none(search_vs_delegated_deltas),
            "search_vs_native_delta_mean": _mean_or_none(search_vs_native_deltas),
            "delegated_runtime_mean": _mean_or_none([float(run["delegated_baseline"]["runtime_seconds"]) for run in run_rows]),
            "native_runtime_mean": _mean_or_none([float(run["native_constructive"]["runtime_seconds"]) for run in run_rows]),
            "search_runtime_mean": _mean_or_none([float(run["official_search"]["runtime_seconds"]) for run in run_rows]),
            "native_better_or_equal_runs": sum(
                1
                for run in run_rows
                if run["objective_delta"] is not None and float(run["objective_delta"]) <= 0.0
            ),
            "native_faster_runs": sum(
                1
                for run in run_rows
                if float(run["native_constructive"]["runtime_seconds"]) <= float(run["delegated_baseline"]["runtime_seconds"])
            ),
            "search_better_or_equal_than_delegated_runs": sum(
                1
                for run in run_rows
                if run["search_vs_delegated_delta"] is not None and float(run["search_vs_delegated_delta"]) <= 0.0
            ),
            "search_better_or_equal_than_native_runs": sum(
                1
                for run in run_rows
                if run["search_vs_native_delta"] is not None and float(run["search_vs_native_delta"]) <= 0.0
            ),
            "search_faster_than_delegated_runs": sum(
                1
                for run in run_rows
                if float(run["official_search"]["runtime_seconds"]) <= float(run["delegated_baseline"]["runtime_seconds"])
            ),
        },
        "runs": run_rows,
    }
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "summary.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def _timed_run(run_callable):
    started_at = perf_counter()
    solution = run_callable()
    return solution, perf_counter() - started_at


def _serialize_result(
    result: dict[str, object],
    runtime_seconds: float,
    problem: dict[str, object] | None = None,
    solution: dict[str, object] | None = None,
) -> dict[str, object]:
    serialized = {
        "runtime_seconds": runtime_seconds,
        "feasible": result["feasible"],
        "stage": result["stage"],
        "objective": result["objective"],
        "obj1": result["obj1"],
        "obj2": result["obj2"],
        "obj3": result["obj3"],
        "violations": result["violations"],
    }
    if problem is not None and solution is not None:
        assignments = _extract_assignments(problem, solution)
        serialized["assignment_count"] = len(assignments)
        serialized["assignments"] = assignments
    return serialized


def _mean_or_none(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def _extract_assignments(problem: dict[str, object], solution: dict[str, object]) -> list[dict[str, object]]:
    operations = solution.get("operations", {})
    blocks = problem["blocks"]
    entries_by_block: dict[int, dict[str, object]] = {}
    exits_by_block: dict[int, int] = {}

    for time_key in sorted(operations.keys(), key=lambda item: int(item)):
        time_value = int(time_key)
        for operation in operations[time_key]:
            operation_type = operation["type"]
            block_id = int(operation["block_id"])
            if operation_type == "ENTRY":
                width, height = _shape_dimensions(blocks[block_id], int(operation["orient_idx"]))
                entries_by_block[block_id] = {
                    "block_id": block_id,
                    "bay_id": int(operation["bay_id"]),
                    "x": int(operation["x"]),
                    "y": int(operation["y"]),
                    "orient_idx": int(operation["orient_idx"]),
                    "entry_time": time_value,
                    "width": width,
                    "height": height,
                }
            elif operation_type == "EXIT":
                exits_by_block[block_id] = time_value

    assignments: list[dict[str, object]] = []
    for block_id, entry in sorted(entries_by_block.items()):
        assignment = dict(entry)
        assignment["exit_time"] = exits_by_block.get(block_id)
        assignments.append(assignment)
    return assignments


def _shape_dimensions(block_data: dict[str, object], orient_idx: int) -> tuple[int, int]:
    vertices = [vertex for layer in block_data["shape"][orient_idx]["layers"] for vertex in layer]
    xs = [vertex[0] for vertex in vertices]
    ys = [vertex[1] for vertex in vertices]
    return int(max(xs) - min(xs)), int(max(ys) - min(ys))