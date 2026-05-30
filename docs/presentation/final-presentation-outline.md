# Final Presentation Outline

## Slide 1: Dense But Fragile Baseline Layout

Use the constructive solution on `examples/realistic-improvement-instance.json` as the dense-but-bad example.

Suggested visual:
- draw the yard as a `9 x 6` grid
- show constructive placements for the overlapping time windows
- annotate that utilization is acceptable but congestion remains high

Reference constructive placements:
- `A -> (0, 0)`
- `B -> (7, 4)`
- `C -> (5, 0)`
- `D -> (1, 3)`
- `E -> (4, 3)`
- `F -> (0, 0)`

Narration:
- the baseline is feasible and compact
- feasibility alone is not enough because overlapping occupancy periods still create dense local interactions
- the resulting congestion penalty is `11.1110`

## Slide 2: Retrieval-Aware Improved Layout

Use the seed-`1` search solution on `examples/realistic-improvement-instance.json` as the improved example.

Reference search placements:
- `A -> (0, 0)`
- `B -> (7, 4)`
- `C -> (6, 0)`
- `D -> (4, 3)`
- `E -> (0, 4)`
- `F -> (0, 0)`

Narration:
- utilization stays the same at `0.5556`
- lateness stays at `0.0`
- retrieval-risk stays effectively flat at `4.2`
- congestion drops from `11.1110` to `10.7800`
- total objective improves from `-14.7554` to `-14.4244`

## Slide 3: Convergence Chart

Use the seeded run with `seed=1` and `iterations=20` on `examples/realistic-improvement-instance.json`.

Chart data:

| Iteration | Best Objective |
| --- | ---: |
| 1 | -14.7554 |
| 2 | -14.4244 |
| 3 | -14.4244 |
| 4 | -14.4244 |
| 5 | -14.4244 |
| 10 | -14.4244 |
| 15 | -14.4244 |
| 20 | -14.4244 |

Callout:
- the key improvement happens early at iteration `2`
- the improving move uses `congestion_cluster_k3` with `bounded_exact`
- later iterations preserve the stronger incumbent rather than drifting away from it

## Slide 4: System Architecture

Use this runtime flow:

1. Input loader parses development instances into internal models.
2. Feasibility engine rejects invalid placements.
3. Constructive solver produces the first feasible incumbent.
4. Local search applies destroy and repair neighborhoods.
5. Bounded exact repair handles small difficult neighborhoods.
6. Benchmark and CLI layers expose reproducible experiments and diagnostics.

Emphasize:
- feasibility first
- anytime best-incumbent preservation
- interpretable objective terms
- bounded exact repair instead of whole-instance exact solving

## Slide 5: Engineering Robustness And Reproducibility

Evidence to show:
- seeded local search and seeded benchmarks
- JSON benchmark artifacts with per-iteration history
- operator-level attempt, acceptance, and improvement totals
- wall-clock time-limit support for search and benchmark modes
- scripted workflow validation through `scripts/validate-documented-workflow.ps1`
- chart-ready artifact generation through `scripts/generate_chart_ready_artifacts.py`
- current green state with `38` passing tests in the documented workflow run

Speaker note:
- this project is designed to score well not only by producing improvements, but by making those improvements explainable and reproducible for final-round review