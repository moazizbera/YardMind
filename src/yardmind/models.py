from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable


@dataclass(slots=True)
class Block:
    block_id: str
    width: int
    height: int
    release_time: int
    due_time: int
    priority: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def rotated_dimensions(self, rotation: int) -> tuple[int, int]:
        if rotation % 180 == 90:
            return self.height, self.width
        return self.width, self.height


@dataclass(slots=True)
class Placement:
    block_id: str
    x: int
    y: int
    start_time: int
    end_time: int
    rotation: int = 0


@dataclass(slots=True)
class Yard:
    width: int
    height: int
    min_clearance: int = 0
    zones: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Bay:
    bay_id: int
    width: int
    height: int


@dataclass(slots=True)
class Instance:
    yard: Yard
    blocks: list[Block]
    source_format: str = "development"
    name: str | None = None
    bays: list[Bay] = field(default_factory=list)
    weights: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def iter_blocks(self) -> Iterable[Block]:
        return iter(self.blocks)

    def block_by_id(self, block_id: str) -> Block:
        for block in self.blocks:
            if block.block_id == block_id:
                return block
        raise KeyError(f"Unknown block_id: {block_id}")
