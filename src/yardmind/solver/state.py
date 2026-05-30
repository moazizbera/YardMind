from __future__ import annotations

from dataclasses import dataclass, field

from yardmind.models import Instance, Placement


@dataclass(slots=True)
class ObjectiveBreakdown:
    area_utilization: float = 0.0
    lateness_penalty: float = 0.0
    retrieval_risk_penalty: float = 0.0
    congestion_penalty: float = 0.0

    @property
    def total(self) -> float:
        return (
            self.area_utilization
            - self.lateness_penalty
            - self.retrieval_risk_penalty
            - self.congestion_penalty
        )


@dataclass(slots=True)
class SolutionState:
    instance: Instance
    placements: list[Placement] = field(default_factory=list)
    objective_value: float = 0.0
    objective_breakdown: ObjectiveBreakdown = field(default_factory=ObjectiveBreakdown)

    def add(self, placement: Placement) -> None:
        self.placements.append(placement)
