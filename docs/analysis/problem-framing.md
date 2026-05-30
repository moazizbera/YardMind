# Problem Framing

## Challenge Interpretation

OGC 2026 combines spatial layout and temporal scheduling in a shipyard setting. The core decision is not only whether a block fits, but whether it can be placed in a way that remains operationally efficient when future arrivals and removals happen.

## Working Assumptions

Until the official data format is implemented, YardMind assumes the real problem contains most of the following elements:
- rectangular or grid-based yard capacity
- block dimensions and orientation rules
- arrival or release times
- due dates or retrieval deadlines
- hard feasibility rules for placement and overlap
- implicit or explicit penalties for congestion, relocations, or delays

## Optimization View

This is best treated as a coupled optimization problem with these linked subproblems:
- assignment of a block to a yard area
- exact placement within that area
- timing of occupancy and removal
- avoidance of future blocking patterns

## Design Principle

YardMind is built around retrieval-aware optimization. Dense packing alone is not enough if it creates expensive rehandling later. The solver should prefer placements that preserve future mobility and reduce conflict cascades.

## Success Criteria

A competitive solution should:
- produce feasible plans reliably
- improve objective value under tight runtime limits
- avoid pathological future blocking
- scale to large hidden instances
- remain explainable in a technical report
