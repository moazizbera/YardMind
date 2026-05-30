from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Literal

from yardmind.models import Bay, Block, Instance, Yard


class InstanceFormatError(ValueError):
    """Raised when an input instance does not match the expected schema."""


def load_instance(path: Path, input_format: Literal["development", "official"] = "development") -> Instance:
    if input_format == "official":
        return _load_official_instance(path)
    return _load_development_instance(path)


def _load_development_instance(path: Path) -> Instance:
    raw = json.loads(path.read_text(encoding="utf-8"))

    try:
        yard_raw = raw["yard"]
        blocks_raw = raw["blocks"]
    except KeyError as exc:
        raise InstanceFormatError(f"Missing required top-level field: {exc.args[0]}") from exc

    yard = Yard(
        width=int(yard_raw["width"]),
        height=int(yard_raw["height"]),
        min_clearance=int(yard_raw.get("min_clearance", 0)),
        zones=list(yard_raw.get("zones", [])),
    )

    blocks: list[Block] = []
    for index, block_raw in enumerate(blocks_raw):
        try:
            block = Block(
                block_id=str(block_raw["id"]),
                width=int(block_raw["width"]),
                height=int(block_raw["height"]),
                release_time=int(block_raw["release_time"]),
                due_time=int(block_raw["due_time"]),
                priority=int(block_raw.get("priority", 0)),
            )
        except KeyError as exc:
            raise InstanceFormatError(
                f"Block at index {index} is missing field: {exc.args[0]}"
            ) from exc
        blocks.append(block)

    return Instance(yard=yard, blocks=blocks, source_format="development", name=path.stem)


def _load_official_instance(path: Path) -> Instance:
    raw = json.loads(path.read_text(encoding="utf-8"))

    try:
        bays_raw = raw["bays"]
        blocks_raw = raw["blocks"]
        weights_raw = raw["weights"]
    except KeyError as exc:
        raise InstanceFormatError(
            f"Missing required top-level field: {exc.args[0]}"
        ) from exc

    if not isinstance(bays_raw, list) or not bays_raw:
        raise InstanceFormatError("Official instances must define a non-empty 'bays' list")
    if not isinstance(blocks_raw, list) or not blocks_raw:
        raise InstanceFormatError("Official instances must define a non-empty 'blocks' list")
    if not isinstance(weights_raw, dict):
        raise InstanceFormatError("Official instances must define a 'weights' object")

    bays: list[Bay] = []
    for index, bay_raw in enumerate(bays_raw):
        try:
            bay = Bay(
                bay_id=index,
                width=int(bay_raw["width"]),
                height=int(bay_raw["height"]),
            )
        except KeyError as exc:
            raise InstanceFormatError(
                f"Bay at index {index} is missing field: {exc.args[0]}"
            ) from exc
        if bay.width <= 0 or bay.height <= 0:
            raise InstanceFormatError(
                f"Bay at index {index} must have positive dimensions, got {bay.width}x{bay.height}"
            )
        bays.append(bay)

    weights: dict[str, float] = {}
    for key in ("w1", "w2", "w3"):
        if key not in weights_raw:
            raise InstanceFormatError(f"Official weights are missing field: {key}")
        weights[key] = float(weights_raw[key])

    blocks: list[Block] = []
    for index, block_raw in enumerate(blocks_raw):
        try:
            bay_preferences = [int(value) for value in block_raw["bay_preferences"]]
            width, height, orientation_count = _derive_official_block_dimensions(block_raw["shape"], index)
            block = Block(
                block_id=str(index),
                width=width,
                height=height,
                release_time=int(block_raw["release_time"]),
                due_time=int(block_raw["due_date"]),
                priority=0,
            )
        except KeyError as exc:
            raise InstanceFormatError(
                f"Block at index {index} is missing field: {exc.args[0]}"
            ) from exc

        if len(bay_preferences) != len(bays):
            raise InstanceFormatError(
                f"Block at index {index} must define {len(bays)} bay preferences, got {len(bay_preferences)}"
            )

        block.metadata.update(
            {
                "official_block_id": index,
                "orientation_count": orientation_count,
                "processing_time": int(block_raw["processing_time"]),
                "workload": int(block_raw["workload"]),
                "bay_preferences": bay_preferences,
            }
        )
        blocks.append(block)

    yard = Yard(
        width=max(bay.width for bay in bays),
        height=max(bay.height for bay in bays),
    )
    return Instance(
        yard=yard,
        blocks=blocks,
        source_format="official",
        name=str(raw.get("name", path.stem)),
        bays=bays,
        weights=weights,
        metadata={"raw_problem": raw},
    )


def _derive_official_block_dimensions(shape_raw: object, block_index: int) -> tuple[int, int, int]:
    if not isinstance(shape_raw, list) or not shape_raw:
        raise InstanceFormatError(
            f"Block at index {block_index} must define a non-empty 'shape' list"
        )

    max_width = 0
    max_height = 0
    for orientation_index, orientation_raw in enumerate(shape_raw):
        if not isinstance(orientation_raw, dict) or "layers" not in orientation_raw:
            raise InstanceFormatError(
                f"Block at index {block_index} orientation {orientation_index} is missing field: layers"
            )
        layers_raw = orientation_raw["layers"]
        if not isinstance(layers_raw, list) or not layers_raw:
            raise InstanceFormatError(
                f"Block at index {block_index} orientation {orientation_index} must define a non-empty 'layers' list"
            )

        points: list[tuple[float, float]] = []
        for layer_index, layer_raw in enumerate(layers_raw):
            if not isinstance(layer_raw, list) or not layer_raw:
                raise InstanceFormatError(
                    f"Block at index {block_index} orientation {orientation_index} layer {layer_index} must be a non-empty point list"
                )
            for point_index, point_raw in enumerate(layer_raw):
                if not isinstance(point_raw, list | tuple) or len(point_raw) != 2:
                    raise InstanceFormatError(
                        f"Block at index {block_index} orientation {orientation_index} layer {layer_index} point {point_index} must contain exactly two coordinates"
                    )
                points.append((float(point_raw[0]), float(point_raw[1])))

        min_x = min(point[0] for point in points)
        max_x = max(point[0] for point in points)
        min_y = min(point[1] for point in points)
        max_y = max(point[1] for point in points)
        max_width = max(max_width, max(1, math.ceil(max_x - min_x)))
        max_height = max(max_height, max(1, math.ceil(max_y - min_y)))

    return max_width, max_height, len(shape_raw)
