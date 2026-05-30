from pathlib import Path

import pytest

from yardmind.loader import InstanceFormatError, load_instance
from yardmind.models import Placement
from yardmind.official_compare import generate_official_constructive_comparison
from yardmind.official import (
    _build_bay_bias_candidates,
    _build_combined_perturbation_candidates,
    _build_objective_partial_reconstruction_diagnostics,
    _build_objective_partial_reconstruction_candidates,
    _build_objective_rebuild_candidates,
    _build_objective_reinsertion_candidates,
    _build_order_neighbors,
    _build_official_search_orders,
    _evaluate_native_order_candidates,
    _evaluate_bay_bias_candidates,
    _evaluate_combined_perturbation_candidates,
    _evaluate_partial_reconstruction_candidates,
    _select_best_official_candidate,
    load_official_solution,
    solve_official_constructive,
    solve_official_constructive_native,
    solve_official_search,
    validate_official_solution,
)
from yardmind.solver.constructive import ConstructiveSolver
from yardmind.solver.feasibility import FeasibilityChecker
from yardmind.solver.scoring import score_placement_candidate

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_load_instance_reads_sample() -> None:
    instance = load_instance(Path("examples/sample-instance.json"))
    assert instance.yard.width == 12
    assert instance.yard.min_clearance == 1
    assert len(instance.blocks) == 3


def test_load_instance_reads_official_sample() -> None:
    instance = load_instance(Path("examples/official-sample-instance.json"), input_format="official")

    assert instance.source_format == "official"
    assert instance.name == "official-sample-instance"
    assert len(instance.bays) == 2
    assert instance.weights == {"w1": 10.0, "w2": 3.0, "w3": 1.0}
    assert instance.yard.width == 10
    assert instance.yard.height == 6
    assert len(instance.blocks) == 2
    assert instance.block_by_id("0").metadata["processing_time"] == 4
    assert instance.block_by_id("1").metadata["bay_preferences"] == [4, 9]


def test_load_instance_rejects_development_schema_when_official_requested() -> None:
    with pytest.raises(InstanceFormatError, match="Missing required top-level field: bays"):
        load_instance(Path("examples/sample-instance.json"), input_format="official")


def test_validate_official_sample_solution() -> None:
    instance = load_instance(Path("examples/official-sample-instance.json"), input_format="official")
    solution = load_official_solution(Path("examples/official-sample-solution.json"))

    result = validate_official_solution(instance.metadata["raw_problem"], solution)

    assert result["feasible"] is True
    assert result["stage"] == 5
    assert result["violations"] == []
    assert result["objective"] == 0.0


def test_official_constructive_baseline_returns_feasible_solution() -> None:
    instance = load_instance(Path("examples/official-sample-instance.json"), input_format="official")

    solution = solve_official_constructive(instance.metadata["raw_problem"], timelimit=5.0)
    result = validate_official_solution(instance.metadata["raw_problem"], solution)

    assert "operations" in solution
    assert result["feasible"] is True
    assert result["stage"] == 5


def test_official_constructive_native_returns_feasible_solution() -> None:
    instance = load_instance(Path("examples/official-sample-instance.json"), input_format="official")

    solution = solve_official_constructive_native(instance.metadata["raw_problem"], timelimit=5.0)
    result = validate_official_solution(instance.metadata["raw_problem"], solution)

    assert "operations" in solution
    assert result["feasible"] is True
    assert result["stage"] == 5
    assert result["objective"] == 0.0


def test_official_search_returns_feasible_solution() -> None:
    instance = load_instance(Path("examples/official-sample-instance.json"), input_format="official")

    solution = solve_official_search(instance.metadata["raw_problem"], timelimit=5.0)
    result = validate_official_solution(instance.metadata["raw_problem"], solution)

    assert "operations" in solution
    assert result["feasible"] is True
    assert result["stage"] == 5


def test_official_search_selects_better_candidate_on_capacity_preservation_case() -> None:
    problem = {
        "name": "native-capacity-preservation",
        "bays": [
            {"width": 6, "height": 6},
            {"width": 4, "height": 6},
        ],
        "blocks": [
            {
                "release_time": 0,
                "due_date": 3,
                "processing_time": 3,
                "workload": 1,
                "bay_preferences": [10, 9],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [4, 0], [4, 4], [0, 4]]
                        ],
                    }
                ],
            },
            {
                "release_time": 0,
                "due_date": 4,
                "processing_time": 4,
                "workload": 1,
                "bay_preferences": [10, 0],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [6, 0], [6, 4], [0, 4]]
                        ],
                    }
                ],
            },
        ],
        "weights": {"w1": 10, "w2": 3, "w3": 1},
    }

    delegated_result = validate_official_solution(problem, solve_official_constructive(problem, timelimit=5.0))
    native_result = validate_official_solution(problem, solve_official_constructive_native(problem, timelimit=5.0))
    search_result = validate_official_solution(problem, solve_official_search(problem, timelimit=5.0))

    assert delegated_result["objective"] == 35.0
    assert native_result["objective"] == 2.25
    assert search_result["feasible"] is True
    assert search_result["objective"] == native_result["objective"]


def test_official_search_can_improve_on_default_native_order() -> None:
    problem = {
        "name": "order-diversified-search",
        "bays": [
            {"width": 6, "height": 5},
            {"width": 5, "height": 6},
        ],
        "blocks": [
            {
                "release_time": 2,
                "due_date": 3,
                "processing_time": 1,
                "workload": 1,
                "bay_preferences": [6, 10],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [4, 0], [4, 2], [0, 2]]
                        ],
                    }
                ],
            },
            {
                "release_time": 2,
                "due_date": 8,
                "processing_time": 2,
                "workload": 4,
                "bay_preferences": [5, 1],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [6, 0], [6, 5], [0, 5]]
                        ],
                    }
                ],
            },
            {
                "release_time": 2,
                "due_date": 6,
                "processing_time": 2,
                "workload": 2,
                "bay_preferences": [7, 1],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [6, 0], [6, 3], [0, 3]]
                        ],
                    }
                ],
            },
            {
                "release_time": 2,
                "due_date": 4,
                "processing_time": 3,
                "workload": 9,
                "bay_preferences": [4, 1],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [4, 0], [4, 5], [0, 5]]
                        ],
                    }
                ],
            },
        ],
        "weights": {"w1": 10, "w2": 3, "w3": 1},
    }

    native_result = validate_official_solution(problem, solve_official_constructive_native(problem, timelimit=1.0))
    search_result = validate_official_solution(problem, solve_official_search(problem, timelimit=1.0))

    assert native_result["feasible"] is True
    assert search_result["feasible"] is True
    assert native_result["objective"] == 72.0
    assert search_result["objective"] == 23.0
    assert search_result["objective"] < native_result["objective"]


def test_official_search_local_order_improvement_beats_fixed_order_portfolio() -> None:
    problem = {
        "name": "local-order-neighborhood-search",
        "bays": [
            {"width": 5, "height": 6},
            {"width": 6, "height": 6},
        ],
        "blocks": [
            {
                "release_time": 2,
                "due_date": 5,
                "processing_time": 5,
                "workload": 1,
                "bay_preferences": [3, 6],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [2, 0], [2, 5], [0, 5]]
                        ],
                    }
                ],
            },
            {
                "release_time": 1,
                "due_date": 6,
                "processing_time": 5,
                "workload": 7,
                "bay_preferences": [7, 5],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [5, 0], [5, 4], [0, 4]]
                        ],
                    }
                ],
            },
            {
                "release_time": 2,
                "due_date": 8,
                "processing_time": 4,
                "workload": 3,
                "bay_preferences": [0, 3],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [4, 0], [4, 2], [0, 2]]
                        ],
                    }
                ],
            },
            {
                "release_time": 1,
                "due_date": 4,
                "processing_time": 5,
                "workload": 2,
                "bay_preferences": [0, 10],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [6, 0], [6, 3], [0, 3]]
                        ],
                    }
                ],
            },
        ],
        "weights": {"w1": 10, "w2": 3, "w3": 1},
    }

    initial_orders = _build_official_search_orders(problem)
    initial_solutions, _ = _evaluate_native_order_candidates(problem, initial_orders, timelimit=0.6)
    initial_best = min(
        float(result["objective"])
        for result in (validate_official_solution(problem, solution) for solution in initial_solutions)
        if result["feasible"]
    )
    search_result = validate_official_solution(problem, solve_official_search(problem, timelimit=1.0))

    assert initial_best == pytest.approx(124.7)
    assert search_result["feasible"] is True
    assert float(search_result["objective"]) == pytest.approx(86.6)
    assert float(search_result["objective"]) < initial_best


def test_official_search_bay_bias_improvement_beats_order_only_search() -> None:
    problem = {
        "name": "bay-bias-search",
        "bays": [
            {"width": 6, "height": 6},
            {"width": 4, "height": 5},
        ],
        "blocks": [
            {
                "release_time": 0,
                "due_date": 10,
                "processing_time": 2,
                "workload": 6,
                "bay_preferences": [10, 10],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [5, 0], [5, 3], [0, 3]]
                        ],
                    }
                ],
            },
            {
                "release_time": 2,
                "due_date": 10,
                "processing_time": 2,
                "workload": 8,
                "bay_preferences": [9, 6],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [2, 0], [2, 2], [0, 2]]
                        ],
                    }
                ],
            },
            {
                "release_time": 1,
                "due_date": 5,
                "processing_time": 3,
                "workload": 7,
                "bay_preferences": [4, 9],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [6, 0], [6, 4], [0, 4]]
                        ],
                    }
                ],
            },
            {
                "release_time": 0,
                "due_date": 3,
                "processing_time": 3,
                "workload": 3,
                "bay_preferences": [2, 2],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [2, 0], [2, 3], [0, 3]]
                        ],
                    }
                ],
            },
        ],
        "weights": {"w1": 10, "w2": 3, "w3": 1},
    }

    initial_orders = _build_official_search_orders(problem)
    initial_solutions, best_order = _evaluate_native_order_candidates(problem, initial_orders, timelimit=0.45)
    assert best_order is not None
    neighbor_solutions, _ = _evaluate_native_order_candidates(
        problem,
        _build_order_neighbors(best_order),
        timelimit=0.35,
    )
    _, order_only_result = _select_best_official_candidate(problem, initial_solutions + neighbor_solutions)
    search_result = validate_official_solution(problem, solve_official_search(problem, timelimit=1.0))

    assert order_only_result is not None
    assert order_only_result["feasible"] is True
    assert float(order_only_result["objective"]) == pytest.approx(23.866666666666664)
    assert search_result["feasible"] is True
    assert float(search_result["objective"]) == pytest.approx(21.733333333333334)
    assert float(search_result["objective"]) < float(order_only_result["objective"])


def test_official_search_combined_perturbation_beats_precombined_search() -> None:
    problem = {
        "name": "combined-perturbation-search",
        "bays": [
            {"width": 6, "height": 5},
            {"width": 5, "height": 6},
        ],
        "blocks": [
            {
                "release_time": 2,
                "due_date": 10,
                "processing_time": 2,
                "workload": 10,
                "bay_preferences": [4, 10],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [6, 0], [6, 5], [0, 5]]
                        ],
                    }
                ],
            },
            {
                "release_time": 0,
                "due_date": 5,
                "processing_time": 5,
                "workload": 6,
                "bay_preferences": [7, 6],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [4, 0], [4, 2], [0, 2]]
                        ],
                    }
                ],
            },
            {
                "release_time": 1,
                "due_date": 8,
                "processing_time": 3,
                "workload": 3,
                "bay_preferences": [4, 5],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [3, 0], [3, 4], [0, 4]]
                        ],
                    }
                ],
            },
            {
                "release_time": 1,
                "due_date": 7,
                "processing_time": 5,
                "workload": 8,
                "bay_preferences": [6, 8],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [2, 0], [2, 3], [0, 3]]
                        ],
                    }
                ],
            },
        ],
        "weights": {"w1": 10, "w2": 3, "w3": 1},
    }

    initial_orders = _build_official_search_orders(problem)
    initial_solutions, best_order = _evaluate_native_order_candidates(problem, initial_orders, timelimit=0.45)
    assert best_order is not None
    neighbor_solutions, _ = _evaluate_native_order_candidates(
        problem,
        _build_order_neighbors(best_order),
        timelimit=0.25,
    )
    best_sol, _ = _select_best_official_candidate(problem, initial_solutions + neighbor_solutions)
    assert best_sol is not None
    bias_candidates = _build_bay_bias_candidates(problem, best_sol)
    bias_solutions = _evaluate_bay_bias_candidates(
        problem,
        block_order=best_order,
        candidate_biases=bias_candidates,
        timelimit=0.2,
    )
    _, precombined_result = _select_best_official_candidate(problem, initial_solutions + neighbor_solutions + bias_solutions)
    search_result = validate_official_solution(problem, solve_official_search(problem, timelimit=1.0))

    assert precombined_result is not None
    assert precombined_result["feasible"] is True
    assert float(precombined_result["objective"]) == pytest.approx(21.0)
    assert search_result["feasible"] is True
    assert float(search_result["objective"]) == pytest.approx(11.0)
    assert float(search_result["objective"]) < float(precombined_result["objective"])


def test_official_search_paired_perturbation_beats_single_combined_moves() -> None:
    problem = {
        "name": "paired-combined-perturbation-search",
        "bays": [
            {"width": 6, "height": 6},
            {"width": 6, "height": 5},
            {"width": 5, "height": 5},
        ],
        "blocks": [
            {
                "release_time": 2,
                "due_date": 7,
                "processing_time": 6,
                "workload": 7,
                "bay_preferences": [10, 2, 3],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [2, 0], [2, 2], [0, 2]]
                        ],
                    }
                ],
            },
            {
                "release_time": 2,
                "due_date": 11,
                "processing_time": 5,
                "workload": 5,
                "bay_preferences": [5, 6, 4],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [3, 0], [3, 3], [0, 3]]
                        ],
                    }
                ],
            },
            {
                "release_time": 3,
                "due_date": 7,
                "processing_time": 6,
                "workload": 4,
                "bay_preferences": [5, 5, 2],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [4, 0], [4, 6], [0, 6]]
                        ],
                    }
                ],
            },
            {
                "release_time": 0,
                "due_date": 5,
                "processing_time": 1,
                "workload": 5,
                "bay_preferences": [1, 7, 8],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [6, 0], [6, 3], [0, 3]]
                        ],
                    }
                ],
            },
            {
                "release_time": 1,
                "due_date": 10,
                "processing_time": 4,
                "workload": 1,
                "bay_preferences": [5, 4, 6],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [5, 0], [5, 2], [0, 2]]
                        ],
                    }
                ],
            },
        ],
        "weights": {"w1": 10, "w2": 3, "w3": 1},
    }

    initial_orders = _build_official_search_orders(problem)
    initial_solutions, best_order = _evaluate_native_order_candidates(problem, initial_orders, timelimit=0.45)
    assert best_order is not None
    neighbor_solutions, _ = _evaluate_native_order_candidates(
        problem,
        _build_order_neighbors(best_order),
        timelimit=0.25,
    )
    candidate_solutions = initial_solutions + neighbor_solutions
    best_sol, _ = _select_best_official_candidate(problem, candidate_solutions)
    assert best_sol is not None
    bias_candidates = _build_bay_bias_candidates(problem, best_sol)
    candidate_solutions.extend(
        _evaluate_bay_bias_candidates(
            problem,
            block_order=best_order,
            candidate_biases=bias_candidates,
            timelimit=0.2,
        )
    )
    best_sol, _ = _select_best_official_candidate(problem, candidate_solutions)
    assert best_sol is not None

    combined_specs = _build_combined_perturbation_candidates(problem, best_sol, best_order)
    single_specs = [spec for spec in combined_specs if len(spec[1]) == 1]
    single_combined_solutions = candidate_solutions + _evaluate_combined_perturbation_candidates(
        problem,
        candidate_specs=single_specs,
        timelimit=0.25,
    )
    _, single_combined_result = _select_best_official_candidate(problem, single_combined_solutions)
    search_result = validate_official_solution(problem, solve_official_search(problem, timelimit=1.0))

    assert single_combined_result is not None
    assert single_combined_result["feasible"] is True
    assert float(single_combined_result["objective"]) == pytest.approx(45.63888888888889)
    assert search_result["feasible"] is True
    assert float(search_result["objective"]) == pytest.approx(44.605555555555554)
    assert float(search_result["objective"]) < float(single_combined_result["objective"])


def test_official_search_incumbent_aware_combined_ranking_beats_static_ranking() -> None:
    problem = {
        "name": "incumbent-aware-combined-ranking-search",
        "bays": [
            {"width": 6, "height": 6},
            {"width": 5, "height": 4},
            {"width": 4, "height": 6},
        ],
        "blocks": [
            {
                "release_time": 0,
                "due_date": 7,
                "processing_time": 5,
                "workload": 8,
                "bay_preferences": [7, 4, 0],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [2, 0], [2, 4], [0, 4]]
                        ],
                    }
                ],
            },
            {
                "release_time": 0,
                "due_date": 6,
                "processing_time": 6,
                "workload": 7,
                "bay_preferences": [3, 10, 0],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [4, 0], [4, 5], [0, 5]]
                        ],
                    }
                ],
            },
            {
                "release_time": 3,
                "due_date": 5,
                "processing_time": 4,
                "workload": 5,
                "bay_preferences": [7, 9, 8],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [3, 0], [3, 5], [0, 5]]
                        ],
                    }
                ],
            },
            {
                "release_time": 2,
                "due_date": 8,
                "processing_time": 1,
                "workload": 4,
                "bay_preferences": [0, 7, 6],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [6, 0], [6, 3], [0, 3]]
                        ],
                    }
                ],
            },
            {
                "release_time": 3,
                "due_date": 8,
                "processing_time": 6,
                "workload": 6,
                "bay_preferences": [6, 5, 4],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [2, 0], [2, 5], [0, 5]]
                        ],
                    }
                ],
            },
        ],
        "weights": {"w1": 10, "w2": 3, "w3": 1},
    }

    initial_orders = _build_official_search_orders(problem)
    initial_solutions, best_order = _evaluate_native_order_candidates(problem, initial_orders, timelimit=0.45)
    assert best_order is not None
    neighbor_solutions, _ = _evaluate_native_order_candidates(
        problem,
        _build_order_neighbors(best_order),
        timelimit=0.25,
    )
    candidate_solutions = initial_solutions + neighbor_solutions
    best_sol, _ = _select_best_official_candidate(problem, candidate_solutions)
    assert best_sol is not None
    bias_candidates = _build_bay_bias_candidates(problem, best_sol)
    candidate_solutions.extend(
        _evaluate_bay_bias_candidates(
            problem,
            block_order=best_order,
            candidate_biases=bias_candidates,
            timelimit=0.2,
        )
    )
    best_sol, _ = _select_best_official_candidate(problem, candidate_solutions)
    assert best_sol is not None

    static_combined_specs = _build_combined_perturbation_candidates(
        problem,
        best_sol,
        best_order,
        prioritize_incumbent_pressure=False,
    )
    static_solutions = candidate_solutions + _evaluate_combined_perturbation_candidates(
        problem,
        candidate_specs=static_combined_specs,
        timelimit=0.25,
    )
    _, static_result = _select_best_official_candidate(problem, static_solutions)
    search_result = validate_official_solution(problem, solve_official_search(problem, timelimit=1.0))

    assert static_result is not None
    assert static_result["feasible"] is True
    assert float(static_result["objective"]) == pytest.approx(89.11111111111111)
    assert search_result["feasible"] is True
    assert float(search_result["objective"]) == pytest.approx(62.0)
    assert float(search_result["objective"]) < float(static_result["objective"])


def test_official_search_load_aware_combined_ranking_is_not_worse_than_load_blind_ranking() -> None:
    problem = {
        "name": "load-aware-combined-ranking-search",
        "bays": [
            {"width": 5, "height": 6},
            {"width": 6, "height": 4},
            {"width": 4, "height": 6},
        ],
        "blocks": [
            {
                "release_time": 2,
                "due_date": 7,
                "processing_time": 5,
                "workload": 7,
                "bay_preferences": [1, 4, 10],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [3, 0], [3, 2], [0, 2]]
                        ],
                    }
                ],
            },
            {
                "release_time": 1,
                "due_date": 9,
                "processing_time": 6,
                "workload": 10,
                "bay_preferences": [2, 2, 5],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [3, 0], [3, 2], [0, 2]]
                        ],
                    }
                ],
            },
            {
                "release_time": 2,
                "due_date": 10,
                "processing_time": 1,
                "workload": 9,
                "bay_preferences": [8, 2, 4],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [2, 0], [2, 6], [0, 6]]
                        ],
                    }
                ],
            },
            {
                "release_time": 1,
                "due_date": 5,
                "processing_time": 5,
                "workload": 2,
                "bay_preferences": [10, 7, 6],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [4, 0], [4, 2], [0, 2]]
                        ],
                    }
                ],
            },
            {
                "release_time": 0,
                "due_date": 9,
                "processing_time": 3,
                "workload": 3,
                "bay_preferences": [6, 1, 5],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [6, 0], [6, 2], [0, 2]]
                        ],
                    }
                ],
            },
        ],
        "weights": {"w1": 10, "w2": 3, "w3": 1},
    }

    initial_orders = _build_official_search_orders(problem)
    initial_solutions, best_order = _evaluate_native_order_candidates(problem, initial_orders, timelimit=0.45)
    assert best_order is not None
    neighbor_solutions, _ = _evaluate_native_order_candidates(
        problem,
        _build_order_neighbors(best_order),
        timelimit=0.25,
    )
    candidate_solutions = initial_solutions + neighbor_solutions
    best_sol, _ = _select_best_official_candidate(problem, candidate_solutions)
    assert best_sol is not None
    bias_candidates = _build_bay_bias_candidates(problem, best_sol)
    candidate_solutions.extend(
        _evaluate_bay_bias_candidates(
            problem,
            block_order=best_order,
            candidate_biases=bias_candidates,
            timelimit=0.2,
        )
    )
    best_sol, _ = _select_best_official_candidate(problem, candidate_solutions)
    assert best_sol is not None

    no_load_combined_specs = _build_combined_perturbation_candidates(
        problem,
        best_sol,
        best_order,
        prioritize_incumbent_pressure=True,
        include_load_pressure=False,
        use_objective_contribution=True,
    )
    no_load_solutions = candidate_solutions + _evaluate_combined_perturbation_candidates(
        problem,
        candidate_specs=no_load_combined_specs,
        timelimit=0.25,
    )
    _, no_load_result = _select_best_official_candidate(problem, no_load_solutions)
    search_result = validate_official_solution(problem, solve_official_search(problem, timelimit=1.0))

    assert no_load_result is not None
    assert no_load_result["feasible"] is True
    assert search_result["feasible"] is True
    assert float(search_result["objective"]) == pytest.approx(24.9)
    assert float(search_result["objective"]) <= float(no_load_result["objective"])


def test_official_search_objective_aware_combined_ranking_beats_additive_ranking() -> None:
    problem = {
        "name": "objective-aware-combined-ranking-search",
        "bays": [
            {"width": 4, "height": 6},
            {"width": 6, "height": 6},
            {"width": 6, "height": 6},
        ],
        "blocks": [
            {
                "release_time": 0,
                "due_date": 6,
                "processing_time": 3,
                "workload": 4,
                "bay_preferences": [7, 3, 0],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [4, 0], [4, 6], [0, 6]]
                        ],
                    }
                ],
            },
            {
                "release_time": 0,
                "due_date": 12,
                "processing_time": 6,
                "workload": 5,
                "bay_preferences": [6, 5, 3],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [4, 0], [4, 6], [0, 6]]
                        ],
                    }
                ],
            },
            {
                "release_time": 1,
                "due_date": 5,
                "processing_time": 4,
                "workload": 6,
                "bay_preferences": [8, 3, 8],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [4, 0], [4, 5], [0, 5]]
                        ],
                    }
                ],
            },
            {
                "release_time": 0,
                "due_date": 8,
                "processing_time": 1,
                "workload": 10,
                "bay_preferences": [10, 10, 9],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [2, 0], [2, 5], [0, 5]]
                        ],
                    }
                ],
            },
            {
                "release_time": 3,
                "due_date": 6,
                "processing_time": 1,
                "workload": 6,
                "bay_preferences": [1, 1, 8],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [5, 0], [5, 5], [0, 5]]
                        ],
                    }
                ],
            },
        ],
        "weights": {"w1": 10, "w2": 3, "w3": 1},
    }

    initial_orders = _build_official_search_orders(problem)
    initial_solutions, best_order = _evaluate_native_order_candidates(problem, initial_orders, timelimit=0.45)
    assert best_order is not None
    neighbor_solutions, _ = _evaluate_native_order_candidates(
        problem,
        _build_order_neighbors(best_order),
        timelimit=0.25,
    )
    candidate_solutions = initial_solutions + neighbor_solutions
    best_sol, _ = _select_best_official_candidate(problem, candidate_solutions)
    assert best_sol is not None
    bias_candidates = _build_bay_bias_candidates(problem, best_sol)
    candidate_solutions.extend(
        _evaluate_bay_bias_candidates(
            problem,
            block_order=best_order,
            candidate_biases=bias_candidates,
            timelimit=0.2,
        )
    )
    best_sol, _ = _select_best_official_candidate(problem, candidate_solutions)
    assert best_sol is not None

    additive_combined_specs = _build_combined_perturbation_candidates(
        problem,
        best_sol,
        best_order,
        prioritize_incumbent_pressure=True,
        include_load_pressure=True,
        use_objective_contribution=False,
    )
    additive_solutions = candidate_solutions + _evaluate_combined_perturbation_candidates(
        problem,
        candidate_specs=additive_combined_specs,
        timelimit=0.25,
    )
    _, additive_result = _select_best_official_candidate(problem, additive_solutions)
    search_result = validate_official_solution(problem, solve_official_search(problem, timelimit=1.0))

    assert additive_result is not None
    assert additive_result["feasible"] is True
    assert float(additive_result["objective"]) == pytest.approx(20.33333333333333)
    assert search_result["feasible"] is True
    assert float(search_result["objective"]) == pytest.approx(9.333333333333332)
    assert float(search_result["objective"]) < float(additive_result["objective"])


def test_official_search_rebuild_stage_beats_pre_rebuild_search() -> None:
    problem = {
        "name": "objective-rebuild-search",
        "bays": [
            {"width": 5, "height": 6},
            {"width": 6, "height": 6},
            {"width": 5, "height": 6},
        ],
        "blocks": [
            {
                "release_time": 0,
                "due_date": 5,
                "processing_time": 3,
                "workload": 7,
                "bay_preferences": [3, 9, 9],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [4, 0], [4, 6], [0, 6]]
                        ],
                    }
                ],
            },
            {
                "release_time": 2,
                "due_date": 5,
                "processing_time": 5,
                "workload": 5,
                "bay_preferences": [0, 6, 5],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [6, 0], [6, 6], [0, 6]]
                        ],
                    }
                ],
            },
            {
                "release_time": 1,
                "due_date": 4,
                "processing_time": 2,
                "workload": 3,
                "bay_preferences": [5, 10, 10],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [4, 0], [4, 5], [0, 5]]
                        ],
                    }
                ],
            },
            {
                "release_time": 3,
                "due_date": 7,
                "processing_time": 1,
                "workload": 6,
                "bay_preferences": [10, 9, 7],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [3, 0], [3, 4], [0, 4]]
                        ],
                    }
                ],
            },
            {
                "release_time": 1,
                "due_date": 6,
                "processing_time": 3,
                "workload": 4,
                "bay_preferences": [2, 6, 2],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [3, 0], [3, 6], [0, 6]]
                        ],
                    }
                ],
            },
        ],
        "weights": {"w1": 10, "w2": 3, "w3": 1},
    }

    initial_orders = _build_official_search_orders(problem)
    initial_solutions, best_order = _evaluate_native_order_candidates(problem, initial_orders, timelimit=0.45)
    assert best_order is not None
    neighbor_solutions, _ = _evaluate_native_order_candidates(
        problem,
        _build_order_neighbors(best_order),
        timelimit=0.25,
    )
    candidate_solutions = initial_solutions + neighbor_solutions
    best_sol, _ = _select_best_official_candidate(problem, candidate_solutions)
    assert best_sol is not None
    bias_candidates = _build_bay_bias_candidates(problem, best_sol)
    candidate_solutions.extend(
        _evaluate_bay_bias_candidates(
            problem,
            block_order=best_order,
            candidate_biases=bias_candidates,
            timelimit=0.2,
        )
    )
    best_sol, _ = _select_best_official_candidate(problem, candidate_solutions)
    assert best_sol is not None

    combined_candidates = _build_combined_perturbation_candidates(problem, best_sol, best_order)
    pre_rebuild_solutions = candidate_solutions + _evaluate_combined_perturbation_candidates(
        problem,
        candidate_specs=combined_candidates,
        timelimit=0.25,
    )
    _, pre_rebuild_result = _select_best_official_candidate(problem, pre_rebuild_solutions)
    search_result = validate_official_solution(problem, solve_official_search(problem, timelimit=1.0))

    assert pre_rebuild_result is not None
    assert pre_rebuild_result["feasible"] is True
    assert float(pre_rebuild_result["objective"]) == pytest.approx(46.8)
    assert search_result["feasible"] is True
    assert float(search_result["objective"]) == pytest.approx(44.666666666666664)
    assert float(search_result["objective"]) < float(pre_rebuild_result["objective"])


def test_official_search_expanded_rebuild_variants_beat_single_rebuild() -> None:
    problem = {
        "name": "expanded-rebuild-variants-search",
        "bays": [
            {"width": 6, "height": 4},
            {"width": 4, "height": 6},
            {"width": 5, "height": 6},
        ],
        "blocks": [
            {
                "release_time": 0,
                "due_date": 10,
                "processing_time": 6,
                "workload": 1,
                "bay_preferences": [4, 9, 3],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [2, 0], [2, 3], [0, 3]]
                        ],
                    }
                ],
            },
            {
                "release_time": 3,
                "due_date": 5,
                "processing_time": 4,
                "workload": 6,
                "bay_preferences": [9, 5, 3],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [4, 0], [4, 2], [0, 2]]
                        ],
                    }
                ],
            },
            {
                "release_time": 2,
                "due_date": 6,
                "processing_time": 3,
                "workload": 10,
                "bay_preferences": [3, 7, 10],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [4, 0], [4, 6], [0, 6]]
                        ],
                    }
                ],
            },
            {
                "release_time": 1,
                "due_date": 5,
                "processing_time": 4,
                "workload": 7,
                "bay_preferences": [0, 7, 3],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [3, 0], [3, 4], [0, 4]]
                        ],
                    }
                ],
            },
            {
                "release_time": 0,
                "due_date": 8,
                "processing_time": 6,
                "workload": 10,
                "bay_preferences": [6, 1, 9],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [5, 0], [5, 2], [0, 2]]
                        ],
                    }
                ],
            },
        ],
        "weights": {"w1": 10, "w2": 3, "w3": 1},
    }

    initial_orders = _build_official_search_orders(problem)
    initial_solutions, best_order = _evaluate_native_order_candidates(problem, initial_orders, timelimit=0.45)
    assert best_order is not None
    neighbor_solutions, _ = _evaluate_native_order_candidates(
        problem,
        _build_order_neighbors(best_order),
        timelimit=0.25,
    )
    candidate_solutions = initial_solutions + neighbor_solutions
    best_sol, _ = _select_best_official_candidate(problem, candidate_solutions)
    assert best_sol is not None
    bias_candidates = _build_bay_bias_candidates(problem, best_sol)
    candidate_solutions.extend(
        _evaluate_bay_bias_candidates(
            problem,
            block_order=best_order,
            candidate_biases=bias_candidates,
            timelimit=0.2,
        )
    )
    best_sol, _ = _select_best_official_candidate(problem, candidate_solutions)
    assert best_sol is not None
    combined_candidates = _build_combined_perturbation_candidates(problem, best_sol, best_order)
    candidate_solutions.extend(
        _evaluate_combined_perturbation_candidates(
            problem,
            candidate_specs=combined_candidates,
            timelimit=0.25,
        )
    )
    best_sol, _ = _select_best_official_candidate(problem, candidate_solutions)
    assert best_sol is not None

    single_rebuild_candidates = _build_objective_rebuild_candidates(
        problem,
        best_sol,
        best_order,
        explore_order_variants=False,
        max_alternative_bays=1,
    )
    single_rebuild_solutions = candidate_solutions + _evaluate_combined_perturbation_candidates(
        problem,
        candidate_specs=single_rebuild_candidates,
        timelimit=0.15,
    )
    _, single_rebuild_result = _select_best_official_candidate(problem, single_rebuild_solutions)
    search_result = validate_official_solution(problem, solve_official_search(problem, timelimit=1.0))

    assert single_rebuild_result is not None
    assert single_rebuild_result["feasible"] is True
    assert float(single_rebuild_result["objective"]) == pytest.approx(56.49999999999999)
    assert search_result["feasible"] is True
    assert float(search_result["objective"]) == pytest.approx(45.900000000000006)
    assert float(search_result["objective"]) < float(single_rebuild_result["objective"])


def test_official_search_reinsertion_stage_beats_pre_reinsertion_search() -> None:
    problem = {
        "name": "objective-reinsertion-search",
        "bays": [
            {"width": 5, "height": 5},
            {"width": 6, "height": 4},
            {"width": 6, "height": 6},
        ],
        "blocks": [
            {
                "release_time": 2,
                "due_date": 8,
                "processing_time": 3,
                "workload": 3,
                "bay_preferences": [0, 3, 0],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [5, 0], [5, 2], [0, 2]]
                        ],
                    }
                ],
            },
            {
                "release_time": 3,
                "due_date": 9,
                "processing_time": 3,
                "workload": 4,
                "bay_preferences": [8, 9, 9],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [3, 0], [3, 2], [0, 2]]
                        ],
                    }
                ],
            },
            {
                "release_time": 0,
                "due_date": 10,
                "processing_time": 6,
                "workload": 4,
                "bay_preferences": [3, 4, 1],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [2, 0], [2, 2], [0, 2]]
                        ],
                    }
                ],
            },
            {
                "release_time": 1,
                "due_date": 10,
                "processing_time": 5,
                "workload": 4,
                "bay_preferences": [3, 6, 6],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [5, 0], [5, 2], [0, 2]]
                        ],
                    }
                ],
            },
            {
                "release_time": 3,
                "due_date": 10,
                "processing_time": 2,
                "workload": 5,
                "bay_preferences": [7, 9, 4],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [3, 0], [3, 2], [0, 2]]
                        ],
                    }
                ],
            },
        ],
        "weights": {"w1": 10, "w2": 3, "w3": 1},
    }

    initial_orders = _build_official_search_orders(problem)
    initial_solutions, best_order = _evaluate_native_order_candidates(problem, initial_orders, timelimit=0.45)
    assert best_order is not None
    neighbor_solutions, _ = _evaluate_native_order_candidates(
        problem,
        _build_order_neighbors(best_order),
        timelimit=0.25,
    )
    candidate_solutions = initial_solutions + neighbor_solutions
    best_sol, _ = _select_best_official_candidate(problem, candidate_solutions)
    assert best_sol is not None
    bias_candidates = _build_bay_bias_candidates(problem, best_sol)
    candidate_solutions.extend(
        _evaluate_bay_bias_candidates(
            problem,
            block_order=best_order,
            candidate_biases=bias_candidates,
            timelimit=0.2,
        )
    )
    best_sol, _ = _select_best_official_candidate(problem, candidate_solutions)
    assert best_sol is not None
    combined_candidates = _build_combined_perturbation_candidates(problem, best_sol, best_order)
    candidate_solutions.extend(
        _evaluate_combined_perturbation_candidates(
            problem,
            candidate_specs=combined_candidates,
            timelimit=0.25,
        )
    )
    best_sol, _ = _select_best_official_candidate(problem, candidate_solutions)
    assert best_sol is not None
    rebuild_candidates = _build_objective_rebuild_candidates(problem, best_sol, best_order)
    pre_reinsertion_solutions = candidate_solutions + _evaluate_combined_perturbation_candidates(
        problem,
        candidate_specs=rebuild_candidates,
        timelimit=0.15,
    )
    _, pre_reinsertion_result = _select_best_official_candidate(problem, pre_reinsertion_solutions)
    search_result = validate_official_solution(problem, solve_official_search(problem, timelimit=1.0))

    assert pre_reinsertion_result is not None
    assert pre_reinsertion_result["feasible"] is True
    assert float(pre_reinsertion_result["objective"]) == pytest.approx(12.79166666666667)
    assert search_result["feasible"] is True
    assert float(search_result["objective"]) == pytest.approx(9.79166666666667)
    assert float(search_result["objective"]) < float(pre_reinsertion_result["objective"])


def test_official_search_staggered_reinsertion_beats_contiguous_only_reinsertion() -> None:
    problem = {
        "name": "staggered-reinsertion-search",
        "bays": [
            {"width": 5, "height": 6},
            {"width": 4, "height": 6},
            {"width": 5, "height": 4},
        ],
        "blocks": [
            {
                "release_time": 0,
                "due_date": 12,
                "processing_time": 2,
                "workload": 4,
                "bay_preferences": [8, 6, 6],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [5, 0], [5, 6], [0, 6]]
                        ],
                    }
                ],
            },
            {
                "release_time": 2,
                "due_date": 12,
                "processing_time": 3,
                "workload": 9,
                "bay_preferences": [8, 6, 8],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [2, 0], [2, 4], [0, 4]]
                        ],
                    }
                ],
            },
            {
                "release_time": 3,
                "due_date": 8,
                "processing_time": 6,
                "workload": 6,
                "bay_preferences": [3, 4, 8],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [4, 0], [4, 3], [0, 3]]
                        ],
                    }
                ],
            },
            {
                "release_time": 1,
                "due_date": 6,
                "processing_time": 3,
                "workload": 5,
                "bay_preferences": [9, 1, 0],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [4, 0], [4, 4], [0, 4]]
                        ],
                    }
                ],
            },
            {
                "release_time": 2,
                "due_date": 6,
                "processing_time": 1,
                "workload": 3,
                "bay_preferences": [9, 10, 5],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [4, 0], [4, 6], [0, 6]]
                        ],
                    }
                ],
            },
        ],
        "weights": {"w1": 10, "w2": 3, "w3": 1},
    }

    initial_orders = _build_official_search_orders(problem)
    initial_solutions, best_order = _evaluate_native_order_candidates(problem, initial_orders, timelimit=0.45)
    assert best_order is not None
    neighbor_solutions, _ = _evaluate_native_order_candidates(
        problem,
        _build_order_neighbors(best_order),
        timelimit=0.25,
    )
    candidate_solutions = initial_solutions + neighbor_solutions
    best_sol, _ = _select_best_official_candidate(problem, candidate_solutions)
    assert best_sol is not None
    bias_candidates = _build_bay_bias_candidates(problem, best_sol)
    candidate_solutions.extend(
        _evaluate_bay_bias_candidates(
            problem,
            block_order=best_order,
            candidate_biases=bias_candidates,
            timelimit=0.2,
        )
    )
    best_sol, _ = _select_best_official_candidate(problem, candidate_solutions)
    assert best_sol is not None
    combined_candidates = _build_combined_perturbation_candidates(problem, best_sol, best_order)
    candidate_solutions.extend(
        _evaluate_combined_perturbation_candidates(
            problem,
            candidate_specs=combined_candidates,
            timelimit=0.25,
        )
    )
    best_sol, _ = _select_best_official_candidate(problem, candidate_solutions)
    assert best_sol is not None
    rebuild_candidates = _build_objective_rebuild_candidates(problem, best_sol, best_order)
    candidate_solutions.extend(
        _evaluate_combined_perturbation_candidates(
            problem,
            candidate_specs=rebuild_candidates,
            timelimit=0.15,
        )
    )
    best_sol, _ = _select_best_official_candidate(problem, candidate_solutions)
    assert best_sol is not None

    contiguous_reinsertion_candidates = _build_objective_reinsertion_candidates(
        problem,
        best_sol,
        best_order,
        explore_staggered_variants=False,
    )
    contiguous_reinsertion_solutions = candidate_solutions + _evaluate_combined_perturbation_candidates(
        problem,
        candidate_specs=contiguous_reinsertion_candidates,
        timelimit=0.1,
    )
    _, contiguous_reinsertion_result = _select_best_official_candidate(problem, contiguous_reinsertion_solutions)
    search_result = validate_official_solution(problem, solve_official_search(problem, timelimit=1.0))

    assert contiguous_reinsertion_result is not None
    assert contiguous_reinsertion_result["feasible"] is True
    assert float(contiguous_reinsertion_result["objective"]) == pytest.approx(25.1)
    assert search_result["feasible"] is True
    assert float(search_result["objective"]) == pytest.approx(20.4)
    assert float(search_result["objective"]) < float(contiguous_reinsertion_result["objective"])


def test_official_search_partial_reconstruction_beats_pre_partial_search() -> None:
    problem = {
        "name": "partial-reconstruction-search",
        "bays": [
            {"width": 5, "height": 6},
            {"width": 5, "height": 6},
            {"width": 5, "height": 4},
        ],
        "blocks": [
            {
                "release_time": 3,
                "due_date": 5,
                "processing_time": 2,
                "workload": 3,
                "bay_preferences": [9, 9, 2],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [4, 0], [4, 5], [0, 5]]
                        ],
                    }
                ],
            },
            {
                "release_time": 1,
                "due_date": 8,
                "processing_time": 4,
                "workload": 6,
                "bay_preferences": [8, 3, 7],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [3, 0], [3, 3], [0, 3]]
                        ],
                    }
                ],
            },
            {
                "release_time": 1,
                "due_date": 8,
                "processing_time": 6,
                "workload": 7,
                "bay_preferences": [0, 10, 4],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [3, 0], [3, 3], [0, 3]]
                        ],
                    }
                ],
            },
            {
                "release_time": 2,
                "due_date": 9,
                "processing_time": 4,
                "workload": 5,
                "bay_preferences": [3, 9, 4],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [3, 0], [3, 6], [0, 6]]
                        ],
                    }
                ],
            },
            {
                "release_time": 2,
                "due_date": 10,
                "processing_time": 2,
                "workload": 8,
                "bay_preferences": [8, 1, 9],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [2, 0], [2, 5], [0, 5]]
                        ],
                    }
                ],
            },
        ],
        "weights": {"w1": 10, "w2": 3, "w3": 1},
    }

    initial_orders = _build_official_search_orders(problem)
    initial_solutions, best_order = _evaluate_native_order_candidates(problem, initial_orders, timelimit=0.45)
    assert best_order is not None
    neighbor_solutions, _ = _evaluate_native_order_candidates(
        problem,
        _build_order_neighbors(best_order),
        timelimit=0.25,
    )
    candidate_solutions = initial_solutions + neighbor_solutions
    best_sol, _ = _select_best_official_candidate(problem, candidate_solutions)
    assert best_sol is not None
    bias_candidates = _build_bay_bias_candidates(problem, best_sol)
    candidate_solutions.extend(
        _evaluate_bay_bias_candidates(
            problem,
            block_order=best_order,
            candidate_biases=bias_candidates,
            timelimit=0.2,
        )
    )
    best_sol, _ = _select_best_official_candidate(problem, candidate_solutions)
    assert best_sol is not None
    combined_candidates = _build_combined_perturbation_candidates(problem, best_sol, best_order)
    candidate_solutions.extend(
        _evaluate_combined_perturbation_candidates(
            problem,
            candidate_specs=combined_candidates,
            timelimit=0.25,
        )
    )
    best_sol, _ = _select_best_official_candidate(problem, candidate_solutions)
    assert best_sol is not None
    rebuild_candidates = _build_objective_rebuild_candidates(problem, best_sol, best_order)
    candidate_solutions.extend(
        _evaluate_combined_perturbation_candidates(
            problem,
            candidate_specs=rebuild_candidates,
            timelimit=0.15,
        )
    )
    best_sol, _ = _select_best_official_candidate(problem, candidate_solutions)
    assert best_sol is not None
    reinsertion_candidates = _build_objective_reinsertion_candidates(problem, best_sol, best_order)
    pre_partial_solutions = candidate_solutions + _evaluate_combined_perturbation_candidates(
        problem,
        candidate_specs=reinsertion_candidates,
        timelimit=0.1,
    )
    pre_partial_solution, pre_partial_result = _select_best_official_candidate(problem, pre_partial_solutions)
    assert pre_partial_solution is not None

    partial_reconstruction_candidates = _build_objective_partial_reconstruction_candidates(
        problem,
        pre_partial_solution,
        best_order,
    )
    partial_reconstruction_solutions = pre_partial_solutions + _evaluate_partial_reconstruction_candidates(
        problem,
        candidate_specs=partial_reconstruction_candidates,
        timelimit=0.08,
    )
    _, partial_reconstruction_result = _select_best_official_candidate(problem, partial_reconstruction_solutions)
    search_result = validate_official_solution(problem, solve_official_search(problem, timelimit=1.0))

    assert pre_partial_result is not None
    assert pre_partial_result["feasible"] is True
    assert float(pre_partial_result["objective"]) == pytest.approx(23.0)
    assert partial_reconstruction_result is not None
    assert partial_reconstruction_result["feasible"] is True
    assert float(partial_reconstruction_result["objective"]) == pytest.approx(21.333333333333336)
    assert search_result["feasible"] is True
    assert float(search_result["objective"]) == pytest.approx(21.333333333333336)
    assert float(partial_reconstruction_result["objective"]) < float(pre_partial_result["objective"])


def test_partial_reconstruction_diagnostics_reports_pool_and_cap() -> None:
    problem = {
        "name": "partial-reconstruction-diagnostics",
        "bays": [
            {"width": 5, "height": 6},
            {"width": 5, "height": 6},
            {"width": 5, "height": 4},
        ],
        "blocks": [
            {
                "release_time": 3,
                "due_date": 5,
                "processing_time": 2,
                "workload": 3,
                "bay_preferences": [9, 9, 2],
                "shape": [{"orientation": 0, "layers": [[[0, 0], [4, 0], [4, 5], [0, 5]]]}],
            },
            {
                "release_time": 1,
                "due_date": 8,
                "processing_time": 4,
                "workload": 6,
                "bay_preferences": [8, 3, 7],
                "shape": [{"orientation": 0, "layers": [[[0, 0], [3, 0], [3, 3], [0, 3]]]}],
            },
            {
                "release_time": 1,
                "due_date": 8,
                "processing_time": 6,
                "workload": 7,
                "bay_preferences": [0, 10, 4],
                "shape": [{"orientation": 0, "layers": [[[0, 0], [3, 0], [3, 3], [0, 3]]]}],
            },
            {
                "release_time": 2,
                "due_date": 9,
                "processing_time": 4,
                "workload": 5,
                "bay_preferences": [3, 9, 4],
                "shape": [{"orientation": 0, "layers": [[[0, 0], [3, 0], [3, 6], [0, 6]]]}],
            },
            {
                "release_time": 2,
                "due_date": 10,
                "processing_time": 2,
                "workload": 8,
                "bay_preferences": [8, 1, 9],
                "shape": [{"orientation": 0, "layers": [[[0, 0], [2, 0], [2, 5], [0, 5]]]}],
            },
        ],
        "weights": {"w1": 10, "w2": 3, "w3": 1},
    }

    initial_orders = _build_official_search_orders(problem)
    initial_solutions, best_order = _evaluate_native_order_candidates(problem, initial_orders, timelimit=0.45)
    assert best_order is not None
    neighbor_solutions, _ = _evaluate_native_order_candidates(problem, _build_order_neighbors(best_order), timelimit=0.25)
    candidate_solutions = initial_solutions + neighbor_solutions
    best_sol, _ = _select_best_official_candidate(problem, candidate_solutions)
    assert best_sol is not None
    bias_candidates = _build_bay_bias_candidates(problem, best_sol)
    candidate_solutions.extend(
        _evaluate_bay_bias_candidates(problem, block_order=best_order, candidate_biases=bias_candidates, timelimit=0.2)
    )
    best_sol, _ = _select_best_official_candidate(problem, candidate_solutions)
    assert best_sol is not None
    combined_candidates = _build_combined_perturbation_candidates(problem, best_sol, best_order)
    candidate_solutions.extend(
        _evaluate_combined_perturbation_candidates(problem, candidate_specs=combined_candidates, timelimit=0.25)
    )
    best_sol, _ = _select_best_official_candidate(problem, candidate_solutions)
    assert best_sol is not None
    rebuild_candidates = _build_objective_rebuild_candidates(problem, best_sol, best_order)
    candidate_solutions.extend(
        _evaluate_combined_perturbation_candidates(problem, candidate_specs=rebuild_candidates, timelimit=0.15)
    )
    best_sol, _ = _select_best_official_candidate(problem, candidate_solutions)
    assert best_sol is not None
    reinsertion_candidates = _build_objective_reinsertion_candidates(problem, best_sol, best_order)
    pre_partial_solutions = candidate_solutions + _evaluate_combined_perturbation_candidates(
        problem,
        candidate_specs=reinsertion_candidates,
        timelimit=0.1,
    )
    pre_partial_solution, _ = _select_best_official_candidate(problem, pre_partial_solutions)
    assert pre_partial_solution is not None

    fixed_diagnostics = _build_objective_partial_reconstruction_diagnostics(
        problem,
        pre_partial_solution,
        best_order,
        max_candidates=12,
        adaptive_max_candidates=False,
    )
    adaptive_diagnostics = _build_objective_partial_reconstruction_diagnostics(
        problem,
        pre_partial_solution,
        best_order,
        max_candidates=12,
        adaptive_max_candidates=True,
    )

    assert fixed_diagnostics["pool_size"] >= 1
    assert fixed_diagnostics["kept_count"] == len(fixed_diagnostics["candidate_specs"])
    assert fixed_diagnostics["selected_cap"] == min(12, fixed_diagnostics["pool_size"])
    assert adaptive_diagnostics["pool_size"] == fixed_diagnostics["pool_size"]
    assert adaptive_diagnostics["kept_count"] == len(adaptive_diagnostics["candidate_specs"])
    assert 0 < adaptive_diagnostics["selected_cap"] <= adaptive_diagnostics["pool_size"]
    assert len(adaptive_diagnostics["top_scores"]) <= 5


def test_official_search_adaptive_partial_reconstruction_cap_shrinks_candidate_slice() -> None:
    problem = {
        "name": "adaptive-partial-reconstruction-cap-search",
        "bays": [
            {"width": 5, "height": 6},
            {"width": 5, "height": 6},
            {"width": 5, "height": 4},
        ],
        "blocks": [
            {
                "release_time": 3,
                "due_date": 5,
                "processing_time": 2,
                "workload": 3,
                "bay_preferences": [9, 9, 2],
                "shape": [{"orientation": 0, "layers": [[[0, 0], [4, 0], [4, 5], [0, 5]]]}],
            },
            {
                "release_time": 1,
                "due_date": 8,
                "processing_time": 4,
                "workload": 6,
                "bay_preferences": [8, 3, 7],
                "shape": [{"orientation": 0, "layers": [[[0, 0], [3, 0], [3, 3], [0, 3]]]}],
            },
            {
                "release_time": 1,
                "due_date": 8,
                "processing_time": 6,
                "workload": 7,
                "bay_preferences": [0, 10, 4],
                "shape": [{"orientation": 0, "layers": [[[0, 0], [3, 0], [3, 3], [0, 3]]]}],
            },
            {
                "release_time": 2,
                "due_date": 9,
                "processing_time": 4,
                "workload": 5,
                "bay_preferences": [3, 9, 4],
                "shape": [{"orientation": 0, "layers": [[[0, 0], [3, 0], [3, 6], [0, 6]]]}],
            },
            {
                "release_time": 2,
                "due_date": 10,
                "processing_time": 2,
                "workload": 8,
                "bay_preferences": [8, 1, 9],
                "shape": [{"orientation": 0, "layers": [[[0, 0], [2, 0], [2, 5], [0, 5]]]}],
            },
        ],
        "weights": {"w1": 10, "w2": 3, "w3": 1},
    }

    initial_orders = _build_official_search_orders(problem)
    initial_solutions, best_order = _evaluate_native_order_candidates(problem, initial_orders, timelimit=0.45)
    assert best_order is not None
    neighbor_solutions, _ = _evaluate_native_order_candidates(
        problem,
        _build_order_neighbors(best_order),
        timelimit=0.25,
    )
    candidate_solutions = initial_solutions + neighbor_solutions
    best_sol, _ = _select_best_official_candidate(problem, candidate_solutions)
    assert best_sol is not None
    bias_candidates = _build_bay_bias_candidates(problem, best_sol)
    candidate_solutions.extend(
        _evaluate_bay_bias_candidates(
            problem,
            block_order=best_order,
            candidate_biases=bias_candidates,
            timelimit=0.2,
        )
    )
    best_sol, _ = _select_best_official_candidate(problem, candidate_solutions)
    assert best_sol is not None
    combined_candidates = _build_combined_perturbation_candidates(problem, best_sol, best_order)
    candidate_solutions.extend(
        _evaluate_combined_perturbation_candidates(
            problem,
            candidate_specs=combined_candidates,
            timelimit=0.25,
        )
    )
    best_sol, _ = _select_best_official_candidate(problem, candidate_solutions)
    assert best_sol is not None
    rebuild_candidates = _build_objective_rebuild_candidates(problem, best_sol, best_order)
    candidate_solutions.extend(
        _evaluate_combined_perturbation_candidates(
            problem,
            candidate_specs=rebuild_candidates,
            timelimit=0.15,
        )
    )
    best_sol, _ = _select_best_official_candidate(problem, candidate_solutions)
    assert best_sol is not None
    reinsertion_candidates = _build_objective_reinsertion_candidates(problem, best_sol, best_order)
    pre_partial_solutions = candidate_solutions + _evaluate_combined_perturbation_candidates(
        problem,
        candidate_specs=reinsertion_candidates,
        timelimit=0.1,
    )
    pre_partial_solution, _ = _select_best_official_candidate(problem, pre_partial_solutions)
    assert pre_partial_solution is not None

    fixed_diagnostics = _build_objective_partial_reconstruction_diagnostics(
        problem,
        pre_partial_solution,
        best_order,
        max_candidates=12,
        adaptive_max_candidates=False,
    )
    adaptive_diagnostics = _build_objective_partial_reconstruction_diagnostics(
        problem,
        pre_partial_solution,
        best_order,
        max_candidates=12,
        adaptive_max_candidates=True,
    )
    assert fixed_diagnostics["pool_size"] == adaptive_diagnostics["pool_size"]
    assert fixed_diagnostics["pool_size"] >= fixed_diagnostics["selected_cap"]
    assert fixed_diagnostics["selected_cap"] == 12
    assert adaptive_diagnostics["selected_cap"] == 8
    assert len(fixed_diagnostics["candidate_specs"]) == 12
    assert len(adaptive_diagnostics["candidate_specs"]) == 8


def test_adaptive_partial_reconstruction_cap_keeps_flat_top_plateau() -> None:
    problem = {
        "name": "adaptive-cap-flat-top-plateau",
        "bays": [
            {"width": 7, "height": 4},
            {"width": 7, "height": 7},
            {"width": 5, "height": 4},
            {"width": 5, "height": 5},
        ],
        "blocks": [
            {"release_time": 4, "due_date": 13, "processing_time": 5, "workload": 7, "bay_preferences": [3, 9, 9, 9], "shape": [{"orientation": 0, "layers": [[[0, 0], [5, 0], [5, 3], [0, 3]]]}]},
            {"release_time": 3, "due_date": 9, "processing_time": 6, "workload": 6, "bay_preferences": [7, 6, 4, 8], "shape": [{"orientation": 0, "layers": [[[0, 0], [6, 0], [6, 6], [0, 6]]]}]},
            {"release_time": 1, "due_date": 9, "processing_time": 4, "workload": 7, "bay_preferences": [5, 8, 9, 0], "shape": [{"orientation": 0, "layers": [[[0, 0], [5, 0], [5, 3], [0, 3]]]}]},
            {"release_time": 3, "due_date": 5, "processing_time": 2, "workload": 4, "bay_preferences": [5, 7, 4, 8], "shape": [{"orientation": 0, "layers": [[[0, 0], [3, 0], [3, 2], [0, 2]]]}]},
            {"release_time": 6, "due_date": 14, "processing_time": 5, "workload": 8, "bay_preferences": [10, 6, 10, 10], "shape": [{"orientation": 0, "layers": [[[0, 0], [6, 0], [6, 5], [0, 5]]]}]},
            {"release_time": 6, "due_date": 8, "processing_time": 2, "workload": 7, "bay_preferences": [2, 9, 10, 9], "shape": [{"orientation": 0, "layers": [[[0, 0], [5, 0], [5, 6], [0, 6]]]}]},
            {"release_time": 6, "due_date": 12, "processing_time": 6, "workload": 1, "bay_preferences": [10, 2, 8, 9], "shape": [{"orientation": 0, "layers": [[[0, 0], [5, 0], [5, 5], [0, 5]]]}]},
        ],
        "weights": {"w1": 10, "w2": 3, "w3": 1},
    }

    initial_orders = _build_official_search_orders(problem)
    initial_solutions, best_order = _evaluate_native_order_candidates(problem, initial_orders, timelimit=0.16)
    assert best_order is not None
    neighbor_solutions, _ = _evaluate_native_order_candidates(
        problem,
        _build_order_neighbors(best_order),
        timelimit=0.09,
    )
    candidate_solutions = initial_solutions + neighbor_solutions
    best_sol, _ = _select_best_official_candidate(problem, candidate_solutions)
    assert best_sol is not None
    bias_candidates = _build_bay_bias_candidates(problem, best_sol)
    candidate_solutions.extend(
        _evaluate_bay_bias_candidates(
            problem,
            block_order=best_order,
            candidate_biases=bias_candidates,
            timelimit=0.07,
        )
    )
    best_sol, _ = _select_best_official_candidate(problem, candidate_solutions)
    assert best_sol is not None
    combined_candidates = _build_combined_perturbation_candidates(problem, best_sol, best_order)
    candidate_solutions.extend(
        _evaluate_combined_perturbation_candidates(
            problem,
            candidate_specs=combined_candidates,
            timelimit=0.08,
        )
    )
    best_sol, _ = _select_best_official_candidate(problem, candidate_solutions)
    assert best_sol is not None
    rebuild_candidates = _build_objective_rebuild_candidates(problem, best_sol, best_order)
    candidate_solutions.extend(
        _evaluate_combined_perturbation_candidates(
            problem,
            candidate_specs=rebuild_candidates,
            timelimit=0.05,
        )
    )
    best_sol, _ = _select_best_official_candidate(problem, candidate_solutions)
    assert best_sol is not None
    reinsertion_candidates = _build_objective_reinsertion_candidates(problem, best_sol, best_order)
    pre_partial_solutions = candidate_solutions + _evaluate_combined_perturbation_candidates(
        problem,
        candidate_specs=reinsertion_candidates,
        timelimit=0.05,
    )
    pre_partial_solution, _ = _select_best_official_candidate(problem, pre_partial_solutions)
    assert pre_partial_solution is not None

    fixed_diagnostics = _build_objective_partial_reconstruction_diagnostics(
        problem,
        pre_partial_solution,
        best_order,
        max_candidates=12,
        adaptive_max_candidates=False,
    )
    adaptive_diagnostics = _build_objective_partial_reconstruction_diagnostics(
        problem,
        pre_partial_solution,
        best_order,
        max_candidates=12,
        adaptive_max_candidates=True,
    )

    assert fixed_diagnostics["selected_cap"] == 12
    assert adaptive_diagnostics["selected_cap"] == 12
    assert adaptive_diagnostics["top_scores"][0] == pytest.approx(adaptive_diagnostics["top_scores"][4])


def test_official_search_clustered_partial_reconstruction_beats_top_only_focus() -> None:
    problem = {
        "name": "clustered-partial-reconstruction-search",
        "bays": [
            {"width": 4, "height": 6},
            {"width": 6, "height": 4},
            {"width": 4, "height": 6},
        ],
        "blocks": [
            {
                "release_time": 4,
                "due_date": 10,
                "processing_time": 6,
                "workload": 7,
                "bay_preferences": [6, 6, 7],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [2, 0], [2, 3], [0, 3]]
                        ],
                    }
                ],
            },
            {
                "release_time": 2,
                "due_date": 6,
                "processing_time": 2,
                "workload": 7,
                "bay_preferences": [10, 9, 7],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [2, 0], [2, 2], [0, 2]]
                        ],
                    }
                ],
            },
            {
                "release_time": 4,
                "due_date": 12,
                "processing_time": 2,
                "workload": 7,
                "bay_preferences": [6, 1, 9],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [3, 0], [3, 3], [0, 3]]
                        ],
                    }
                ],
            },
            {
                "release_time": 4,
                "due_date": 11,
                "processing_time": 6,
                "workload": 7,
                "bay_preferences": [3, 3, 5],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [2, 0], [2, 5], [0, 5]]
                        ],
                    }
                ],
            },
            {
                "release_time": 4,
                "due_date": 10,
                "processing_time": 6,
                "workload": 4,
                "bay_preferences": [3, 0, 6],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [4, 0], [4, 4], [0, 4]]
                        ],
                    }
                ],
            },
        ],
        "weights": {"w1": 10, "w2": 3, "w3": 1},
    }

    initial_orders = _build_official_search_orders(problem)
    initial_solutions, best_order = _evaluate_native_order_candidates(problem, initial_orders, timelimit=0.45)
    assert best_order is not None
    neighbor_solutions, _ = _evaluate_native_order_candidates(
        problem,
        _build_order_neighbors(best_order),
        timelimit=0.25,
    )
    candidate_solutions = initial_solutions + neighbor_solutions
    best_sol, _ = _select_best_official_candidate(problem, candidate_solutions)
    assert best_sol is not None
    bias_candidates = _build_bay_bias_candidates(problem, best_sol)
    candidate_solutions.extend(
        _evaluate_bay_bias_candidates(
            problem,
            block_order=best_order,
            candidate_biases=bias_candidates,
            timelimit=0.2,
        )
    )
    best_sol, _ = _select_best_official_candidate(problem, candidate_solutions)
    assert best_sol is not None
    combined_candidates = _build_combined_perturbation_candidates(problem, best_sol, best_order)
    candidate_solutions.extend(
        _evaluate_combined_perturbation_candidates(
            problem,
            candidate_specs=combined_candidates,
            timelimit=0.25,
        )
    )
    best_sol, _ = _select_best_official_candidate(problem, candidate_solutions)
    assert best_sol is not None
    rebuild_candidates = _build_objective_rebuild_candidates(problem, best_sol, best_order)
    candidate_solutions.extend(
        _evaluate_combined_perturbation_candidates(
            problem,
            candidate_specs=rebuild_candidates,
            timelimit=0.15,
        )
    )
    best_sol, _ = _select_best_official_candidate(problem, candidate_solutions)
    assert best_sol is not None
    reinsertion_candidates = _build_objective_reinsertion_candidates(problem, best_sol, best_order)
    pre_partial_solutions = candidate_solutions + _evaluate_combined_perturbation_candidates(
        problem,
        candidate_specs=reinsertion_candidates,
        timelimit=0.1,
    )
    pre_partial_solution, _ = _select_best_official_candidate(problem, pre_partial_solutions)
    assert pre_partial_solution is not None

    top_only_candidates = _build_objective_partial_reconstruction_candidates(
        problem,
        pre_partial_solution,
        best_order,
        use_overlap_clusters=False,
        use_bay_neighborhoods=False,
    )
    top_only_solutions = pre_partial_solutions + _evaluate_partial_reconstruction_candidates(
        problem,
        candidate_specs=top_only_candidates,
        timelimit=0.08,
    )
    _, top_only_result = _select_best_official_candidate(problem, top_only_solutions)

    clustered_candidates = _build_objective_partial_reconstruction_candidates(
        problem,
        pre_partial_solution,
        best_order,
        use_overlap_clusters=True,
        use_bay_neighborhoods=False,
    )
    clustered_solutions = pre_partial_solutions + _evaluate_partial_reconstruction_candidates(
        problem,
        candidate_specs=clustered_candidates,
        timelimit=0.08,
    )
    _, clustered_result = _select_best_official_candidate(problem, clustered_solutions)
    search_result = validate_official_solution(problem, solve_official_search(problem, timelimit=1.0))

    assert top_only_result is not None
    assert top_only_result["feasible"] is True
    assert float(top_only_result["objective"]) == pytest.approx(25.0)
    assert clustered_result is not None
    assert clustered_result["feasible"] is True
    assert float(clustered_result["objective"]) == pytest.approx(24.0)
    assert search_result["feasible"] is True
    assert float(search_result["objective"]) == pytest.approx(24.0)
    assert float(clustered_result["objective"]) < float(top_only_result["objective"])


def test_official_constructive_comparison_summary_contains_runtime(tmp_path) -> None:
    output_root = tmp_path / "artifacts" / "official" / "comparison"
    summary = generate_official_constructive_comparison(REPO_ROOT, output_root=output_root)

    assert summary["instance"] == "official-sample-instance"
    delegated = summary["delegated_baseline"]
    native = summary["native_constructive"]
    assert delegated["feasible"] is True
    assert native["feasible"] is True
    assert delegated["stage"] == 5
    assert native["stage"] == 5
    assert delegated["assignment_count"] == 2
    assert native["assignment_count"] == 2
    assert delegated["runtime_seconds"] >= 0.0
    assert native["runtime_seconds"] >= 0.0
    assert (output_root / "summary.json").exists()


def test_official_constructive_comparison_accepts_explicit_instance_path(tmp_path) -> None:
    output_root = tmp_path / "artifacts" / "official" / "comparison"
    summary = generate_official_constructive_comparison(
        REPO_ROOT,
        output_root=output_root,
        instance_path=REPO_ROOT / "examples" / "official-sample-instance.json",
        timelimit=5.0,
    )

    assert summary["instance"] == "official-sample-instance"
    assert summary["delegated_baseline"]["feasible"] is True
    assert summary["native_constructive"]["feasible"] is True


def test_official_constructive_native_preserves_exclusive_large_bay_capacity() -> None:
    problem = {
        "name": "native-capacity-preservation",
        "bays": [
            {"width": 6, "height": 6},
            {"width": 4, "height": 6},
        ],
        "blocks": [
            {
                "release_time": 0,
                "due_date": 3,
                "processing_time": 3,
                "workload": 1,
                "bay_preferences": [10, 9],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [4, 0], [4, 4], [0, 4]]
                        ],
                    }
                ],
            },
            {
                "release_time": 0,
                "due_date": 4,
                "processing_time": 4,
                "workload": 1,
                "bay_preferences": [10, 0],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [6, 0], [6, 4], [0, 4]]
                        ],
                    }
                ],
            },
        ],
        "weights": {"w1": 10, "w2": 3, "w3": 1},
    }

    solution = solve_official_constructive_native(problem, timelimit=5.0)
    result = validate_official_solution(problem, solution)
    entry_ops = [
        operation
        for operations in solution["operations"].values()
        for operation in operations
        if operation["type"] == "ENTRY"
    ]
    block_zero_entry = next(operation for operation in entry_ops if operation["block_id"] == 0)

    assert result["feasible"] is True
    assert result["stage"] == 5
    assert result["obj1"] == 0.0
    assert block_zero_entry["bay_id"] == 1


def test_official_constructive_native_accounts_for_future_bay_scarcity() -> None:
    problem = {
        "name": "native-future-bay-scarcity",
        "bays": [
            {"width": 6, "height": 6},
            {"width": 5, "height": 6},
            {"width": 4, "height": 6},
        ],
        "blocks": [
            {
                "release_time": 0,
                "due_date": 2,
                "processing_time": 2,
                "workload": 1,
                "bay_preferences": [10, 0, 9],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [4, 0], [4, 4], [0, 4]]
                        ],
                    }
                ],
            },
            {
                "release_time": 0,
                "due_date": 4,
                "processing_time": 4,
                "workload": 1,
                "bay_preferences": [10, 9, 0],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [5, 0], [5, 4], [0, 4]]
                        ],
                    }
                ],
            },
            {
                "release_time": 0,
                "due_date": 4,
                "processing_time": 4,
                "workload": 1,
                "bay_preferences": [9, 10, 0],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [5, 0], [5, 4], [0, 4]]
                        ],
                    }
                ],
            },
        ],
        "weights": {"w1": 10, "w2": 3, "w3": 1},
    }

    solution = solve_official_constructive_native(problem, timelimit=5.0)
    result = validate_official_solution(problem, solution)
    entry_ops = [
        operation
        for operations in solution["operations"].values()
        for operation in operations
        if operation["type"] == "ENTRY"
    ]
    block_zero_entry = next(operation for operation in entry_ops if operation["block_id"] == 0)

    assert result["feasible"] is True
    assert result["stage"] == 5
    assert result["obj1"] == 0.0
    assert block_zero_entry["bay_id"] == 2


def test_official_constructive_native_weights_future_bay_scarcity_by_urgency() -> None:
    problem = {
        "name": "native-urgency-weighted-bay-scarcity",
        "bays": [
            {"width": 6, "height": 6},
            {"width": 5, "height": 3},
            {"width": 4, "height": 4},
        ],
        "blocks": [
            {
                "release_time": 0,
                "due_date": 2,
                "processing_time": 2,
                "workload": 1,
                "bay_preferences": [0, 10, 9],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [4, 0], [4, 3], [0, 3]]
                        ],
                    }
                ],
            },
            {
                "release_time": 0,
                "due_date": 3,
                "processing_time": 3,
                "workload": 1,
                "bay_preferences": [10, 0, 0],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [6, 0], [6, 4], [0, 4]]
                        ],
                    }
                ],
            },
            {
                "release_time": 0,
                "due_date": 4,
                "processing_time": 4,
                "workload": 1,
                "bay_preferences": [10, 9, 0],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [5, 0], [5, 3], [0, 3]]
                        ],
                    }
                ],
            },
            {
                "release_time": 0,
                "due_date": 20,
                "processing_time": 4,
                "workload": 1,
                "bay_preferences": [9, 0, 10],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [4, 0], [4, 4], [0, 4]]
                        ],
                    }
                ],
            },
        ],
        "weights": {"w1": 10, "w2": 3, "w3": 1},
    }

    solution = solve_official_constructive_native(problem, timelimit=5.0)
    result = validate_official_solution(problem, solution)
    entry_ops = [
        operation
        for operations in solution["operations"].values()
        for operation in operations
        if operation["type"] == "ENTRY"
    ]
    block_zero_entry = next(operation for operation in entry_ops if operation["block_id"] == 0)

    assert result["feasible"] is True
    assert result["stage"] == 5
    assert result["obj1"] == 0.0
    assert block_zero_entry["bay_id"] == 2


def test_official_constructive_native_accounts_for_future_schedule_pressure() -> None:
    problem = {
        "name": "native-future-schedule-pressure",
        "bays": [
            {"width": 6, "height": 6},
            {"width": 6, "height": 6},
            {"width": 4, "height": 6},
        ],
        "blocks": [
            {
                "release_time": 0,
                "due_date": 4,
                "processing_time": 4,
                "workload": 1,
                "bay_preferences": [10, 9, 0],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [4, 0], [4, 4], [0, 4]]
                        ],
                    }
                ],
            },
            {
                "release_time": 0,
                "due_date": 4,
                "processing_time": 4,
                "workload": 1,
                "bay_preferences": [10, 0, 0],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [6, 0], [6, 4], [0, 4]]
                        ],
                    }
                ],
            },
            {
                "release_time": 0,
                "due_date": 9,
                "processing_time": 4,
                "workload": 1,
                "bay_preferences": [9, 10, 0],
                "shape": [
                    {
                        "orientation": 0,
                        "layers": [
                            [[0, 0], [6, 0], [6, 4], [0, 4]]
                        ],
                    }
                ],
            },
        ],
        "weights": {"w1": 10, "w2": 3, "w3": 1},
    }

    solution = solve_official_constructive_native(problem, timelimit=5.0)
    result = validate_official_solution(problem, solution)
    entry_ops = [
        operation
        for operations in solution["operations"].values()
        for operation in operations
        if operation["type"] == "ENTRY"
    ]
    block_zero_entry = next(operation for operation in entry_ops if operation["block_id"] == 0)

    assert result["feasible"] is True
    assert result["stage"] == 5
    assert result["obj1"] == 0.0
    assert block_zero_entry["bay_id"] == 2


@pytest.mark.parametrize(
    ("solution_path", "expected_stage", "expected_snippet"),
    [
        ("examples/official-invalid-stage1-solution.json", 1, "block 1 has no EXIT operation"),
        ("examples/official-invalid-stage2-solution.json", 2, "exceeds bay boundary"),
        (
            "examples/official-invalid-stage5-solution.json",
            5,
            "EXIT block 0 listed after an ENTRY operation",
        ),
    ],
)
def test_validate_official_invalid_solutions_report_expected_stage(
    solution_path: str,
    expected_stage: int,
    expected_snippet: str,
) -> None:
    instance = load_instance(Path("examples/official-sample-instance.json"), input_format="official")
    solution = load_official_solution(Path(solution_path))

    result = validate_official_solution(instance.metadata["raw_problem"], solution)

    assert result["feasible"] is False
    assert result["stage"] == expected_stage
    assert any(expected_snippet in violation for violation in result["violations"])


def test_validate_official_stage3_solution_reports_expected_exit_obstruction() -> None:
    instance = load_instance(Path("examples/official-stage3-instance.json"), input_format="official")
    solution = load_official_solution(Path("examples/official-invalid-stage3-solution.json"))

    result = validate_official_solution(instance.metadata["raw_problem"], solution)

    assert result["feasible"] is False
    assert result["stage"] == 3
    assert any("exit obstructed by block 1" in violation for violation in result["violations"])
    assert any("kind=sweep" in violation for violation in result["violations"])


def test_constructive_solution_is_feasible() -> None:
    instance = load_instance(Path("examples/sample-instance.json"))
    checker = FeasibilityChecker(instance)
    state = ConstructiveSolver(checker=checker).solve(instance)

    is_feasible, violations = checker.validate_solution(state.placements)

    assert is_feasible
    assert violations == []


def test_overlap_is_detected() -> None:
    instance = load_instance(Path("examples/sample-instance.json"))
    checker = FeasibilityChecker(instance)
    placements = [
        Placement(block_id="B1", x=0, y=0, start_time=0, end_time=5),
        Placement(block_id="B2", x=2, y=1, start_time=1, end_time=4),
    ]

    is_feasible, violations = checker.validate_solution(placements)

    assert not is_feasible
    assert any("overlaps block B1" in violation or "overlaps block B2" in violation for violation in violations)


def test_minimum_clearance_is_detected() -> None:
    instance = load_instance(Path("examples/sample-instance.json"))
    checker = FeasibilityChecker(instance)
    placements = [
        Placement(block_id="B1", x=0, y=0, start_time=0, end_time=5),
        Placement(block_id="B2", x=4, y=0, start_time=1, end_time=4),
    ]

    is_feasible, violations = checker.validate_solution(placements)

    assert not is_feasible
    assert any("minimum clearance" in violation for violation in violations)


def test_scoring_prefers_less_congested_candidate() -> None:
    instance = load_instance(Path("examples/sample-instance.json"))
    placements = [Placement(block_id="B1", x=0, y=0, start_time=0, end_time=5)]

    congested = Placement(block_id="B2", x=4, y=0, start_time=1, end_time=6)
    separated = Placement(block_id="B2", x=8, y=4, start_time=1, end_time=6)

    congested_score = score_placement_candidate(instance, placements, congested)
    separated_score = score_placement_candidate(instance, placements, separated)

    assert separated_score > congested_score
