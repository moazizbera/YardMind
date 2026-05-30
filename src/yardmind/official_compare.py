from __future__ import annotations

import json
from pathlib import Path
from time import perf_counter

from yardmind.loader import load_instance
from yardmind.official import (
    solve_official_constructive,
    solve_official_constructive_native,
    validate_official_solution,
)


def generate_official_constructive_comparison(
    repo_root: Path,
    output_root: Path | None = None,
    instance_path: Path | None = None,
    timelimit: float = 5.0,
) -> dict[str, object]:
    if instance_path is None:
        instance_path = repo_root / "examples" / "official-sample-instance.json"
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

    delegated_result = validate_official_solution(problem, delegated_solution)
    native_result = validate_official_solution(problem, native_solution)

    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "delegated_baseline_solution.json").write_text(
        json.dumps(delegated_solution, indent=2),
        encoding="utf-8",
    )
    (output_root / "native_constructive_solution.json").write_text(
        json.dumps(native_solution, indent=2),
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
    }
    (output_root / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


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