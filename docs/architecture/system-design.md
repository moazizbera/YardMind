# System Design

## High-Level Modules

1. Instance Loader
Parses official challenge inputs into validated internal models.

2. Domain Model
Represents blocks, yard geometry, occupancy intervals, and placements.

3. Feasibility Engine
Checks all hard constraints before a move is accepted.

4. Constructive Solver
Builds a valid initial solution quickly.

5. Improvement Engine
Runs neighborhood search to improve incumbent quality.

6. Local Exact Repair
Solves a reduced subproblem for selected blocks or zones.

7. Evaluation and Logging
Tracks objective components, runtime, and search diagnostics.

## Concrete Runtime Architecture

### 1. Input Layer
- parse official challenge instances into internal models
- validate required fields early and fail with explicit format errors
- normalize dimensions, time data, and yard metadata before solving

### 2. Domain Layer
- represent blocks, placements, yard geometry, and solution state
- store both total objective value and interpretable component breakdowns
- keep the domain model lightweight so search operators can clone and mutate state cheaply

### 3. Constraint Layer
- centralize all hard-feasibility checks in one engine
- evaluate placement validity incrementally against the current partial solution
- support later extension for access lanes, retrieval paths, zoning, and resource rules

### 4. Constructive Layer
- generate a feasible incumbent quickly
- rank candidate placements using retrieval-aware heuristics
- act as both the baseline solver and the fallback repair primitive

### 5. Search Layer
- maintain the incumbent and best-so-far feasible solution separately
- apply destroy operators to expose promising neighborhoods
- apply repair operators to rebuild feasibility
- track operator outcomes so later adaptive weighting can be added without changing the solver boundary

### 6. Exact Repair Layer
- extract a bounded neighborhood around difficult blocks or congested zones
- solve a reduced model with CP-SAT or MIP
- return control to the heuristic search with a repaired incumbent

### 7. Experiment Layer
- run seeded comparisons across solver variants
- collect objective values, runtime, and operator effectiveness
- emit report-ready data for convergence plots and ablation tables

## Solver Loop

1. Load instance.
2. Build feasible initial solution.
3. Score conflict hotspots.
4. Select neighborhood destroy and repair operators.
5. Apply local repair.
6. Accept or reject move.
7. Repeat until time budget is exhausted.
8. Return best feasible solution.

## Current Implementation Mapping

- input layer: `src/yardmind/loader.py`
- domain layer: `src/yardmind/models.py`, `src/yardmind/solver/state.py`
- constraint layer: `src/yardmind/solver/feasibility.py`
- constructive layer: `src/yardmind/solver/constructive.py`
- search layer: `src/yardmind/solver/local_search.py`
- command-line entrypoint: `src/yardmind/cli.py`

## Design Decisions

### Feasibility First
The solver should never sacrifice reliability for speculative objective gains. Every operator must either preserve feasibility directly or rebuild it before a candidate can be accepted.

### Anytime Operation
The solver architecture is designed so it can stop at any time and still return the best feasible incumbent found so far. This is important for leaderboard robustness and final-round reproducibility.

### Interpretable Objectives
Objective values should remain decomposable into terms that can be explained in the technical report. This is necessary because final-round evaluation is not based on score alone.

### Bounded Complexity
Whole-instance exact optimization is deliberately avoided in the main loop. Expensive exact models should be limited to small subproblems where they can improve quality without destroying runtime predictability.

## Engineering Requirements

- deterministic mode for debugging
- multi-seed support for experimentation
- structured logging for report figures
- strict timeout handling
- no dependence on external services during execution
