from __future__ import annotations

from yardmind.models import Instance, Placement
from yardmind.solver.state import ObjectiveBreakdown


def score_solution(instance: Instance, placements: list[Placement]) -> ObjectiveBreakdown:
    total_area = instance.yard.width * instance.yard.height
    used_area = 0.0
    lateness_penalty = 0.0
    retrieval_risk_penalty = 0.0
    congestion_penalty = 0.0

    for placement in placements:
        block = instance.block_by_id(placement.block_id)
        width, height = block.rotated_dimensions(placement.rotation)
        used_area += width * height
        lateness_penalty += max(0, placement.end_time - block.due_time)
        retrieval_risk_penalty += _edge_distance_penalty(instance, placement, width, height)
        congestion_penalty += _local_density_penalty(instance, placements, placement)

    area_utilization = used_area / total_area if total_area else 0.0
    return ObjectiveBreakdown(
        area_utilization=area_utilization,
        lateness_penalty=lateness_penalty,
        retrieval_risk_penalty=retrieval_risk_penalty,
        congestion_penalty=congestion_penalty,
    )


def score_placement_candidate(
    instance: Instance,
    placements: list[Placement],
    candidate: Placement,
) -> float:
    block = instance.block_by_id(candidate.block_id)
    width, height = block.rotated_dimensions(candidate.rotation)
    edge_penalty = _edge_distance_penalty(instance, candidate, width, height)
    congestion_penalty = _local_density_penalty(instance, placements, candidate)
    priority_bonus = block.priority * 0.02
    early_due_bonus = 1.0 / max(1, block.due_time - block.release_time + 1)
    compactness_bonus = 0.35 / max(1, candidate.y + height)
    return (
        priority_bonus
        + early_due_bonus
        + compactness_bonus
        - 0.35 * edge_penalty
        - 2.5 * congestion_penalty
    )


def _edge_distance_penalty(
    instance: Instance,
    placement: Placement,
    width: int,
    height: int,
) -> float:
    right_gap = instance.yard.width - (placement.x + width)
    top_gap = instance.yard.height - (placement.y + height)
    return (placement.x + placement.y + right_gap + top_gap) / max(1, instance.yard.width + instance.yard.height)


def _local_density_penalty(
    instance: Instance,
    placements: list[Placement],
    candidate: Placement,
) -> float:
    block = instance.block_by_id(candidate.block_id)
    width, height = block.rotated_dimensions(candidate.rotation)
    candidate_center_x = candidate.x + width / 2
    candidate_center_y = candidate.y + height / 2
    penalty = 0.0

    for other in placements:
        other_block = instance.block_by_id(other.block_id)
        other_width, other_height = other_block.rotated_dimensions(other.rotation)
        other_center_x = other.x + other_width / 2
        other_center_y = other.y + other_height / 2
        distance = abs(candidate_center_x - other_center_x) + abs(candidate_center_y - other_center_y)
        if distance == 0:
            penalty += 1.0
            continue
        if _overlaps_in_time(candidate, other):
            penalty += 1.0 / distance

    return penalty


def _overlaps_in_time(left: Placement, right: Placement) -> bool:
    return not (left.end_time <= right.start_time or right.end_time <= left.start_time)