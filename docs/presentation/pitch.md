# Pitch

## One-Line Pitch

YardMind is a retrieval-aware hybrid optimizer that packs shipyard blocks efficiently without creating expensive future moves.

## 30-Second Version

YardMind treats the shipyard as a time-evolving system rather than a static packing board. It first builds a feasible plan quickly, then improves that plan with neighborhood search and local exact repair. The key idea is retrieval-aware placement: a block is evaluated not only by whether it fits now, but by whether it will block future operations later.

The current prototype already exposes interpretable objective terms and reproducible seeded search runs, which supports both leaderboard tuning and final-round reporting.

## Key Talking Points

- feasibility first, improvement second
- packing and scheduling optimized together
- retrieval-risk is part of the score, not an afterthought
- local exact repair improves difficult neighborhoods without solving the full instance exactly
- anytime behavior makes the solver robust under runtime limits

## Judge Hooks

- official proof is visible: stage, replay, runtime, and objective terms are shown instead of hidden behind a single score
- measurable lift is explicit: the demo shows search lift and official delta versus the delegated baseline
- the engineering is auditable: guided judge flow, equation surfaces, and on-demand trace make the system feel reliable under scrutiny

## Demo Narrative

1. Show a dense but fragile layout.
2. Show how future retrieval creates cascading conflicts.
3. Show YardMind choosing a slightly different placement with lower downstream disruption.
4. Show convergence of objective value over time.
