from __future__ import annotations

from yardmind.models import Instance, Placement


class FeasibilityChecker:
    def __init__(self, instance: Instance) -> None:
        self.instance = instance

    def validate_solution(self, placements: list[Placement]) -> tuple[bool, list[str]]:
        violations: list[str] = []
        seen_ids: set[str] = set()

        for placement in placements:
            if placement.block_id in seen_ids:
                violations.append(f"duplicate placement for block {placement.block_id}")
            seen_ids.add(placement.block_id)

            is_valid, placement_violations = self.validate_placement(placement, placements, skip_id=placement.block_id)
            violations.extend(placement_violations if not is_valid else [])

        missing_ids = {block.block_id for block in self.instance.blocks} - seen_ids
        for block_id in sorted(missing_ids):
            violations.append(f"missing placement for block {block_id}")

        return len(violations) == 0, violations

    def validate_placement(
        self,
        placement: Placement,
        placements: list[Placement],
        skip_id: str | None = None,
    ) -> tuple[bool, list[str]]:
        violations: list[str] = []
        block = self.instance.block_by_id(placement.block_id)
        width, height = block.rotated_dimensions(placement.rotation)

        if placement.start_time < block.release_time:
            violations.append(f"block {block.block_id} starts before release time")
        if placement.end_time > block.due_time:
            violations.append(f"block {block.block_id} ends after due time")
        if placement.start_time > placement.end_time:
            violations.append(f"block {block.block_id} has inverted time interval")
        if placement.x < 0 or placement.y < 0:
            violations.append(f"block {block.block_id} has negative coordinates")
        if placement.x + width > self.instance.yard.width:
            violations.append(f"block {block.block_id} exceeds yard width")
        if placement.y + height > self.instance.yard.height:
            violations.append(f"block {block.block_id} exceeds yard height")

        for other in placements:
            if other.block_id == skip_id or other.block_id == placement.block_id:
                continue
            if not self._overlaps_in_time(placement, other):
                continue
            if self._overlaps_in_space(placement, other):
                violations.append(
                    f"block {placement.block_id} overlaps block {other.block_id} in space-time"
                )
                continue
            if self._violates_min_clearance(placement, other):
                violations.append(
                    f"block {placement.block_id} violates minimum clearance with block {other.block_id}"
                )

        return len(violations) == 0, violations

    @staticmethod
    def _overlaps_in_time(left: Placement, right: Placement) -> bool:
        return not (left.end_time <= right.start_time or right.end_time <= left.start_time)

    def _overlaps_in_space(self, left: Placement, right: Placement) -> bool:
        left_block = self.instance.block_by_id(left.block_id)
        right_block = self.instance.block_by_id(right.block_id)
        left_width, left_height = left_block.rotated_dimensions(left.rotation)
        right_width, right_height = right_block.rotated_dimensions(right.rotation)

        return not (
            left.x + left_width <= right.x
            or right.x + right_width <= left.x
            or left.y + left_height <= right.y
            or right.y + right_height <= left.y
        )

    def _violates_min_clearance(self, left: Placement, right: Placement) -> bool:
        clearance = max(0, self.instance.yard.min_clearance)
        if clearance == 0:
            return False

        left_block = self.instance.block_by_id(left.block_id)
        right_block = self.instance.block_by_id(right.block_id)
        left_width, left_height = left_block.rotated_dimensions(left.rotation)
        right_width, right_height = right_block.rotated_dimensions(right.rotation)

        return not (
            left.x + left_width + clearance <= right.x
            or right.x + right_width + clearance <= left.x
            or left.y + left_height + clearance <= right.y
            or right.y + right_height + clearance <= left.y
        )
