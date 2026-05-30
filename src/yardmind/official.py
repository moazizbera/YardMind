from __future__ import annotations

import contextlib
import io
import importlib.util
import json
import sys
import time
from functools import lru_cache
from itertools import combinations, permutations, product
from pathlib import Path
from types import ModuleType
from typing import Any


class OfficialSupportError(RuntimeError):
    """Raised when official baseline assets are unavailable or invalid."""


def load_official_solution(path: Path) -> dict[str, Any]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise OfficialSupportError(f"Official solution JSON is invalid: {path}") from exc

    if not isinstance(raw, dict):
        raise OfficialSupportError(f"Official solution must be a JSON object: {path}")
    return raw


def validate_official_solution(problem: dict[str, Any], solution: dict[str, Any]) -> dict[str, Any]:
    utils_module = _load_official_utils_module()
    return utils_module.check_feasibility(problem, solution)


def solve_official_constructive(problem: dict[str, Any], timelimit: float = 60.0) -> dict[str, Any]:
    baseline_module = _load_official_baseline_greedy_module()
    captured_stdout = io.StringIO()
    with contextlib.redirect_stdout(captured_stdout):
        return baseline_module.greedyalgorithm(problem, timelimit)


def solve_official_search(problem: dict[str, Any], timelimit: float = 60.0) -> dict[str, Any]:
    candidate_solutions = [solve_official_constructive(problem, timelimit=timelimit)]
    candidate_orders = _build_official_search_orders(problem)
    if not candidate_orders:
        candidate_orders = [_default_official_block_order(problem)]

    initial_budget = max(0.01, timelimit * 0.45)
    initial_candidates, best_native_order = _evaluate_native_order_candidates(
        problem,
        candidate_orders,
        timelimit=initial_budget,
    )
    candidate_solutions.extend(initial_candidates)

    remaining_budget = max(0.01, timelimit - initial_budget)
    if best_native_order is not None:
        neighbor_orders = _build_order_neighbors(best_native_order)
        if neighbor_orders:
            neighbor_candidates, _ = _evaluate_native_order_candidates(
                problem,
                neighbor_orders,
                timelimit=max(0.01, remaining_budget * 0.6),
            )
            candidate_solutions.extend(neighbor_candidates)

        best_solution, _ = _select_best_official_candidate(problem, candidate_solutions)
        if best_solution is not None:
            bay_bias_candidates = _build_bay_bias_candidates(problem, best_solution)
            if bay_bias_candidates:
                candidate_solutions.extend(
                    _evaluate_bay_bias_candidates(
                        problem,
                        block_order=best_native_order,
                        candidate_biases=bay_bias_candidates,
                        timelimit=max(0.01, remaining_budget * 0.4),
                    )
                )

            combined_candidates = _build_combined_perturbation_candidates(problem, best_solution, best_native_order)
            if combined_candidates:
                candidate_solutions.extend(
                    _evaluate_combined_perturbation_candidates(
                        problem,
                        candidate_specs=combined_candidates,
                        timelimit=max(0.01, remaining_budget * 0.25),
                    )
                )

            best_solution, _ = _select_best_official_candidate(problem, candidate_solutions)
            if best_solution is not None:
                rebuild_candidates = _build_objective_rebuild_candidates(problem, best_solution, best_native_order)
                if rebuild_candidates:
                    candidate_solutions.extend(
                        _evaluate_combined_perturbation_candidates(
                            problem,
                            candidate_specs=rebuild_candidates,
                            timelimit=max(0.01, remaining_budget * 0.15),
                        )
                    )

            best_solution, _ = _select_best_official_candidate(problem, candidate_solutions)
            if best_solution is not None:
                reinsertion_candidates = _build_objective_reinsertion_candidates(problem, best_solution, best_native_order)
                if reinsertion_candidates:
                    candidate_solutions.extend(
                        _evaluate_combined_perturbation_candidates(
                            problem,
                            candidate_specs=reinsertion_candidates,
                            timelimit=max(0.01, remaining_budget * 0.1),
                        )
                    )

            best_solution, _ = _select_best_official_candidate(problem, candidate_solutions)
            if best_solution is not None:
                partial_reconstruction_candidates = _build_objective_partial_reconstruction_candidates(
                    problem,
                    best_solution,
                    best_native_order,
                )
                if partial_reconstruction_candidates:
                    candidate_solutions.extend(
                        _evaluate_partial_reconstruction_candidates(
                            problem,
                            candidate_specs=partial_reconstruction_candidates,
                            timelimit=max(0.01, remaining_budget * 0.08),
                        )
                    )

    best_solution, best_result = _select_best_official_candidate(problem, candidate_solutions)

    if best_solution is None:
        raise OfficialSupportError("Official search could not produce any candidate solution.")
    return best_solution


def solve_official_constructive_native(
    problem: dict[str, Any],
    timelimit: float = 60.0,
    block_order: list[int] | None = None,
    bay_score_biases: dict[int, dict[int, float]] | None = None,
    fixed_assignments: dict[int, dict[str, int]] | None = None,
) -> dict[str, Any]:
    utils_module = _load_official_utils_module()
    baseline_module = _load_official_baseline_greedy_module()

    bays_data = problem["bays"]
    blocks_data = problem["blocks"]
    weights = problem.get("weights", {})
    bays = [utils_module.Bay.from_dict(bay_data, index) for index, bay_data in enumerate(bays_data)]
    feasible_bays_by_block = [_feasible_bays_for_block(block_data, bays, baseline_module) for block_data in blocks_data]

    bay_placed: list[list[Any]] = [[] for _ in bays]
    bay_schedule: list[list[tuple[int, int]]] = [[] for _ in bays]
    bay_loads: list[float] = [0.0 for _ in bays]
    assignments: list[dict[str, Any]] = []

    started_at = time.time()
    incumbent_assignments = fixed_assignments or {}
    for block_id, placement in sorted(
        incumbent_assignments.items(),
        key=lambda item: (int(item[1].get("entry_time", 0)), item[0]),
    ):
        placed_block = utils_module.Block(
            block_id=block_id,
            block_data=blocks_data[block_id],
            x=int(placement["x"]),
            y=int(placement["y"]),
            orient_idx=int(placement["orient_idx"]),
        )
        bay_id = int(placement["bay_id"])
        bay_placed[bay_id].append(placed_block)
        bay_schedule[bay_id].append((int(placement["entry_time"]), int(placement["exit_time"])))
        bay_loads[bay_id] += float(blocks_data[block_id]["workload"])
        assignments.append(
            {
                "block_id": block_id,
                "bay_id": bay_id,
                "x": int(placement["x"]),
                "y": int(placement["y"]),
                "orient_idx": int(placement["orient_idx"]),
                "entry_time": int(placement["entry_time"]),
                "exit_time": int(placement["exit_time"]),
            }
        )

    ordered_block_ids = [
        block_id
        for block_id in (block_order or _default_official_block_order(problem))
        if block_id not in incumbent_assignments
    ]

    for ordered_index, block_id in enumerate(ordered_block_ids):
        future_bay_scarcity = [0.0 for _ in bays]
        future_blocks = []
        for future_block_id in ordered_block_ids[ordered_index + 1 :]:
            future_block = blocks_data[future_block_id]
            future_blocks.append((future_block, feasible_bays_by_block[future_block_id]))
            future_feasible_bays = feasible_bays_by_block[future_block_id]
            if not future_feasible_bays:
                continue
            scarcity_share = _future_block_pressure(future_block) / len(future_feasible_bays)
            for bay_id in future_feasible_bays:
                future_bay_scarcity[bay_id] += scarcity_share

        placement = _select_native_official_placement(
            block_id=block_id,
            blocks_data=blocks_data,
            bays=bays,
            bay_placed=bay_placed,
            bay_schedule=bay_schedule,
            bay_loads=bay_loads,
            current_fit_bay_count=len(feasible_bays_by_block[block_id]),
            future_bay_scarcity=future_bay_scarcity,
            future_blocks=future_blocks,
            w1=float(weights.get("w1", 1.0)),
            w2=float(weights.get("w2", 1.0)),
            w3=float(weights.get("w3", 1.0)),
            bay_score_biases=bay_score_biases,
            utils_module=utils_module,
            baseline_module=baseline_module,
            started_at=started_at,
            timelimit=timelimit,
        )
        assignments.append(placement)

        placed_block = utils_module.Block(
            block_id=block_id,
            block_data=blocks_data[block_id],
            x=int(placement["x"]),
            y=int(placement["y"]),
            orient_idx=int(placement["orient_idx"]),
        )
        bay_id = int(placement["bay_id"])
        bay_placed[bay_id].append(placed_block)
        bay_schedule[bay_id].append((int(placement["entry_time"]), int(placement["exit_time"])))
        bay_loads[bay_id] += float(blocks_data[block_id]["workload"])

    return {"operations": baseline_module._build_operations(assignments)}


def _select_native_official_placement(
    *,
    block_id: int,
    blocks_data: list[dict[str, Any]],
    bays: list[Any],
    bay_placed: list[list[Any]],
    bay_schedule: list[list[tuple[int, int]]],
    bay_loads: list[float],
    current_fit_bay_count: int,
    future_bay_scarcity: list[float],
    future_blocks: list[tuple[dict[str, Any], list[int]]],
    w1: float,
    w2: float,
    w3: float,
    bay_score_biases: dict[int, dict[int, float]] | None,
    utils_module: ModuleType,
    baseline_module: ModuleType,
    started_at: float,
    timelimit: float,
) -> dict[str, Any]:
    block_data = blocks_data[block_id]
    bay_preferences = block_data["bay_preferences"]
    due_date = int(block_data["due_date"])
    release_time = int(block_data["release_time"])
    processing_time = int(block_data["processing_time"])
    workload = float(block_data["workload"])
    max_preference = max(bay_preferences)

    bay_areas = [bay.width * bay.height for bay in bays]
    average_bay_area = sum(bay_areas) / len(bay_areas)
    bay_weights = [average_bay_area / area for area in bay_areas]

    best_key: tuple[float, int, int, int, int, int] | None = None
    best_placement: dict[str, Any] | None = None

    bay_order = sorted(range(len(bays)), key=lambda bay_id: (-bay_preferences[bay_id], bay_id))
    for bay_rank, bay_id in enumerate(bay_order):
        bay = bays[bay_id]
        for orient_idx in range(len(block_data["shape"])):
            block_bbox = baseline_module._block_bbox(block_data, orient_idx)
            block_width = block_bbox[2] - block_bbox[0]
            block_height = block_bbox[3] - block_bbox[1]
            if block_width > bay.width + 1e-6 or block_height > bay.height + 1e-6:
                continue

            for x, y in baseline_module._candidate_positions(
                bay.width,
                bay.height,
                bay_placed[bay_id],
                block_bbox,
            ):
                candidate_block = utils_module.Block(
                    block_id=block_id,
                    block_data=block_data,
                    x=int(x),
                    y=int(y),
                    orient_idx=orient_idx,
                )
                entry_time, exit_time = baseline_module._find_earliest_slot(
                    candidate_block,
                    bay,
                    bay_placed[bay_id],
                    bay_schedule[bay_id],
                    release_time,
                    processing_time,
                )
                if entry_time is None or exit_time is None:
                    continue

                tardiness = max(0.0, float(exit_time) - due_date)
                preference_penalty = max_preference - bay_preferences[bay_id]
                top_y = candidate_block.bounding_rect()[3]
                score = baseline_module._placement_score(
                    tardiness,
                    workload,
                    bay_loads,
                    bay_id,
                    preference_penalty,
                    bay_weights,
                    w1,
                    w2,
                    w3,
                    top_y=top_y,
                )
                if current_fit_bay_count > 1:
                    score += max(w1, w3) * future_bay_scarcity[bay_id]
                    score += max(w1, w3) * _future_schedule_pressure(
                        bay_id,
                        int(entry_time),
                        int(exit_time),
                        future_blocks,
                    )
                if bay_score_biases is not None:
                    score += bay_score_biases.get(block_id, {}).get(bay_id, 0.0)
                key = (score, bay_rank, int(entry_time), int(y), int(x), orient_idx)
                if best_key is None or key < best_key:
                    best_key = key
                    best_placement = {
                        "block_id": block_id,
                        "bay_id": bay_id,
                        "x": int(x),
                        "y": int(y),
                        "orient_idx": orient_idx,
                        "entry_time": int(entry_time),
                        "exit_time": int(exit_time),
                    }

        if time.time() - started_at > timelimit * 0.95:
            break

    if best_placement is not None:
        return best_placement

    bay_id, x, y, orient_idx, entry_time, exit_time = baseline_module._force_place(
        block_id,
        blocks_data,
        bays,
        bay_schedule,
        bay_preferences,
    )
    return {
        "block_id": block_id,
        "bay_id": int(bay_id),
        "x": int(x),
        "y": int(y),
        "orient_idx": int(orient_idx),
        "entry_time": int(entry_time),
        "exit_time": int(exit_time),
    }


def _feasible_bays_for_block(block_data: dict[str, Any], bays: list[Any], baseline_module: ModuleType) -> list[int]:
    feasible_bays: list[int] = []
    for bay_id, bay in enumerate(bays):
        for orient_idx in range(len(block_data["shape"])):
            block_width, block_height = baseline_module._block_size(block_data, orient_idx)
            if block_width <= bay.width + 1e-6 and block_height <= bay.height + 1e-6:
                feasible_bays.append(bay_id)
                break
    return feasible_bays


def _future_block_pressure(block_data: dict[str, Any]) -> float:
    slack = max(
        0,
        int(block_data["due_date"]) - int(block_data["release_time"]) - int(block_data["processing_time"]),
    )
    return 1.0 / (1.0 + slack)


def _future_schedule_pressure(
    bay_id: int,
    entry_time: int,
    exit_time: int,
    future_blocks: list[tuple[dict[str, Any], list[int]]],
) -> float:
    pressure = 0.0
    for future_block, feasible_bays in future_blocks:
        if bay_id not in feasible_bays:
            continue
        overlap = _interval_overlap(
            entry_time,
            exit_time,
            int(future_block["release_time"]),
            int(future_block["due_date"]),
        )
        if overlap <= 0:
            continue
        processing_time = max(1, int(future_block["processing_time"]))
        pressure += _future_block_pressure(future_block) * (overlap / processing_time)
    return pressure


def _interval_overlap(start_a: int, end_a: int, start_b: int, end_b: int) -> int:
    return max(0, min(end_a, end_b) - max(start_a, start_b))


def _default_official_block_order(problem: dict[str, Any]) -> list[int]:
    blocks_data = problem["blocks"]
    return sorted(
        range(len(blocks_data)),
        key=lambda block_id: (
            blocks_data[block_id]["due_date"],
            blocks_data[block_id]["processing_time"],
            -max(blocks_data[block_id]["bay_preferences"]),
            block_id,
        ),
    )


def _build_official_search_orders(problem: dict[str, Any]) -> list[list[int]]:
    blocks_data = problem["blocks"]
    utils_module = _load_official_utils_module()
    baseline_module = _load_official_baseline_greedy_module()
    bays = [utils_module.Bay.from_dict(bay_data, index) for index, bay_data in enumerate(problem["bays"])]

    feasible_counts = [
        len(
            _feasible_bays_for_block(
                block_data,
                bays,
                baseline_module,
            )
        )
        for block_data in blocks_data
    ]
    unique_orders: list[list[int]] = []
    seen_orders: set[tuple[int, ...]] = set()

    order_keys = [
        lambda block_id: (
            blocks_data[block_id]["due_date"],
            blocks_data[block_id]["processing_time"],
            -max(blocks_data[block_id]["bay_preferences"]),
            block_id,
        ),
        lambda block_id: (
            feasible_counts[block_id],
            blocks_data[block_id]["due_date"],
            blocks_data[block_id]["processing_time"],
            -_preference_gap(blocks_data[block_id]),
            block_id,
        ),
        lambda block_id: (
            _slack(blocks_data[block_id]),
            feasible_counts[block_id],
            -float(blocks_data[block_id]["workload"]),
            block_id,
        ),
        lambda block_id: (
            -float(blocks_data[block_id]["workload"]),
            feasible_counts[block_id],
            blocks_data[block_id]["due_date"],
            block_id,
        ),
    ]

    for order_key in order_keys:
        order = tuple(sorted(range(len(blocks_data)), key=order_key))
        if order not in seen_orders:
            seen_orders.add(order)
            unique_orders.append(list(order))

    return unique_orders


def _slack(block_data: dict[str, Any]) -> int:
    return int(block_data["due_date"]) - int(block_data["release_time"]) - int(block_data["processing_time"])


def _preference_gap(block_data: dict[str, Any]) -> float:
    preferences = sorted((float(value) for value in block_data["bay_preferences"]), reverse=True)
    if len(preferences) < 2:
        return preferences[0] if preferences else 0.0
    return preferences[0] - preferences[1]


def _official_result_key(result: dict[str, Any]) -> tuple[int, int, float, int]:
    feasible_rank = 0 if result.get("feasible") else 1
    stage_rank = -int(result.get("stage", 0))
    objective = float(result["objective"]) if result.get("objective") is not None else float("inf")
    violation_rank = len(result.get("violations", []))
    return (feasible_rank, stage_rank, objective, violation_rank)


def _evaluate_native_order_candidates(
    problem: dict[str, Any],
    candidate_orders: list[list[int]],
    *,
    timelimit: float,
) -> tuple[list[dict[str, Any]], list[int] | None]:
    unique_orders: list[list[int]] = []
    seen_orders: set[tuple[int, ...]] = set()
    for order in candidate_orders:
        order_key = tuple(order)
        if order_key in seen_orders:
            continue
        seen_orders.add(order_key)
        unique_orders.append(order)

    if not unique_orders:
        return [], None

    per_candidate_timelimit = max(0.01, timelimit / len(unique_orders))
    solutions: list[dict[str, Any]] = []
    best_order: list[int] | None = None
    best_result: dict[str, Any] | None = None
    for order in unique_orders:
        solution = solve_official_constructive_native(
            problem,
            timelimit=per_candidate_timelimit,
            block_order=order,
        )
        solutions.append(solution)
        result = validate_official_solution(problem, solution)
        if best_result is None or _official_result_key(result) < _official_result_key(best_result):
            best_result = result
            best_order = list(order)

    return solutions, best_order


def _evaluate_bay_bias_candidates(
    problem: dict[str, Any],
    *,
    block_order: list[int],
    candidate_biases: list[dict[int, dict[int, float]]],
    timelimit: float,
) -> list[dict[str, Any]]:
    if not candidate_biases:
        return []

    per_candidate_timelimit = max(0.01, timelimit / len(candidate_biases))
    return [
        solve_official_constructive_native(
            problem,
            timelimit=per_candidate_timelimit,
            block_order=block_order,
            bay_score_biases=biases,
        )
        for biases in candidate_biases
    ]


def _select_best_official_candidate(
    problem: dict[str, Any],
    candidate_solutions: list[dict[str, Any]],
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    best_solution: dict[str, Any] | None = None
    best_result: dict[str, Any] | None = None
    for solution in candidate_solutions:
        result = validate_official_solution(problem, solution)
        if best_result is None or _official_result_key(result) < _official_result_key(best_result):
            best_solution = solution
            best_result = result
    return best_solution, best_result


def _evaluate_combined_perturbation_candidates(
    problem: dict[str, Any],
    *,
    candidate_specs: list[tuple[list[int], dict[int, dict[int, float]]]],
    timelimit: float,
) -> list[dict[str, Any]]:
    if not candidate_specs:
        return []

    per_candidate_timelimit = max(0.01, timelimit / len(candidate_specs))
    return [
        solve_official_constructive_native(
            problem,
            timelimit=per_candidate_timelimit,
            block_order=block_order,
            bay_score_biases=biases,
        )
        for block_order, biases in candidate_specs
    ]


def _evaluate_partial_reconstruction_candidates(
    problem: dict[str, Any],
    *,
    candidate_specs: list[tuple[list[int], dict[int, dict[int, float]], dict[int, dict[str, int]]]],
    timelimit: float,
) -> list[dict[str, Any]]:
    if not candidate_specs:
        return []

    per_candidate_timelimit = max(0.01, timelimit / len(candidate_specs))
    return [
        solve_official_constructive_native(
            problem,
            timelimit=per_candidate_timelimit,
            block_order=block_order,
            bay_score_biases=biases,
            fixed_assignments=fixed_assignments,
        )
        for block_order, biases, fixed_assignments in candidate_specs
    ]


def _build_order_neighbors(block_order: list[int]) -> list[list[int]]:
    neighbors: list[list[int]] = []
    seen_orders: set[tuple[int, ...]] = set()

    for index in range(len(block_order) - 1):
        order = list(block_order)
        order[index], order[index + 1] = order[index + 1], order[index]
        order_key = tuple(order)
        if order_key not in seen_orders:
            seen_orders.add(order_key)
            neighbors.append(order)

    pivot_count = min(3, len(block_order))
    for left in range(pivot_count):
        for right in range(left + 2, len(block_order)):
            order = list(block_order)
            order[left], order[right] = order[right], order[left]
            order_key = tuple(order)
            if order_key not in seen_orders:
                seen_orders.add(order_key)
                neighbors.append(order)

    for source in range(1, len(block_order)):
        for target in range(min(3, source)):
            order = list(block_order)
            moved = order.pop(source)
            order.insert(target, moved)
            order_key = tuple(order)
            if order_key not in seen_orders:
                seen_orders.add(order_key)
                neighbors.append(order)

    return neighbors


def _build_bay_bias_candidates(
    problem: dict[str, Any],
    solution: dict[str, Any],
) -> list[dict[int, dict[int, float]]]:
    baseline_module = _load_official_baseline_greedy_module()
    utils_module = _load_official_utils_module()
    bays = [utils_module.Bay.from_dict(bay_data, index) for index, bay_data in enumerate(problem["bays"])]
    assignments = _extract_solution_assignments(solution)

    candidate_biases: list[dict[int, dict[int, float]]] = []
    seen_biases: set[tuple[tuple[int, tuple[tuple[int, float], ...]], ...]] = set()
    for block_id, assignment in assignments.items():
        block_data = problem["blocks"][block_id]
        feasible_bays = _feasible_bays_for_block(block_data, bays, baseline_module)
        assigned_bay = assignment["bay_id"]
        if len(feasible_bays) <= 1:
            continue

        alternatives = sorted(
            (bay_id for bay_id in feasible_bays if bay_id != assigned_bay),
            key=lambda bay_id: (-block_data["bay_preferences"][bay_id], bay_id),
        )
        if not alternatives:
            continue

        for bay_id in alternatives[:2]:
            bias_strength = max(2.0, _preference_gap(block_data) + 1.0)
            bias = {
                block_id: {
                    assigned_bay: bias_strength,
                    bay_id: -bias_strength,
                }
            }
            bias_key = tuple(
                sorted(
                    (bid, tuple(sorted((bay, round(delta, 6)) for bay, delta in per_bay.items())))
                    for bid, per_bay in bias.items()
                )
            )
            if bias_key not in seen_biases:
                seen_biases.add(bias_key)
                candidate_biases.append(bias)

    return candidate_biases


def _build_combined_perturbation_candidates(
    problem: dict[str, Any],
    solution: dict[str, Any],
    block_order: list[int],
    *,
    prioritize_incumbent_pressure: bool = True,
    include_load_pressure: bool = True,
    use_objective_contribution: bool = True,
) -> list[tuple[list[int], dict[int, dict[int, float]]]]:
    baseline_module = _load_official_baseline_greedy_module()
    utils_module = _load_official_utils_module()
    bays = [utils_module.Bay.from_dict(bay_data, index) for index, bay_data in enumerate(problem["bays"])]
    assignments = _extract_solution_assignments(solution)

    candidate_specs: list[tuple[list[int], dict[int, dict[int, float]]]] = []
    seen_specs: set[tuple[tuple[int, ...], tuple[tuple[int, tuple[tuple[int, float], ...]], ...]]] = set()
    ranked_blocks = _rank_combined_perturbation_blocks(
        problem,
        assignments,
        bays=bays,
        baseline_module=baseline_module,
        prioritize_incumbent_pressure=prioritize_incumbent_pressure,
        include_load_pressure=include_load_pressure,
        use_objective_contribution=use_objective_contribution,
    )
    top_ranked_blocks = ranked_blocks[:4]

    for block_id in top_ranked_blocks[:3]:
        assignment = assignments[block_id]
        feasible_bays = _feasible_bays_for_block(problem["blocks"][block_id], bays, baseline_module)
        alternatives = [bay_id for bay_id in feasible_bays if bay_id != assignment["bay_id"]]
        if not alternatives:
            continue

        promoted_order = _promote_blocks_in_order(block_order, [block_id])
        for bay_id in sorted(alternatives, key=lambda candidate: (-problem["blocks"][block_id]["bay_preferences"][candidate], candidate))[:2]:
            bias_strength = max(2.0, _preference_gap(problem["blocks"][block_id]) + 1.0)
            biases = {
                block_id: {
                    assignment["bay_id"]: bias_strength,
                    bay_id: -bias_strength,
                }
            }
            spec_key = (
                tuple(promoted_order),
                tuple(
                    sorted(
                        (bid, tuple(sorted((bay, round(delta, 6)) for bay, delta in per_bay.items())))
                        for bid, per_bay in biases.items()
                    )
                ),
            )
            if spec_key not in seen_specs:
                seen_specs.add(spec_key)
                candidate_specs.append((promoted_order, biases))

    for first_block_id, second_block_id in combinations(top_ranked_blocks[:3], 2):
        first_assignment = assignments[first_block_id]
        second_assignment = assignments[second_block_id]
        first_alternatives = _top_alternative_bays(
            problem["blocks"][first_block_id],
            assigned_bay=first_assignment["bay_id"],
            bays=bays,
            baseline_module=baseline_module,
            limit=1,
        )
        second_alternatives = _top_alternative_bays(
            problem["blocks"][second_block_id],
            assigned_bay=second_assignment["bay_id"],
            bays=bays,
            baseline_module=baseline_module,
            limit=1,
        )
        if not first_alternatives or not second_alternatives:
            continue

        promoted_order = _promote_blocks_in_order(block_order, [first_block_id, second_block_id])
        first_bias_strength = max(2.0, _preference_gap(problem["blocks"][first_block_id]) + 1.0)
        second_bias_strength = max(2.0, _preference_gap(problem["blocks"][second_block_id]) + 1.0)
        biases = {
            first_block_id: {
                first_assignment["bay_id"]: first_bias_strength,
                first_alternatives[0]: -first_bias_strength,
            },
            second_block_id: {
                second_assignment["bay_id"]: second_bias_strength,
                second_alternatives[0]: -second_bias_strength,
            },
        }
        spec_key = (
            tuple(promoted_order),
            tuple(
                sorted(
                    (bid, tuple(sorted((bay, round(delta, 6)) for bay, delta in per_bay.items())))
                    for bid, per_bay in biases.items()
                )
            ),
        )
        if spec_key not in seen_specs:
            seen_specs.add(spec_key)
            candidate_specs.append((promoted_order, biases))

    return candidate_specs


def _build_objective_rebuild_candidates(
    problem: dict[str, Any],
    solution: dict[str, Any],
    block_order: list[int],
    *,
    explore_order_variants: bool = True,
    max_alternative_bays: int = 2,
) -> list[tuple[list[int], dict[int, dict[int, float]]]]:
    baseline_module = _load_official_baseline_greedy_module()
    utils_module = _load_official_utils_module()
    bays = [utils_module.Bay.from_dict(bay_data, index) for index, bay_data in enumerate(problem["bays"])]
    assignments = _extract_solution_assignments(solution)
    bay_load_pressure = _incumbent_bay_load_pressure(problem, assignments, bays)
    objective_contributions = _incumbent_objective_contributions(problem, assignments, bays, bay_load_pressure)
    ranked_blocks = sorted(
        assignments.keys(),
        key=lambda block_id: (-objective_contributions.get(block_id, 0.0), block_id),
    )

    candidate_specs: list[tuple[list[int], dict[int, dict[int, float]]]] = []
    seen_specs: set[tuple[tuple[int, ...], tuple[tuple[int, tuple[tuple[int, float], ...]], ...]]] = set()
    max_focus_count = min(3, len(ranked_blocks))
    for focus_count in range(2, max_focus_count + 1):
        focus_blocks = ranked_blocks[:focus_count]
        order_variants = _build_rebuild_order_variants(
            block_order,
            focus_blocks,
            explore_order_variants=explore_order_variants,
        )
        alternative_options: list[tuple[int, list[int], float, int]] = []
        for block_id in focus_blocks:
            assignment = assignments[block_id]
            alternatives = _top_alternative_bays(
                problem["blocks"][block_id],
                assigned_bay=assignment["bay_id"],
                bays=bays,
                baseline_module=baseline_module,
                limit=max_alternative_bays,
            )
            if not alternatives:
                continue

            contribution = objective_contributions.get(block_id, 0.0)
            bias_strength = max(2.0, _preference_gap(problem["blocks"][block_id]) + 1.0)
            bias_strength += min(4.0, contribution / max(1.0, float(problem.get("weights", {}).get("w1", 1.0))))
            alternative_options.append((block_id, alternatives, bias_strength, assignment["bay_id"]))

        if not alternative_options:
            continue

        for rebuilt_order in order_variants:
            for selected_bays in product(*(alternatives for _, alternatives, _, _ in alternative_options)):
                biases: dict[int, dict[int, float]] = {}
                for (block_id, _, bias_strength, assigned_bay), alternative_bay in zip(alternative_options, selected_bays, strict=False):
                    biases[block_id] = {
                        assigned_bay: bias_strength,
                        alternative_bay: -bias_strength,
                    }

                spec_key = (
                    tuple(rebuilt_order),
                    tuple(
                        sorted(
                            (bid, tuple(sorted((bay, round(delta, 6)) for bay, delta in per_bay.items())))
                            for bid, per_bay in biases.items()
                        )
                    ),
                )
                if spec_key not in seen_specs:
                    seen_specs.add(spec_key)
                    candidate_specs.append((rebuilt_order, biases))

    return candidate_specs


def _build_objective_reinsertion_candidates(
    problem: dict[str, Any],
    solution: dict[str, Any],
    block_order: list[int],
    *,
    explore_staggered_variants: bool = True,
) -> list[tuple[list[int], dict[int, dict[int, float]]]]:
    baseline_module = _load_official_baseline_greedy_module()
    utils_module = _load_official_utils_module()
    bays = [utils_module.Bay.from_dict(bay_data, index) for index, bay_data in enumerate(problem["bays"])]
    assignments = _extract_solution_assignments(solution)
    bay_load_pressure = _incumbent_bay_load_pressure(problem, assignments, bays)
    objective_contributions = _incumbent_objective_contributions(problem, assignments, bays, bay_load_pressure)
    ranked_blocks = sorted(
        assignments.keys(),
        key=lambda block_id: (-objective_contributions.get(block_id, 0.0), block_id),
    )

    candidate_specs: list[tuple[list[int], dict[int, dict[int, float]]]] = []
    seen_specs: set[tuple[tuple[int, ...], tuple[tuple[int, tuple[tuple[int, float], ...]], ...]]] = set()
    max_focus_count = min(3, len(ranked_blocks))
    for focus_count in range(2, max_focus_count + 1):
        focus_blocks = ranked_blocks[:focus_count]
        order_variants = _build_reinsertion_order_variants(
            block_order,
            focus_blocks,
            explore_staggered_variants=explore_staggered_variants,
        )
        alternative_options: list[tuple[int, list[int], float, int]] = []
        for block_id in focus_blocks:
            assignment = assignments[block_id]
            alternatives = _top_alternative_bays(
                problem["blocks"][block_id],
                assigned_bay=assignment["bay_id"],
                bays=bays,
                baseline_module=baseline_module,
                limit=2,
            )
            if not alternatives:
                continue

            contribution = objective_contributions.get(block_id, 0.0)
            bias_strength = max(2.0, _preference_gap(problem["blocks"][block_id]) + 1.0)
            bias_strength += min(4.0, contribution / max(1.0, float(problem.get("weights", {}).get("w1", 1.0))))
            alternative_options.append((block_id, alternatives, bias_strength, assignment["bay_id"]))

        if not alternative_options:
            continue

        for order_variant in order_variants:
            for selected_bays in product(*(alternatives for _, alternatives, _, _ in alternative_options)):
                biases: dict[int, dict[int, float]] = {}
                for (block_id, _, bias_strength, assigned_bay), alternative_bay in zip(alternative_options, selected_bays, strict=False):
                    biases[block_id] = {
                        assigned_bay: bias_strength,
                        alternative_bay: -bias_strength,
                    }

                spec_key = (
                    tuple(order_variant),
                    tuple(
                        sorted(
                            (bid, tuple(sorted((bay, round(delta, 6)) for bay, delta in per_bay.items())))
                            for bid, per_bay in biases.items()
                        )
                    ),
                )
                if spec_key not in seen_specs:
                    seen_specs.add(spec_key)
                    candidate_specs.append((order_variant, biases))

    return candidate_specs


def _build_objective_partial_reconstruction_candidates(
    problem: dict[str, Any],
    solution: dict[str, Any],
    block_order: list[int],
    *,
    use_overlap_clusters: bool = True,
    use_bay_neighborhoods: bool = True,
    max_candidates: int | None = 12,
    adaptive_max_candidates: bool = True,
) -> list[tuple[list[int], dict[int, dict[int, float]], dict[int, dict[str, int]]]]:
    diagnostics = _build_objective_partial_reconstruction_diagnostics(
        problem,
        solution,
        block_order,
        use_overlap_clusters=use_overlap_clusters,
        use_bay_neighborhoods=use_bay_neighborhoods,
        max_candidates=max_candidates,
        adaptive_max_candidates=adaptive_max_candidates,
    )

    candidate_specs: list[tuple[list[int], dict[int, dict[int, float]], dict[int, dict[str, int]]]] = []
    candidate_specs.extend(diagnostics["candidate_specs"])
    return candidate_specs


def _build_objective_partial_reconstruction_diagnostics(
    problem: dict[str, Any],
    solution: dict[str, Any],
    block_order: list[int],
    *,
    use_overlap_clusters: bool = True,
    use_bay_neighborhoods: bool = True,
    max_candidates: int | None = 12,
    adaptive_max_candidates: bool = True,
) -> dict[str, Any]:
    baseline_module = _load_official_baseline_greedy_module()
    utils_module = _load_official_utils_module()
    bays = [utils_module.Bay.from_dict(bay_data, index) for index, bay_data in enumerate(problem["bays"])]
    assignments = _extract_solution_assignments(solution)
    bay_load_pressure = _incumbent_bay_load_pressure(problem, assignments, bays)
    objective_contributions = _incumbent_objective_contributions(problem, assignments, bays, bay_load_pressure)
    focus_sets = _build_partial_reconstruction_focus_sets(
        problem,
        assignments,
        objective_contributions,
        bay_load_pressure,
        use_overlap_clusters=use_overlap_clusters,
        use_bay_neighborhoods=use_bay_neighborhoods,
    )

    scored_candidate_specs: list[
        tuple[
            float,
            tuple[list[int], dict[int, dict[int, float]], dict[int, dict[str, int]]],
        ]
    ] = []
    seen_specs: set[
        tuple[
            tuple[int, ...],
            tuple[tuple[int, tuple[tuple[int, float], ...]], ...],
            tuple[tuple[int, int, int, int, int, int, int], ...],
        ]
    ] = set()
    for focus_blocks in focus_sets:
        focus_score = _partial_reconstruction_focus_score(
            problem,
            focus_blocks,
            assignments,
            objective_contributions,
            bay_load_pressure,
        )
        fixed_assignments = {
            block_id: dict(assignment)
            for block_id, assignment in assignments.items()
            if block_id not in focus_blocks
        }
        if not fixed_assignments:
            continue

        order_variants = _build_rebuild_order_variants(
            block_order,
            focus_blocks,
            explore_order_variants=True,
        )
        alternative_options: list[tuple[int, list[int], float, int]] = []
        for block_id in focus_blocks:
            assignment = assignments[block_id]
            alternatives = _top_alternative_bays(
                problem["blocks"][block_id],
                assigned_bay=assignment["bay_id"],
                bays=bays,
                baseline_module=baseline_module,
                limit=2,
            )
            contribution = objective_contributions.get(block_id, 0.0)
            bias_strength = max(2.0, _preference_gap(problem["blocks"][block_id]) + 1.0)
            bias_strength += min(4.0, contribution / max(1.0, float(problem.get("weights", {}).get("w1", 1.0))))
            alternative_options.append((block_id, alternatives, bias_strength, assignment["bay_id"]))

        if any(alternatives for _, alternatives, _, _ in alternative_options):
            selected_bay_sets = product(
                *[
                    alternatives if alternatives else [assigned_bay]
                    for _, alternatives, _, assigned_bay in alternative_options
                ]
            )
        else:
            selected_bay_sets = [tuple(assigned_bay for _, _, _, assigned_bay in alternative_options)]

        fixed_key = tuple(
            sorted(
                (
                    block_id,
                    int(assignment["bay_id"]),
                    int(assignment["x"]),
                    int(assignment["y"]),
                    int(assignment["orient_idx"]),
                    int(assignment["entry_time"]),
                    int(assignment["exit_time"]),
                )
                for block_id, assignment in fixed_assignments.items()
            )
        )
        for rebuilt_order in order_variants:
            for selected_bays in selected_bay_sets:
                biases: dict[int, dict[int, float]] = {}
                for (block_id, alternatives, bias_strength, assigned_bay), selected_bay in zip(
                    alternative_options,
                    selected_bays,
                    strict=False,
                ):
                    if alternatives and selected_bay != assigned_bay:
                        biases[block_id] = {
                            assigned_bay: bias_strength,
                            selected_bay: -bias_strength,
                        }

                spec_key = (
                    tuple(rebuilt_order),
                    tuple(
                        sorted(
                            (bid, tuple(sorted((bay, round(delta, 6)) for bay, delta in per_bay.items())))
                            for bid, per_bay in biases.items()
                        )
                    ),
                    fixed_key,
                )
                if spec_key not in seen_specs:
                    seen_specs.add(spec_key)
                    scored_candidate_specs.append(
                        (
                            focus_score + _partial_reconstruction_spec_score(focus_blocks, rebuilt_order, biases),
                            (rebuilt_order, biases, fixed_assignments),
                        )
                    )

    if not scored_candidate_specs:
        return {
            "pool_size": 0,
            "selected_cap": 0,
            "kept_count": 0,
            "top_scores": [],
            "candidate_specs": [],
        }

    scored_candidate_specs.sort(key=lambda item: item[0], reverse=True)
    if adaptive_max_candidates:
        max_candidates = _resolve_partial_reconstruction_candidate_cap(
            scored_candidate_specs,
            fallback_cap=max_candidates,
        )
    selected_cap = len(scored_candidate_specs) if max_candidates is None else max_candidates
    if max_candidates is not None:
        scored_candidate_specs = scored_candidate_specs[:max_candidates]
    candidate_specs = [spec for _, spec in scored_candidate_specs]
    return {
        "pool_size": len(seen_specs),
        "selected_cap": selected_cap,
        "kept_count": len(candidate_specs),
        "top_scores": [round(score, 6) for score, _ in scored_candidate_specs[:5]],
        "candidate_specs": candidate_specs,
    }


def _build_partial_reconstruction_focus_sets(
    problem: dict[str, Any],
    assignments: dict[int, dict[str, int]],
    objective_contributions: dict[int, float],
    bay_load_pressure: dict[int, float],
    *,
    use_overlap_clusters: bool,
    use_bay_neighborhoods: bool,
) -> list[list[int]]:
    ranked_blocks = sorted(
        assignments.keys(),
        key=lambda block_id: (-objective_contributions.get(block_id, 0.0), block_id),
    )
    if len(ranked_blocks) < 2:
        return []

    focus_sets: list[list[int]] = []
    seen_focus_sets: set[tuple[int, ...]] = set()
    max_focus_count = min(3, len(ranked_blocks))
    for focus_count in range(2, max_focus_count + 1):
        focus_blocks = ranked_blocks[:focus_count]
        focus_key = tuple(focus_blocks)
        if focus_key not in seen_focus_sets:
            seen_focus_sets.add(focus_key)
            focus_sets.append(focus_blocks)

    if not use_overlap_clusters and not use_bay_neighborhoods:
        return focus_sets

    if use_overlap_clusters:
        seed_blocks = ranked_blocks[: min(3, len(ranked_blocks))]
        for seed_block in seed_blocks:
            neighbor_candidates = sorted(
                (block_id for block_id in assignments if block_id != seed_block),
                key=lambda block_id: (
                    -_partial_reconstruction_neighbor_priority(
                        problem,
                        seed_block,
                        block_id,
                        assignments,
                        objective_contributions,
                        bay_load_pressure,
                    ),
                    -objective_contributions.get(block_id, 0.0),
                    block_id,
                ),
            )
            for focus_count in range(2, max_focus_count + 1):
                selected_neighbors = neighbor_candidates[: focus_count - 1]
                if len(selected_neighbors) != focus_count - 1:
                    continue
                focus_blocks = [seed_block, *selected_neighbors]
                focus_key = tuple(sorted(focus_blocks))
                if focus_key not in seen_focus_sets:
                    seen_focus_sets.add(focus_key)
                    focus_sets.append(focus_blocks)

    if use_bay_neighborhoods:
        overloaded_bays = sorted(
            range(len(problem["bays"])),
            key=lambda bay_id: (-bay_load_pressure.get(bay_id, 0.0), bay_id),
        )[:2]
        for bay_id in overloaded_bays:
            bay_blocks = [
                block_id
                for block_id, assignment in assignments.items()
                if int(assignment["bay_id"]) == bay_id
            ]
            if not bay_blocks:
                continue

            seed_block = max(
                bay_blocks,
                key=lambda block_id: (objective_contributions.get(block_id, 0.0), -block_id),
            )
            neighborhood_candidates = sorted(
                assignments.keys(),
                key=lambda block_id: (
                    -_bay_neighborhood_priority(
                        problem,
                        bay_id,
                        seed_block,
                        block_id,
                        assignments,
                        objective_contributions,
                        bay_load_pressure,
                    ),
                    -objective_contributions.get(block_id, 0.0),
                    block_id,
                ),
            )
            for focus_count in range(2, max_focus_count + 1):
                focus_blocks = neighborhood_candidates[:focus_count]
                if seed_block not in focus_blocks or len(focus_blocks) != focus_count:
                    continue
                focus_key = tuple(sorted(focus_blocks))
                if focus_key not in seen_focus_sets:
                    seen_focus_sets.add(focus_key)
                    focus_sets.append(focus_blocks)

    return focus_sets


def _partial_reconstruction_neighbor_priority(
    problem: dict[str, Any],
    seed_block_id: int,
    candidate_block_id: int,
    assignments: dict[int, dict[str, int]],
    objective_contributions: dict[int, float],
    bay_load_pressure: dict[int, float],
) -> float:
    seed_assignment = assignments[seed_block_id]
    candidate_assignment = assignments[candidate_block_id]
    seed_block = problem["blocks"][seed_block_id]
    candidate_block = problem["blocks"][candidate_block_id]

    seed_entry = int(seed_assignment["entry_time"])
    seed_exit = int(seed_assignment.get("exit_time", seed_entry))
    candidate_entry = int(candidate_assignment["entry_time"])
    candidate_exit = int(candidate_assignment.get("exit_time", candidate_entry))
    overlap = _interval_overlap(seed_entry, seed_exit, candidate_entry, candidate_exit)
    time_gap = min(abs(seed_entry - candidate_exit), abs(candidate_entry - seed_exit))
    temporal_pressure = overlap + (1.0 / (1.0 + max(0, time_gap)))

    same_bay_bonus = 2.0 if int(seed_assignment["bay_id"]) == int(candidate_assignment["bay_id"]) else 0.0
    candidate_bay_pressure = bay_load_pressure.get(int(candidate_assignment["bay_id"]), 0.0)
    preference_tension = abs(
        float(seed_block["bay_preferences"][int(candidate_assignment["bay_id"])])
        - float(seed_block["bay_preferences"][int(seed_assignment["bay_id"])])
    )
    preference_tension += abs(
        float(candidate_block["bay_preferences"][int(seed_assignment["bay_id"])])
        - float(candidate_block["bay_preferences"][int(candidate_assignment["bay_id"])])
    )

    return (
        objective_contributions.get(candidate_block_id, 0.0)
        + (4.0 * temporal_pressure)
        + same_bay_bonus
        + candidate_bay_pressure
        + (0.5 * preference_tension)
    )


def _bay_neighborhood_priority(
    problem: dict[str, Any],
    overloaded_bay_id: int,
    seed_block_id: int,
    candidate_block_id: int,
    assignments: dict[int, dict[str, int]],
    objective_contributions: dict[int, float],
    bay_load_pressure: dict[int, float],
) -> float:
    seed_assignment = assignments[seed_block_id]
    candidate_assignment = assignments[candidate_block_id]
    candidate_bay_id = int(candidate_assignment["bay_id"])
    same_bay_bonus = 5.0 if candidate_bay_id == overloaded_bay_id else 0.0
    pressure_bonus = bay_load_pressure.get(candidate_bay_id, 0.0)
    neighbor_bonus = _partial_reconstruction_neighbor_priority(
        problem,
        seed_block_id,
        candidate_block_id,
        assignments,
        objective_contributions,
        bay_load_pressure,
    )
    seed_preference = float(problem["blocks"][candidate_block_id]["bay_preferences"][int(seed_assignment["bay_id"])])
    overloaded_preference = float(problem["blocks"][candidate_block_id]["bay_preferences"][overloaded_bay_id])
    migration_tension = max(0.0, overloaded_preference - seed_preference)
    return objective_contributions.get(candidate_block_id, 0.0) + same_bay_bonus + pressure_bonus + neighbor_bonus + migration_tension


def _partial_reconstruction_focus_score(
    problem: dict[str, Any],
    focus_blocks: list[int],
    assignments: dict[int, dict[str, int]],
    objective_contributions: dict[int, float],
    bay_load_pressure: dict[int, float],
) -> float:
    score = 0.0
    for block_id in focus_blocks:
        assignment = assignments[block_id]
        bay_id = int(assignment["bay_id"])
        score += objective_contributions.get(block_id, 0.0)
        score += bay_load_pressure.get(bay_id, 0.0)
        score += _preference_gap(problem["blocks"][block_id])

    for left_block_id, right_block_id in combinations(focus_blocks, 2):
        left_assignment = assignments[left_block_id]
        right_assignment = assignments[right_block_id]
        score += 2.0 * _interval_overlap(
            int(left_assignment["entry_time"]),
            int(left_assignment.get("exit_time", left_assignment["entry_time"])),
            int(right_assignment["entry_time"]),
            int(right_assignment.get("exit_time", right_assignment["entry_time"])),
        )
        if int(left_assignment["bay_id"]) == int(right_assignment["bay_id"]):
            score += 2.0

    return score


def _partial_reconstruction_spec_score(
    focus_blocks: list[int],
    rebuilt_order: list[int],
    biases: dict[int, dict[int, float]],
) -> float:
    order_bonus = 0.0
    for index, block_id in enumerate(focus_blocks):
        try:
            order_bonus += max(0.0, 4.0 - rebuilt_order.index(block_id) + index)
        except ValueError:
            continue

    bias_bonus = sum(
        max(abs(delta) for delta in per_bay.values())
        for per_bay in biases.values()
        if per_bay
    )
    return order_bonus + bias_bonus


def _resolve_partial_reconstruction_candidate_cap(
    scored_candidate_specs: list[
        tuple[
            float,
            tuple[list[int], dict[int, dict[int, float]], dict[int, dict[str, int]]],
        ]
    ],
    *,
    fallback_cap: int | None,
) -> int | None:
    if fallback_cap is None or len(scored_candidate_specs) <= fallback_cap:
        return fallback_cap

    scores = [score for score, _ in scored_candidate_specs]
    shrink_permitted = True
    plateau_index = min(len(scores) - 1, 4)
    if plateau_index > 0 and abs(scores[0] - scores[plateau_index]) <= 1e-9:
        shrink_permitted = False

    top_score = scores[0]
    median_score = scores[len(scores) // 2]
    tail_score = scores[min(len(scores) - 1, fallback_cap)]
    strength_ratio = top_score / max(1.0, median_score)
    separation = max(0.0, top_score - tail_score)

    adaptive_cap = fallback_cap
    if strength_ratio >= 1.6:
        adaptive_cap += 4
    elif strength_ratio <= 1.15 and shrink_permitted:
        adaptive_cap -= 2

    if separation >= 8.0 and shrink_permitted:
        adaptive_cap -= 2
    elif separation <= 2.5:
        adaptive_cap += 2

    adaptive_cap = max(6, adaptive_cap)
    adaptive_cap = min(18, adaptive_cap)
    adaptive_cap = min(len(scored_candidate_specs), adaptive_cap)
    return adaptive_cap


def _criticality_score(block_data: dict[str, Any], feasible_bay_count: int) -> float:
    return (10.0 / max(1, feasible_bay_count)) + _future_block_pressure(block_data) + _preference_gap(block_data)


def _rank_combined_perturbation_blocks(
    problem: dict[str, Any],
    assignments: dict[int, dict[str, int]],
    *,
    bays: list[Any],
    baseline_module: ModuleType,
    prioritize_incumbent_pressure: bool,
    include_load_pressure: bool,
    use_objective_contribution: bool,
) -> list[int]:
    bay_load_pressure = _incumbent_bay_load_pressure(problem, assignments, bays)
    objective_contributions = _incumbent_objective_contributions(problem, assignments, bays, bay_load_pressure)
    return sorted(
        assignments.keys(),
        key=lambda block_id: (
            -_combined_perturbation_priority(
                problem["blocks"][block_id],
                assignments[block_id],
                feasible_bay_count=len(_feasible_bays_for_block(problem["blocks"][block_id], bays, baseline_module)),
                prioritize_incumbent_pressure=prioritize_incumbent_pressure,
                load_pressure=bay_load_pressure.get(int(assignments[block_id]["bay_id"]), 0.0) if include_load_pressure else 0.0,
                objective_contribution=objective_contributions.get(block_id, 0.0),
                use_objective_contribution=use_objective_contribution,
            ),
            block_id,
        ),
    )


def _combined_perturbation_priority(
    block_data: dict[str, Any],
    assignment: dict[str, int],
    *,
    feasible_bay_count: int,
    prioritize_incumbent_pressure: bool,
    load_pressure: float,
    objective_contribution: float,
    use_objective_contribution: bool,
) -> float:
    priority = _criticality_score(block_data, feasible_bay_count)
    if not prioritize_incumbent_pressure:
        return priority

    if use_objective_contribution:
        return priority + objective_contribution

    exit_time = int(assignment.get("exit_time", assignment["entry_time"]))
    tardiness = max(0, exit_time - int(block_data["due_date"]))
    assigned_bay = int(assignment["bay_id"])
    preference_penalty = max(block_data["bay_preferences"]) - block_data["bay_preferences"][assigned_bay]
    return priority + (3.0 * tardiness) + preference_penalty + load_pressure


def _incumbent_objective_contributions(
    problem: dict[str, Any],
    assignments: dict[int, dict[str, int]],
    bays: list[Any],
    bay_load_pressure: dict[int, float],
) -> dict[int, float]:
    bay_areas = [bay.width * bay.height for bay in bays]
    average_bay_area = sum(bay_areas) / len(bay_areas)
    bay_weights = [average_bay_area / area for area in bay_areas]
    weighted_loads = [0.0 for _ in bays]
    for block_id, assignment in assignments.items():
        bay_id = int(assignment["bay_id"])
        weighted_loads[bay_id] += bay_weights[bay_id] * float(problem["blocks"][block_id]["workload"])

    w1 = float(problem.get("weights", {}).get("w1", 1.0))
    w2 = float(problem.get("weights", {}).get("w2", 1.0))
    w3 = float(problem.get("weights", {}).get("w3", 1.0))
    contributions: dict[int, float] = {}
    for block_id, assignment in assignments.items():
        block_data = problem["blocks"][block_id]
        bay_id = int(assignment["bay_id"])
        exit_time = int(assignment.get("exit_time", assignment["entry_time"]))
        tardiness = max(0, exit_time - int(block_data["due_date"]))
        preference_penalty = max(block_data["bay_preferences"]) - block_data["bay_preferences"][bay_id]
        weighted_workload = bay_weights[bay_id] * float(block_data["workload"])
        load_share = 0.0
        if weighted_loads[bay_id] > 0:
            load_share = bay_load_pressure.get(bay_id, 0.0) * (weighted_workload / weighted_loads[bay_id])
        contributions[block_id] = (w1 * tardiness) + (w2 * load_share) + (w3 * preference_penalty)

    return contributions


def _incumbent_bay_load_pressure(
    problem: dict[str, Any],
    assignments: dict[int, dict[str, int]],
    bays: list[Any],
) -> dict[int, float]:
    bay_areas = [bay.width * bay.height for bay in bays]
    average_bay_area = sum(bay_areas) / len(bay_areas)
    bay_weights = [average_bay_area / area for area in bay_areas]
    weighted_loads = [0.0 for _ in bays]

    for block_id, assignment in assignments.items():
        bay_id = int(assignment["bay_id"])
        weighted_loads[bay_id] += bay_weights[bay_id] * float(problem["blocks"][block_id]["workload"])

    return {
        bay_id: max(
            (abs(weighted_loads[bay_id] - weighted_loads[other_bay_id]) for other_bay_id in range(len(weighted_loads)) if other_bay_id != bay_id),
            default=0.0,
        )
        for bay_id in range(len(weighted_loads))
    }


def _top_alternative_bays(
    block_data: dict[str, Any],
    *,
    assigned_bay: int,
    bays: list[Any],
    baseline_module: ModuleType,
    limit: int,
) -> list[int]:
    feasible_bays = _feasible_bays_for_block(block_data, bays, baseline_module)
    return sorted(
        (bay_id for bay_id in feasible_bays if bay_id != assigned_bay),
        key=lambda bay_id: (-block_data["bay_preferences"][bay_id], bay_id),
    )[:limit]


def _promote_blocks_in_order(block_order: list[int], block_ids: list[int]) -> list[int]:
    promoted_ids = [block_id for block_id in block_ids if block_id in block_order]
    if not promoted_ids:
        return list(block_order)
    order = [candidate for candidate in block_order if candidate not in promoted_ids]
    insert_at = min(2, len(order))
    order[insert_at:insert_at] = promoted_ids
    return order


def _rebuild_order_around_blocks(block_order: list[int], block_ids: list[int]) -> list[int]:
    prioritized_ids = [block_id for block_id in block_ids if block_id in block_order]
    if not prioritized_ids:
        return list(block_order)
    return prioritized_ids + [candidate for candidate in block_order if candidate not in prioritized_ids]


def _build_rebuild_order_variants(
    block_order: list[int],
    block_ids: list[int],
    *,
    explore_order_variants: bool,
) -> list[list[int]]:
    prioritized_ids = [block_id for block_id in block_ids if block_id in block_order]
    if not prioritized_ids:
        return [list(block_order)]

    order_variants: list[list[int]] = []
    seen_orders: set[tuple[int, ...]] = set()
    candidate_prefixes: list[list[int]] = [prioritized_ids]
    if explore_order_variants and len(prioritized_ids) > 1:
        for permutation in permutations(prioritized_ids, len(prioritized_ids)):
            candidate_prefixes.append(list(permutation))
            if len(candidate_prefixes) >= 4:
                break

    for prefix in candidate_prefixes:
        rebuilt_order = prefix + [candidate for candidate in block_order if candidate not in prefix]
        order_key = tuple(rebuilt_order)
        if order_key not in seen_orders:
            seen_orders.add(order_key)
            order_variants.append(rebuilt_order)

    return order_variants


def _build_reinsertion_order_variants(
    block_order: list[int],
    block_ids: list[int],
    *,
    explore_staggered_variants: bool,
) -> list[list[int]]:
    focus_blocks = [block_id for block_id in block_ids if block_id in block_order]
    if not focus_blocks:
        return [list(block_order)]

    base_order = [candidate for candidate in block_order if candidate not in focus_blocks]
    anchor_positions = sorted({0, min(2, len(base_order)), len(base_order)})
    order_variants: list[list[int]] = []
    seen_orders: set[tuple[int, ...]] = set()

    for focus_permutation in permutations(focus_blocks, len(focus_blocks)):
        for anchor in anchor_positions:
            rebuilt_order = list(base_order)
            rebuilt_order[anchor:anchor] = list(focus_permutation)
            order_key = tuple(rebuilt_order)
            if order_key not in seen_orders:
                seen_orders.add(order_key)
                order_variants.append(rebuilt_order)
        if explore_staggered_variants and len(focus_permutation) > 1:
            staggered_anchors = list(anchor_positions[: min(len(anchor_positions), len(focus_permutation))])
            rebuilt_order = list(base_order)
            inserted = 0
            for focus_block, anchor in zip(focus_permutation, staggered_anchors, strict=False):
                insert_at = min(anchor + inserted, len(rebuilt_order))
                rebuilt_order.insert(insert_at, focus_block)
                inserted += 1
            for focus_block in focus_permutation[len(staggered_anchors) :]:
                rebuilt_order.append(focus_block)

            order_key = tuple(rebuilt_order)
            if order_key not in seen_orders:
                seen_orders.add(order_key)
                order_variants.append(rebuilt_order)
        if len(order_variants) >= 6:
            break

    return order_variants


def _extract_solution_assignments(solution: dict[str, Any]) -> dict[int, dict[str, int]]:
    operations = solution.get("operations", {})
    assignments: dict[int, dict[str, int]] = {}
    if not isinstance(operations, dict):
        return assignments

    for time_key in sorted(operations.keys(), key=lambda key: int(key)):
        for operation in operations[time_key]:
            block_id = int(operation["block_id"])
            if operation.get("type") == "ENTRY":
                assignments[block_id] = {
                    "bay_id": int(operation["bay_id"]),
                    "x": int(operation["x"]),
                    "y": int(operation["y"]),
                    "orient_idx": int(operation["orient_idx"]),
                    "entry_time": int(time_key),
                }
            elif operation.get("type") == "EXIT":
                assignments.setdefault(block_id, {})["exit_time"] = int(time_key)
    return assignments


@lru_cache(maxsize=1)
def _load_official_utils_module() -> ModuleType:
    utils_path = _official_utils_path()
    if not utils_path.exists():
        raise OfficialSupportError(
            "Official baseline utility is unavailable. Expected utils.py at "
            f"{utils_path}."
        )

    spec = importlib.util.spec_from_file_location("yardmind_official_utils", utils_path)
    if spec is None or spec.loader is None:
        raise OfficialSupportError(f"Unable to load official baseline utility from {utils_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    sys.modules["utils"] = module
    return module


@lru_cache(maxsize=1)
def _load_official_baseline_greedy_module() -> ModuleType:
    baseline_path = _official_baseline_greedy_path()
    if not baseline_path.exists():
        raise OfficialSupportError(
            "Official baseline greedy algorithm is unavailable. Expected baseline_greedy.py at "
            f"{baseline_path}."
        )

    sys.modules["utils"] = _load_official_utils_module()
    spec = importlib.util.spec_from_file_location("yardmind_official_baseline_greedy", baseline_path)
    if spec is None or spec.loader is None:
        raise OfficialSupportError(f"Unable to load official greedy baseline from {baseline_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _official_utils_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "artifacts"
        / "official-reference"
        / "baseline"
        / "ogc2026"
        / "baseline"
        / "utils.py"
    )


def _official_baseline_greedy_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "artifacts"
        / "official-reference"
        / "baseline"
        / "ogc2026"
        / "baseline"
        / "baseline_greedy.py"
    )