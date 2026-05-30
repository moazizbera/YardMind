from __future__ import annotations

from dataclasses import dataclass

from yardmind.models import Instance, Placement
from yardmind.solver.feasibility import FeasibilityChecker
from yardmind.solver.scoring import score_solution, score_placement_candidate
from yardmind.solver.state import SolutionState


@dataclass(slots=True)
class ScoredPlacement:
    placement: Placement
    score: float


class ConstructiveSolver:
    """Feasibility-first constructive solver with simple retrieval-aware scoring."""

    def __init__(self, checker: FeasibilityChecker) -> None:
        self.checker = checker

    def solve(self, instance: Instance) -> SolutionState:
        state = SolutionState(instance=instance)

        for block in sorted(instance.blocks, key=lambda item: (item.due_time, -item.priority)):
            placement = self.select_best_placement(instance, state, block.block_id)
            state.add(placement)

        state.objective_breakdown = score_solution(instance, state.placements)
        state.objective_value = state.objective_breakdown.total
        return state

    def select_best_placement(
        self,
        instance: Instance,
        state: SolutionState,
        block_id: str,
    ) -> Placement:
        ranked_candidates, last_violations = self.rank_feasible_placements(instance, state, block_id)
        if not ranked_candidates:
            raise ValueError(
                f"Unable to place block {block_id} constructively: {', '.join(last_violations)}"
            )

        return ranked_candidates[0].placement

    def rank_feasible_placements(
        self,
        instance: Instance,
        state: SolutionState,
        block_id: str,
    ) -> tuple[list[ScoredPlacement], list[str]]:
        block = instance.block_by_id(block_id)
        ranked_candidates: list[ScoredPlacement] = []
        last_violations: list[str] = []

        for y in range(0, instance.yard.height - block.height + 1):
            for x in range(0, instance.yard.width - block.width + 1):
                candidate = Placement(
                    block_id=block.block_id,
                    x=x,
                    y=y,
                    start_time=block.release_time,
                    end_time=block.due_time,
                )
                is_valid, violations = self.checker.validate_placement(candidate, state.placements)
                if not is_valid:
                    last_violations = violations
                    continue

                candidate_score = score_placement_candidate(instance, state.placements, candidate)
                ranked_candidates.append(ScoredPlacement(placement=candidate, score=candidate_score))

        ranked_candidates.sort(key=lambda candidate: candidate.score, reverse=True)
        return ranked_candidates, last_violations
