# Data Model

## Core Entities

### Block
Fields expected in the internal representation:
- `block_id`
- `width`
- `height`
- `release_time`
- `due_time`
- `priority`

### Yard
Fields expected in the internal representation:
- `width`
- `height`
- `zones`

### Placement
Fields expected in the internal representation:
- `block_id`
- `x`
- `y`
- `start_time`
- `end_time`
- `rotation`

### Instance
Aggregate object holding yard information and all blocks.

### SolutionState
Runtime object holding placements, objective score, and future diagnostics.

## Planned Extensions

When the official instance schema is available, extend the model with:
- handling resource limits
- block adjacency or clearance rules
- yard sub-areas with different capabilities
- relocation counters
- retrieval path feasibility metadata

## Temporary Development Schema

The current parser accepts a small JSON schema for local development and testing:
- `yard.width`
- `yard.height`
- `yard.zones`
- `blocks[].id`
- `blocks[].width`
- `blocks[].height`
- `blocks[].release_time`
- `blocks[].due_time`
- `blocks[].priority`

This schema exists only to let solver work proceed before the official contest parser is wired in.
