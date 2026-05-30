from __future__ import annotations

from dataclasses import dataclass
import random
from time import perf_counter
from typing import Protocol

from yardmind.models import Block, Instance, Placement
from yardmind.solver.constructive import ConstructiveSolver, ScoredPlacement
from yardmind.solver.feasibility import FeasibilityChecker
from yardmind.solver.scoring import score_solution
from yardmind.solver.state import ObjectiveBreakdown, SolutionState


def state_priority_tuple(state: SolutionState) -> tuple[float, float, float, float, float]:
    breakdown = state.objective_breakdown
    return (
        state.objective_value,
        -breakdown.congestion_penalty,
        -breakdown.retrieval_risk_penalty,
        -breakdown.lateness_penalty,
        breakdown.area_utilization,
    )


@dataclass(slots=True)
class DestroyResult:
    removed_block_ids: list[str]
    remaining_placements: list[Placement]


@dataclass(slots=True)
class OperatorStats:
    name: str
    attempts: int = 0
    feasible_candidates: int = 0
    accepted_candidates: int = 0
    improved_candidates: int = 0


@dataclass(slots=True)
class IterationRecord:
    iteration: int
    destroy_operator: str
    repair_operator: str
    candidate_feasible: bool
    candidate_objective: float
    incumbent_objective: float
    best_objective: float
    accepted: bool
    improved_best: bool


@dataclass(slots=True)
class SearchDiagnostics:
    iterations: int
    destroy_stats: list[OperatorStats]
    repair_stats: list[OperatorStats]
    history: list[IterationRecord]
    destroy_weights: dict[str, float]
    repair_weights: dict[str, float]
    time_limit_seconds: float | None
    stopped_by_time_limit: bool

    @property
    def attempted_moves(self) -> int:
        return sum(stats.attempts for stats in self.destroy_stats)


class DestroyOperator(Protocol):
    @property
    def name(self) -> str:
        ...

    def destroy(self, state: SolutionState) -> DestroyResult:
        ...


class RepairOperator(Protocol):
    @property
    def name(self) -> str:
        ...

    def repair(
        self,
        instance: Instance,
        remaining_placements: list[Placement],
        removed_block_ids: list[str],
    ) -> SolutionState:
        ...


class HighRiskClusterDestroyOperator:
    def __init__(self, cluster_size: int = 2) -> None:
        self.cluster_size = max(1, cluster_size)

    @property
    def name(self) -> str:
        if self.cluster_size == 2:
            return "high_risk_cluster"
        return f"high_risk_cluster_k{self.cluster_size}"

    def destroy(self, state: SolutionState) -> DestroyResult:
        ordered = sorted(
            state.placements,
            key=lambda placement: self._placement_risk(state.instance, placement),
            reverse=True,
        )
        removed = ordered[: min(self.cluster_size, len(ordered))]
        removed_ids = [placement.block_id for placement in removed]
        remaining = [placement for placement in state.placements if placement.block_id not in removed_ids]
        return DestroyResult(removed_block_ids=removed_ids, remaining_placements=remaining)

    @staticmethod
    def _placement_risk(instance: Instance, placement: Placement) -> float:
        breakdown = score_solution(instance, [placement])
        block = instance.block_by_id(placement.block_id)
        urgency = 1.0 / max(1, block.due_time - block.release_time + 1)
        return breakdown.retrieval_risk_penalty + urgency - (0.05 * block.priority)


class CongestionClusterDestroyOperator:
    def __init__(self, cluster_size: int = 2) -> None:
        self.cluster_size = max(1, cluster_size)

    @property
    def name(self) -> str:
        if self.cluster_size == 2:
            return "congestion_cluster"
        return f"congestion_cluster_k{self.cluster_size}"

    def destroy(self, state: SolutionState) -> DestroyResult:
        ordered = sorted(
            state.placements,
            key=lambda placement: self._placement_congestion(state.instance, state.placements, placement),
            reverse=True,
        )
        removed = ordered[: min(self.cluster_size, len(ordered))]
        removed_ids = [placement.block_id for placement in removed]
        remaining = [placement for placement in state.placements if placement.block_id not in removed_ids]
        return DestroyResult(removed_block_ids=removed_ids, remaining_placements=remaining)

    @staticmethod
    def _placement_congestion(
        instance: Instance,
        placements: list[Placement],
        target: Placement,
    ) -> float:
        target_block = instance.block_by_id(target.block_id)
        target_width, target_height = target_block.rotated_dimensions(target.rotation)
        target_center_x = target.x + target_width / 2
        target_center_y = target.y + target_height / 2
        penalty = 0.0

        for other in placements:
            if other.block_id == target.block_id:
                continue
            if not FeasibilityChecker._overlaps_in_time(target, other):
                continue

            other_block = instance.block_by_id(other.block_id)
            other_width, other_height = other_block.rotated_dimensions(other.rotation)
            other_center_x = other.x + other_width / 2
            other_center_y = other.y + other_height / 2
            distance = abs(target_center_x - other_center_x) + abs(target_center_y - other_center_y)
            penalty += 1.0 if distance == 0 else 1.0 / distance

        return penalty


class GlobalRestartDestroyOperator:
    @property
    def name(self) -> str:
        return "global_restart"

    def destroy(self, state: SolutionState) -> DestroyResult:
        return DestroyResult(
            removed_block_ids=[placement.block_id for placement in state.placements],
            remaining_placements=[],
        )


class GreedyRepairOperator:
    def __init__(
        self,
        checker: FeasibilityChecker,
        rng: random.Random | None = None,
        sample_top_k: int = 3,
    ) -> None:
        self.checker = checker
        self.constructive = ConstructiveSolver(checker=checker)
        self.rng = rng or random.Random(0)
        self.sample_top_k = max(1, sample_top_k)

    @property
    def name(self) -> str:
        return "sampled_greedy"

    def repair(
        self,
        instance: Instance,
        remaining_placements: list[Placement],
        removed_block_ids: list[str],
    ) -> SolutionState:
        state = SolutionState(instance=instance, placements=list(remaining_placements))

        for block in sorted(
            (instance.block_by_id(block_id) for block_id in removed_block_ids),
            key=self._repair_order,
        ):
            ranked_candidates, _ = self.constructive.rank_feasible_placements(instance, state, block.block_id)
            placement = self._select_repair_placement(ranked_candidates)
            state.add(placement)

        state.objective_breakdown = score_solution(instance, state.placements)
        state.objective_value = state.objective_breakdown.total
        return state

    @staticmethod
    def _repair_order(block: Block) -> tuple[int, int]:
        return block.due_time, -block.priority

    def _select_repair_placement(self, ranked_candidates: list[ScoredPlacement]) -> Placement:
        if not ranked_candidates:
            raise ValueError("Repair operator received no feasible placement candidates")

        candidate_pool = ranked_candidates[: min(self.sample_top_k, len(ranked_candidates))]
        return self.rng.choice(candidate_pool).placement


class SpreadRepairOperator(GreedyRepairOperator):
    @property
    def name(self) -> str:
        return "spread"

    def _select_repair_placement(self, ranked_candidates: list[ScoredPlacement]) -> Placement:
        if not ranked_candidates:
            raise ValueError("Repair operator received no feasible placement candidates")

        candidate_pool = ranked_candidates[: min(self.sample_top_k, len(ranked_candidates))]
        best_candidate = min(
            candidate_pool,
            key=lambda candidate: (
                self._candidate_congestion(candidate.placement, candidate_pool),
                -candidate.score,
            ),
        )
        return best_candidate.placement

    @staticmethod
    def _candidate_congestion(candidate: Placement, candidate_pool: list[ScoredPlacement]) -> float:
        penalty = 0.0

        for other in candidate_pool:
            if other.placement.block_id == candidate.block_id:
                continue
            distance = abs(candidate.x - other.placement.x) + abs(candidate.y - other.placement.y)
            penalty += 1.0 if distance == 0 else 1.0 / distance

        return penalty


class BestOfTopRepairOperator(GreedyRepairOperator):
    @property
    def name(self) -> str:
        return "best_of_top"

    def repair(
        self,
        instance: Instance,
        remaining_placements: list[Placement],
        removed_block_ids: list[str],
    ) -> SolutionState:
        state = SolutionState(instance=instance, placements=list(remaining_placements))

        for block in sorted(
            (instance.block_by_id(block_id) for block_id in removed_block_ids),
            key=self._repair_order,
        ):
            ranked_candidates, _ = self.constructive.rank_feasible_placements(instance, state, block.block_id)
            placement = self._select_best_state_placement(instance, state, ranked_candidates)
            state.add(placement)

        state.objective_breakdown = score_solution(instance, state.placements)
        state.objective_value = state.objective_breakdown.total
        return state

    def _select_best_state_placement(
        self,
        instance: Instance,
        state: SolutionState,
        ranked_candidates: list[ScoredPlacement],
    ) -> Placement:
        if not ranked_candidates:
            raise ValueError("Repair operator received no feasible placement candidates")

        candidate_pool = ranked_candidates[: min(self.sample_top_k, len(ranked_candidates))]
        best_candidate = None
        best_priority = None

        for scored_candidate in candidate_pool:
            candidate_state = SolutionState(
                instance=instance,
                placements=[*state.placements, scored_candidate.placement],
            )
            candidate_state.objective_breakdown = score_solution(instance, candidate_state.placements)
            candidate_state.objective_value = candidate_state.objective_breakdown.total
            candidate_priority = state_priority_tuple(candidate_state)
            if best_priority is None or candidate_priority > best_priority:
                best_candidate = scored_candidate.placement
                best_priority = candidate_priority

        if best_candidate is None:
            raise ValueError("Repair operator could not select a candidate placement")

        return best_candidate


class BoundedExactRepairOperator(GreedyRepairOperator):
    def __init__(
        self,
        checker: FeasibilityChecker,
        rng: random.Random | None = None,
        sample_top_k: int = 3,
        max_exact_blocks: int = 3,
        exact_time_limit_seconds: float | None = None,
    ) -> None:
        super().__init__(checker=checker, rng=rng, sample_top_k=sample_top_k)
        self.max_exact_blocks = max(1, max_exact_blocks)
        self.exact_time_limit_seconds = (
            exact_time_limit_seconds if exact_time_limit_seconds is None else max(0.0, exact_time_limit_seconds)
        )
        self.fallback = BestOfTopRepairOperator(checker=checker, rng=rng, sample_top_k=sample_top_k)

    @property
    def name(self) -> str:
        return "bounded_exact"

    def repair(
        self,
        instance: Instance,
        remaining_placements: list[Placement],
        removed_block_ids: list[str],
    ) -> SolutionState:
        if len(removed_block_ids) > self.max_exact_blocks:
            return self.fallback.repair(instance, remaining_placements, removed_block_ids)

        started_at = perf_counter()
        if self._timed_out(started_at):
            return self.fallback.repair(instance, remaining_placements, removed_block_ids)

        ordered_block_ids = [
            block.block_id
            for block in sorted(
                (instance.block_by_id(block_id) for block_id in removed_block_ids),
                key=self._repair_order,
            )
        ]
        initial_state = SolutionState(instance=instance, placements=list(remaining_placements))
        best_state = self._search_best_state(instance, initial_state, ordered_block_ids, started_at)
        if best_state is None:
            return self.fallback.repair(instance, remaining_placements, removed_block_ids)

        best_state.objective_breakdown = score_solution(instance, best_state.placements)
        best_state.objective_value = best_state.objective_breakdown.total
        return best_state

    def _search_best_state(
        self,
        instance: Instance,
        state: SolutionState,
        remaining_block_ids: list[str],
        started_at: float,
    ) -> SolutionState | None:
        if self._timed_out(started_at):
            return None

        if not remaining_block_ids:
            completed = SolutionState(instance=instance, placements=list(state.placements))
            completed.objective_breakdown = score_solution(instance, completed.placements)
            completed.objective_value = completed.objective_breakdown.total
            return completed

        ranked_candidates, _ = self.constructive.rank_feasible_placements(instance, state, remaining_block_ids[0])
        if not ranked_candidates:
            return None

        candidate_pool = ranked_candidates[: min(self.sample_top_k, len(ranked_candidates))]
        best_state = None
        best_priority = None

        for scored_candidate in candidate_pool:
            next_state = SolutionState(
                instance=instance,
                placements=[*state.placements, scored_candidate.placement],
            )
            candidate_state = self._search_best_state(instance, next_state, remaining_block_ids[1:], started_at)
            if candidate_state is None:
                continue

            candidate_priority = state_priority_tuple(candidate_state)
            if best_priority is None or candidate_priority > best_priority:
                best_state = candidate_state
                best_priority = candidate_priority

        return best_state

    def _timed_out(self, started_at: float) -> bool:
        if self.exact_time_limit_seconds is None:
            return False
        return perf_counter() - started_at >= self.exact_time_limit_seconds


class LocalSearchSolver:
    def __init__(
        self,
        checker: FeasibilityChecker,
        iterations: int = 8,
        destroy_operators: list[DestroyOperator] | None = None,
        repair_operators: list[RepairOperator] | None = None,
        seed: int = 0,
        time_limit_seconds: float | None = None,
    ) -> None:
        self.checker = checker
        self.iterations = max(1, iterations)
        self.rng = random.Random(seed)
        self.time_limit_seconds = time_limit_seconds if time_limit_seconds is None else max(0.0, time_limit_seconds)
        self.constructive = ConstructiveSolver(checker=checker)
        self.destroy_operators = destroy_operators or [
            HighRiskClusterDestroyOperator(),
            CongestionClusterDestroyOperator(),
            HighRiskClusterDestroyOperator(cluster_size=3),
            CongestionClusterDestroyOperator(cluster_size=3),
            GlobalRestartDestroyOperator(),
        ]
        self.repair_operators = repair_operators or [
            GreedyRepairOperator(checker=checker, rng=self.rng),
            BoundedExactRepairOperator(
                checker=checker,
                rng=self.rng,
                exact_time_limit_seconds=self.time_limit_seconds,
            ),
            BestOfTopRepairOperator(checker=checker, rng=self.rng),
            SpreadRepairOperator(checker=checker, rng=self.rng),
        ]
        self.last_diagnostics = SearchDiagnostics(
            iterations=self.iterations,
            destroy_stats=[OperatorStats(name=operator.name) for operator in self.destroy_operators],
            repair_stats=[OperatorStats(name=operator.name) for operator in self.repair_operators],
            history=[],
            destroy_weights={operator.name: 1.0 for operator in self.destroy_operators},
            repair_weights={operator.name: 1.0 for operator in self.repair_operators},
            time_limit_seconds=self.time_limit_seconds,
            stopped_by_time_limit=False,
        )

    def solve(self, instance: Instance) -> SolutionState:
        started_at = perf_counter()
        incumbent = self.constructive.solve(instance)
        best_state = self._clone_state(incumbent)
        destroy_stats_by_name = {
            stats.name: stats
            for stats in [OperatorStats(name=operator.name) for operator in self.destroy_operators]
        }
        repair_stats_by_name = {
            stats.name: stats
            for stats in [OperatorStats(name=operator.name) for operator in self.repair_operators]
        }
        history: list[IterationRecord] = []
        destroy_weights = {operator.name: 1.0 for operator in self.destroy_operators}
        repair_weights = {operator.name: 1.0 for operator in self.repair_operators}
        stopped_by_time_limit = False

        for iteration in range(1, self.iterations + 1):
            if self.time_limit_seconds is not None and perf_counter() - started_at >= self.time_limit_seconds:
                stopped_by_time_limit = True
                break
            destroy_operator = self._weighted_choice(self.destroy_operators, destroy_weights)
            repair_operator = self._weighted_choice(self.repair_operators, repair_weights)
            destroy_stats = destroy_stats_by_name[destroy_operator.name]
            repair_stats = repair_stats_by_name[repair_operator.name]
            destroy_stats.attempts += 1
            repair_stats.attempts += 1
            destroyed = destroy_operator.destroy(incumbent)
            try:
                candidate = repair_operator.repair(
                    instance,
                    destroyed.remaining_placements,
                    destroyed.removed_block_ids,
                )
            except ValueError:
                self._update_weight(destroy_weights, destroy_operator.name, accepted=False, improved=False)
                self._update_weight(repair_weights, repair_operator.name, accepted=False, improved=False)
                history.append(
                    IterationRecord(
                        iteration=iteration,
                        destroy_operator=destroy_operator.name,
                        repair_operator=repair_operator.name,
                        candidate_feasible=False,
                        candidate_objective=incumbent.objective_value,
                        incumbent_objective=incumbent.objective_value,
                        best_objective=best_state.objective_value,
                        accepted=False,
                        improved_best=False,
                    )
                )
                continue
            is_feasible, _ = self.checker.validate_solution(candidate.placements)
            accepted = False
            improved_best = False
            if not is_feasible:
                self._update_weight(destroy_weights, destroy_operator.name, accepted=False, improved=False)
                self._update_weight(repair_weights, repair_operator.name, accepted=False, improved=False)
                history.append(
                    IterationRecord(
                        iteration=iteration,
                        destroy_operator=destroy_operator.name,
                        repair_operator=repair_operator.name,
                        candidate_feasible=False,
                        candidate_objective=candidate.objective_value,
                        incumbent_objective=incumbent.objective_value,
                        best_objective=best_state.objective_value,
                        accepted=False,
                        improved_best=False,
                    )
                )
                continue
            destroy_stats.feasible_candidates += 1
            repair_stats.feasible_candidates += 1
            if self._is_preferred(candidate, incumbent):
                incumbent = candidate
                destroy_stats.accepted_candidates += 1
                repair_stats.accepted_candidates += 1
                accepted = True
            if self._is_preferred(candidate, best_state):
                best_state = self._clone_state(candidate)
                destroy_stats.improved_candidates += 1
                repair_stats.improved_candidates += 1
                improved_best = True

            self._update_weight(destroy_weights, destroy_operator.name, accepted=accepted, improved=improved_best)
            self._update_weight(repair_weights, repair_operator.name, accepted=accepted, improved=improved_best)

            history.append(
                IterationRecord(
                    iteration=iteration,
                    destroy_operator=destroy_operator.name,
                    repair_operator=repair_operator.name,
                    candidate_feasible=True,
                    candidate_objective=candidate.objective_value,
                    incumbent_objective=incumbent.objective_value,
                    best_objective=best_state.objective_value,
                    accepted=accepted,
                    improved_best=improved_best,
                )
            )

        self.last_diagnostics = SearchDiagnostics(
            iterations=self.iterations,
            destroy_stats=list(destroy_stats_by_name.values()),
            repair_stats=list(repair_stats_by_name.values()),
            history=history,
            destroy_weights=destroy_weights,
            repair_weights=repair_weights,
            time_limit_seconds=self.time_limit_seconds,
            stopped_by_time_limit=stopped_by_time_limit,
        )

        return best_state

    @staticmethod
    def _clone_state(state: SolutionState) -> SolutionState:
        return SolutionState(
            instance=state.instance,
            placements=list(state.placements),
            objective_value=state.objective_value,
            objective_breakdown=ObjectiveBreakdown(
                area_utilization=state.objective_breakdown.area_utilization,
                lateness_penalty=state.objective_breakdown.lateness_penalty,
                retrieval_risk_penalty=state.objective_breakdown.retrieval_risk_penalty,
                congestion_penalty=state.objective_breakdown.congestion_penalty,
            ),
        )

    @staticmethod
    def _is_preferred(candidate: SolutionState, reference: SolutionState) -> bool:
        return state_priority_tuple(candidate) > state_priority_tuple(reference)

    def _weighted_choice(self, operators: list[DestroyOperator] | list[RepairOperator], weights: dict[str, float]):
        total_weight = sum(weights[operator.name] for operator in operators)
        threshold = self.rng.random() * total_weight
        cumulative = 0.0

        for operator in operators:
            cumulative += weights[operator.name]
            if cumulative >= threshold:
                return operator

        return operators[-1]

    @staticmethod
    def _update_weight(weights: dict[str, float], name: str, accepted: bool, improved: bool) -> None:
        current = weights[name]
        if improved:
            weights[name] = current + 2.0
            return
        if accepted:
            weights[name] = current + 0.5
            return
        weights[name] = max(0.5, current * 0.95)