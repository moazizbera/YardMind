# Project Concept

## Positioning

YardMind is a retrieval-aware hybrid optimizer for OGC 2026. It targets the core competition challenge directly: place and schedule shipyard blocks efficiently without creating future operational bottlenecks.

The project is designed to score well across all judged dimensions:
- algorithm performance through fast feasible construction and iterative improvement
- technical report quality through interpretable objectives and clear ablations
- code quality through modular architecture, deterministic execution modes, and reproducible experiments

## Why This Direction

The team considered multiple framings for the competition idea:
- a safe, optimization-first solver direction
- a visually strong digital-twin framing
- an adaptive AI-flavored search story

YardMind was chosen as the primary direction because it offers the best balance of winning potential and implementation risk. It matches the official problem closely, supports strong leaderboard performance, and remains explainable enough for final-round review.

## Core Thesis

Dense packing alone is not a competitive strategy in this problem. A layout that looks efficient at placement time can become expensive later if urgent blocks are trapped behind lower-priority ones.

YardMind therefore optimizes for retrieval-aware efficiency:
- find a feasible solution quickly
- evaluate placements using downstream operational risk
- improve the incumbent with neighborhood search under runtime limits
- preserve the best feasible solution throughout the run

## Competitive Story

YardMind should be presented with two complementary messages:

1. Solver message
The system is a hybrid anytime optimizer combining constructive heuristics, destroy or repair search, and local exact repair on selected neighborhoods.

2. Demo message
The system behaves like a time-aware digital twin of the yard, showing why a slightly less dense placement can outperform a dense but fragile arrangement once retrieval pressure appears.

## Scope Boundaries

What YardMind should do:
- emphasize solver quality first
- use explainable objective terms
- keep a clean reproducible codebase for open-source release
- generate report-ready artifacts such as convergence traces and ablation tables

What YardMind should avoid:
- adding cosmetic AI branding without measurable gains
- over-investing in visualization before solver performance improves
- relying on a full exact model for whole-instance optimization unless runtime data supports it

## Near-Term Build Priorities

1. Align the parser and feasibility engine with the official competition format and constraints.
2. Strengthen local search so it reliably improves over the constructive baseline.
3. Add reproducible seeded benchmarking and operator diagnostics.
4. Prepare report artifacts that connect solver behavior to competition metrics.