from pathlib import Path

from yardmind.loader import load_instance
from yardmind.models import Block, Instance, Yard
from yardmind.solver.constructive import ConstructiveSolver
from yardmind.solver.feasibility import FeasibilityChecker
from yardmind.solver.local_search import (
    BestOfTopRepairOperator,
    BoundedExactRepairOperator,
    CongestionClusterDestroyOperator,
    DestroyResult,
    GreedyRepairOperator,
    GlobalRestartDestroyOperator,
    HighRiskClusterDestroyOperator,
    LocalSearchSolver,
    SpreadRepairOperator,
    state_priority_tuple,
)
from yardmind.solver.state import ObjectiveBreakdown, SolutionState


def test_destroy_operator_removes_a_cluster() -> None:
    instance = load_instance(Path("examples/sample-instance.json"))
    checker = FeasibilityChecker(instance)
    state = ConstructiveSolver(checker=checker).solve(instance)

    destroyed = HighRiskClusterDestroyOperator(cluster_size=2).destroy(state)

    assert len(destroyed.removed_block_ids) == 2
    assert len(destroyed.remaining_placements) == len(state.placements) - 2
    assert len(set(destroyed.removed_block_ids)) == 2


def test_global_restart_destroy_operator_removes_all_blocks() -> None:
    instance = load_instance(Path("examples/sample-instance.json"))
    checker = FeasibilityChecker(instance)
    state = ConstructiveSolver(checker=checker).solve(instance)

    destroyed = GlobalRestartDestroyOperator().destroy(state)

    assert sorted(destroyed.removed_block_ids) == sorted(block.block_id for block in instance.blocks)
    assert destroyed.remaining_placements == []


def test_repair_operator_restores_a_feasible_solution() -> None:
    instance = load_instance(Path("examples/sample-instance.json"))
    checker = FeasibilityChecker(instance)
    state = ConstructiveSolver(checker=checker).solve(instance)
    destroyed = HighRiskClusterDestroyOperator(cluster_size=2).destroy(state)

    repaired = GreedyRepairOperator(checker=checker).repair(
        instance,
        destroyed.remaining_placements,
        destroyed.removed_block_ids,
    )
    is_feasible, violations = checker.validate_solution(repaired.placements)

    assert is_feasible
    assert violations == []
    assert len(repaired.placements) == len(instance.blocks)


def test_spread_repair_operator_restores_a_feasible_solution() -> None:
    instance = load_instance(Path("examples/sample-instance.json"))
    checker = FeasibilityChecker(instance)
    state = ConstructiveSolver(checker=checker).solve(instance)
    destroyed = HighRiskClusterDestroyOperator(cluster_size=2).destroy(state)

    repaired = SpreadRepairOperator(checker=checker).repair(
        instance,
        destroyed.remaining_placements,
        destroyed.removed_block_ids,
    )
    is_feasible, violations = checker.validate_solution(repaired.placements)

    assert is_feasible
    assert violations == []
    assert len(repaired.placements) == len(instance.blocks)


def test_best_of_top_repair_operator_restores_a_feasible_solution() -> None:
    instance = load_instance(Path("examples/sample-instance.json"))
    checker = FeasibilityChecker(instance)
    state = ConstructiveSolver(checker=checker).solve(instance)
    destroyed = HighRiskClusterDestroyOperator(cluster_size=2).destroy(state)

    repaired = BestOfTopRepairOperator(checker=checker).repair(
        instance,
        destroyed.remaining_placements,
        destroyed.removed_block_ids,
    )
    is_feasible, violations = checker.validate_solution(repaired.placements)

    assert is_feasible
    assert violations == []
    assert len(repaired.placements) == len(instance.blocks)


def test_bounded_exact_repair_operator_restores_a_feasible_solution() -> None:
    instance = load_instance(Path("examples/sample-instance.json"))
    checker = FeasibilityChecker(instance)
    state = ConstructiveSolver(checker=checker).solve(instance)
    destroyed = HighRiskClusterDestroyOperator(cluster_size=2).destroy(state)

    repaired = BoundedExactRepairOperator(checker=checker).repair(
        instance,
        destroyed.remaining_placements,
        destroyed.removed_block_ids,
    )
    is_feasible, violations = checker.validate_solution(repaired.placements)

    assert is_feasible
    assert violations == []
    assert len(repaired.placements) == len(instance.blocks)


def test_bounded_exact_repair_operator_falls_back_when_timed_out() -> None:
    instance = load_instance(Path("examples/sample-instance.json"))
    checker = FeasibilityChecker(instance)
    state = ConstructiveSolver(checker=checker).solve(instance)
    destroyed = HighRiskClusterDestroyOperator(cluster_size=2).destroy(state)

    repaired = BoundedExactRepairOperator(
        checker=checker,
        exact_time_limit_seconds=0.0,
    ).repair(
        instance,
        destroyed.remaining_placements,
        destroyed.removed_block_ids,
    )
    is_feasible, violations = checker.validate_solution(repaired.placements)

    assert is_feasible
    assert violations == []
    assert len(repaired.placements) == len(instance.blocks)


def test_congestion_destroy_operator_targets_dense_cluster() -> None:
    instance = Instance(
        yard=Yard(width=10, height=6, min_clearance=0),
        blocks=[
            Block(block_id="A", width=2, height=2, release_time=0, due_time=5, priority=0),
            Block(block_id="B", width=2, height=2, release_time=0, due_time=5, priority=0),
            Block(block_id="C", width=2, height=2, release_time=0, due_time=5, priority=0),
        ],
    )
    checker = FeasibilityChecker(instance)
    state = ConstructiveSolver(checker=checker).solve(instance)
    state.placements = [
        next(placement for placement in state.placements if placement.block_id == "A"),
        next(placement for placement in state.placements if placement.block_id == "B"),
        next(placement for placement in state.placements if placement.block_id == "C"),
    ]
    state.placements[0].x = 0
    state.placements[0].y = 0
    state.placements[1].x = 3
    state.placements[1].y = 0
    state.placements[2].x = 8
    state.placements[2].y = 4

    destroyed = CongestionClusterDestroyOperator(cluster_size=1).destroy(state)

    assert destroyed.removed_block_ids in (["A"], ["B"])


def test_local_search_preserves_best_feasible_incumbent() -> None:
    instance = load_instance(Path("examples/sample-instance.json"))
    checker = FeasibilityChecker(instance)
    baseline = ConstructiveSolver(checker=checker).solve(instance)

    improved = LocalSearchSolver(checker=checker, iterations=4).solve(instance)
    is_feasible, violations = checker.validate_solution(improved.placements)

    assert is_feasible
    assert violations == []
    assert improved.objective_value >= baseline.objective_value


def test_local_search_can_improve_with_seeded_repair_sampling() -> None:
    instance = Instance(
        yard=Yard(width=8, height=5, min_clearance=0),
        blocks=[
            Block(block_id="A", width=2, height=2, release_time=0, due_time=3, priority=1),
            Block(block_id="B", width=2, height=2, release_time=0, due_time=4, priority=0),
            Block(block_id="C", width=3, height=2, release_time=0, due_time=5, priority=2),
            Block(block_id="D", width=2, height=2, release_time=0, due_time=6, priority=0),
        ],
    )
    checker = FeasibilityChecker(instance)
    baseline = ConstructiveSolver(checker=checker).solve(instance)

    improved = LocalSearchSolver(
        checker=checker,
        iterations=12,
        destroy_operators=[HighRiskClusterDestroyOperator()],
        seed=7,
    ).solve(instance)
    is_feasible, violations = checker.validate_solution(improved.placements)

    assert is_feasible
    assert violations == []
    assert improved.objective_value > baseline.objective_value


def test_local_search_tracks_destroy_and_repair_diagnostics() -> None:
    instance = load_instance(Path("examples/sample-instance.json"))
    checker = FeasibilityChecker(instance)
    solver = LocalSearchSolver(checker=checker, iterations=4, seed=5)

    solver.solve(instance)

    assert {stats.name for stats in solver.last_diagnostics.destroy_stats} == {
        "congestion_cluster",
        "congestion_cluster_k3",
        "global_restart",
        "high_risk_cluster",
        "high_risk_cluster_k3",
    }
    assert {stats.name for stats in solver.last_diagnostics.repair_stats} == {
        "bounded_exact",
        "sampled_greedy",
        "best_of_top",
        "spread",
    }
    assert set(solver.last_diagnostics.destroy_weights) == {
        "congestion_cluster",
        "congestion_cluster_k3",
        "global_restart",
        "high_risk_cluster",
        "high_risk_cluster_k3",
    }
    assert set(solver.last_diagnostics.repair_weights) == {"best_of_top", "bounded_exact", "sampled_greedy", "spread"}


def test_large_destroy_operator_name_reflects_cluster_size() -> None:
    assert HighRiskClusterDestroyOperator(cluster_size=3).name == "high_risk_cluster_k3"
    assert CongestionClusterDestroyOperator(cluster_size=3).name == "congestion_cluster_k3"


def test_state_priority_prefers_lower_congestion_on_tie() -> None:
    instance = load_instance(Path("examples/sample-instance.json"))
    reference = SolutionState(
        instance=instance,
        objective_value=-5.0,
        objective_breakdown=ObjectiveBreakdown(
            area_utilization=0.30,
            lateness_penalty=0.0,
            retrieval_risk_penalty=2.10,
            congestion_penalty=3.20,
        ),
    )
    candidate = SolutionState(
        instance=instance,
        objective_value=-5.0,
        objective_breakdown=ObjectiveBreakdown(
            area_utilization=0.30,
            lateness_penalty=0.0,
            retrieval_risk_penalty=2.30,
            congestion_penalty=3.00,
        ),
    )

    assert state_priority_tuple(candidate) > state_priority_tuple(reference)


def test_local_search_preference_uses_breakdown_tiebreak() -> None:
    instance = load_instance(Path("examples/sample-instance.json"))
    reference = SolutionState(
        instance=instance,
        objective_value=-5.0,
        objective_breakdown=ObjectiveBreakdown(
            area_utilization=0.30,
            lateness_penalty=0.0,
            retrieval_risk_penalty=2.10,
            congestion_penalty=3.20,
        ),
    )
    candidate = SolutionState(
        instance=instance,
        objective_value=-5.0,
        objective_breakdown=ObjectiveBreakdown(
            area_utilization=0.30,
            lateness_penalty=0.0,
            retrieval_risk_penalty=2.30,
            congestion_penalty=3.00,
        ),
    )

    assert LocalSearchSolver._is_preferred(candidate, reference)


def test_weight_update_rewards_improvements_and_penalizes_failures() -> None:
    weights = {"op": 1.0}

    LocalSearchSolver._update_weight(weights, "op", accepted=False, improved=False)
    assert weights["op"] == 0.95

    LocalSearchSolver._update_weight(weights, "op", accepted=True, improved=False)
    assert weights["op"] == 1.45

    LocalSearchSolver._update_weight(weights, "op", accepted=True, improved=True)
    assert weights["op"] == 3.45


def test_local_search_respects_zero_time_limit() -> None:
    instance = load_instance(Path("examples/sample-instance.json"))
    checker = FeasibilityChecker(instance)
    baseline = ConstructiveSolver(checker=checker).solve(instance)
    solver = LocalSearchSolver(checker=checker, iterations=10, seed=5, time_limit_seconds=0.0)

    result = solver.solve(instance)

    assert result.objective_value == baseline.objective_value
    assert solver.last_diagnostics.stopped_by_time_limit
    assert solver.last_diagnostics.history == []


def test_local_search_treats_repair_failure_as_rejected_move() -> None:
    class SingleBlockDestroyOperator:
        @property
        def name(self) -> str:
            return "single_block"

        def destroy(self, state: SolutionState) -> DestroyResult:
            removed = state.placements[:1]
            return DestroyResult(
                removed_block_ids=[placement.block_id for placement in removed],
                remaining_placements=state.placements[1:],
            )

    class FailingRepairOperator:
        @property
        def name(self) -> str:
            return "failing_repair"

        def repair(self, instance, remaining_placements, removed_block_ids) -> SolutionState:
            raise ValueError("no feasible placement candidates")

    instance = load_instance(Path("examples/sample-instance.json"))
    checker = FeasibilityChecker(instance)
    baseline = ConstructiveSolver(checker=checker).solve(instance)
    solver = LocalSearchSolver(
        checker=checker,
        iterations=2,
        destroy_operators=[SingleBlockDestroyOperator()],
        repair_operators=[FailingRepairOperator()],
        seed=3,
    )

    result = solver.solve(instance)

    assert result.objective_value == baseline.objective_value
    assert len(solver.last_diagnostics.history) == 2
    assert all(not record.candidate_feasible for record in solver.last_diagnostics.history)
    assert all(not record.accepted for record in solver.last_diagnostics.history)