# Technical Report Draft

## 1. Introduction

YardMind targets the OGC 2026 shipyard block placement problem as a coupled spatial and temporal optimization task. A block should not only fit on the yard at its arrival time, but should also remain retrievable later without creating unnecessary congestion or rehandling pressure.

The project therefore treats retrieval awareness as a first-class objective. The solver first constructs a feasible plan quickly, then improves that plan with seeded neighborhood search and bounded exact repair on small subproblems. The current prototype is designed to be explainable, reproducible, and safe to stop early with the best feasible incumbent still available.

## 2. Problem Definition

### 2.1 Current Working Interpretation

Until the official OGC 2026 format is wired into the parser, the implementation uses a development schema with:
- yard width and height
- optional yard-level minimum clearance
- block dimensions
- release times and due times
- block priorities

The current hard constraints enforced by the feasibility engine are:
- non-negative coordinates
- yard-bound containment
- valid time windows
- space-time non-overlap
- optional minimum clearance between time-overlapping blocks

### 2.2 Objective Interpretation

The current objective is a proxy objective intended to reflect retrieval-aware quality rather than the final official contest score. The total score is:

`area_utilization - lateness_penalty - retrieval_risk_penalty - congestion_penalty`

This decomposition is important for final-round explainability. Even when total score differences are small, the breakdown shows whether a move helped by reducing congestion, moving blocks toward easier retrieval positions, or increasing packing efficiency.

### 2.3 Computational Challenges

The main difficulty is that dense placements can look good locally while causing downstream retrieval trouble. This creates a search landscape where feasibility alone is not enough and pure density-first packing can stall on layouts that are hard to operate later.

## 3. Methodology

### 3.1 Baseline Constructive Heuristic

The constructive solver processes blocks in ascending due time and descending priority. For each block, it enumerates all feasible top-left coordinates in the yard grid and scores each candidate before selecting the highest-ranked placement.

The candidate score combines:
- a small priority bonus
- an early-due bonus
- a compactness bonus that mildly prefers lower rows
- an edge-distance penalty as a retrieval-risk proxy
- a local-density penalty as a congestion proxy

This constructive layer serves three roles at once: it provides the baseline solution, it defines the candidate-ranking logic used by repair operators, and it supplies a reliable feasibility-first fallback whenever a more aggressive neighborhood move fails.

### 3.2 Neighborhood Search Design

The local-search layer starts from the constructive incumbent and repeatedly applies one destroy operator and one repair operator.

Current destroy operators:
- `high_risk_cluster`
- `congestion_cluster`
- 3-block variants of both operators
- `global_restart`

Current repair operators:
- `sampled_greedy`
- `best_of_top`
- `spread`
- `bounded_exact`

The search loop keeps the incumbent and the best-so-far feasible solution separate. This makes the solver anytime-safe: even if an accepted move is only locally useful, the solver still returns the best feasible state observed during the run.

### 3.3 Acceptance Logic

Acceptance is not based on total objective alone. Candidates are compared lexicographically using:
- total objective value
- lower congestion penalty
- lower retrieval-risk penalty
- lower lateness penalty
- higher area utilization

This tie-break avoids the earlier failure mode where equal-score candidates were accepted without proving that the move actually improved the more operationally meaningful objective terms.

### 3.4 Bounded Exact Repair

The current exact repair layer is intentionally local rather than global. When the removed neighborhood is small enough, the `bounded_exact` operator enumerates a capped combination of top-ranked feasible reinsertion candidates and selects the best resulting state. If the neighborhood is too large, or if the local search hits its per-repair timeout, the operator falls back to heuristic repair.

This keeps exact repair useful without making runtime unpredictable.

### 3.5 Runtime Control And Reproducibility

Search runs are seeded, benchmark runs cover deterministic seed ranges, and CLI search and benchmark modes accept an optional wall-clock time limit. The repository also includes `scripts/validate-documented-workflow.ps1`, which executes the documented workflow end to end from tests through benchmark artifact generation.

## 4. Implementation

### 4.1 Software Structure

The current implementation is split into:
- loader and domain models
- feasibility engine
- constructive solver
- local-search solver and operators
- benchmark runner and JSON artifact writer
- CLI entrypoint

This separation keeps feasibility logic centralized while allowing operators and scoring logic to evolve independently.

### 4.2 Data And Diagnostics

Each solution state stores both total objective value and the full objective breakdown. Search diagnostics retain:
- per-iteration history
- destroy and repair operator attempt counts
- feasible, accepted, and improved counts
- adaptive operator weights

These diagnostics support both debugging and report generation.

## 5. Experiments

### 5.1 Benchmark Surfaces

The current development benchmark surfaces are:
- `examples/sample-instance.json` as a regression case where search remains flat
- `examples/curated-improvement-instance.json` as a small reproducible improvement case
- `examples/realistic-improvement-instance.json` as a denser development case where search improvements are more substantial

### 5.2 Exact-Repair Ablation

The strongest current ablation is on `examples/realistic-improvement-instance.json` with 6 seeded runs and 20 iterations per run.

| Variant | Mean Search Objective | Best Search Objective | Improved Runs | Runtime (6-run batch) |
| --- | ---: | ---: | ---: | ---: |
| Constructive baseline | -14.7554 | -14.7554 | 0/6 | n/a |
| Search with heuristic-only repairs | -14.5005 | -14.4244 | 6/6 | 0.9496 s |
| Search with bounded exact repair | -14.4385 | -14.4244 | 6/6 | 1.5429 s |

Interpretation:
- heuristic search already improves clearly over constructive on this denser case
- bounded exact repair improves the mean search objective further by about `0.0620`
- the bounded exact mix pays a runtime premium, but it does so while preserving deterministic behavior and feasibility

### 5.3 Runtime Analysis

The current runtime evidence is intentionally lightweight and development-oriented. On the realistic case above, bounded exact repair increases the 6-run batch runtime from `0.9496 s` to `1.5429 s`, or roughly `1.62x` the heuristic-only runtime. That overhead is acceptable at the current scale because it produces a measurable mean-quality improvement while remaining within short benchmark budgets.

This is not yet a competition-grade runtime analysis. Official-format instances and larger hidden cases will be needed before stronger runtime claims are justified.

## 6. Results And Worked Example

### 6.1 Quantitative Summary

Current validated results support four conclusions:
- the constructive baseline is stable and feasible
- search gains are reproducible on curated and broader realistic development cases
- bounded exact repair is beneficial on the realistic development case
- the sample instance is still too shallow to reveal meaningful search gains, which makes it useful as a regression case but not as a persuasive performance case

### 6.2 Worked Example

On `examples/realistic-improvement-instance.json` with seed `1` and 20 iterations, the constructive baseline scores `-14.7554` while search improves to `-14.4244`.

Constructive placements:
- `A -> (0, 0)`
- `B -> (7, 4)`
- `C -> (5, 0)`
- `D -> (1, 3)`
- `E -> (4, 3)`
- `F -> (0, 0)`

Search placements:
- `A -> (0, 0)`
- `B -> (7, 4)`
- `C -> (6, 0)`
- `D -> (4, 3)`
- `E -> (0, 4)`
- `F -> (0, 0)`

The improvement does not come from area utilization or lateness, which remain unchanged. It comes from lowering the congestion penalty from `11.1110` to `10.7800` while keeping the retrieval-risk term effectively flat. This is the intended retrieval-aware behavior: the search phase is not merely repacking blocks differently, it is reducing future interference among overlapping occupancy intervals.

## 7. Limitations And Conclusion

The current prototype is still limited by three major gaps:
- the parser still uses a development schema rather than the official OGC 2026 format
- the objective is still a proxy objective rather than the final contest metric
- exact repair is bounded and in-process rather than backed by CP-SAT or MIP

Even with those limits, the current system already demonstrates the intended engineering shape for a competition solver: feasibility-first construction, reproducible search, interpretable objective terms, benchmark artifacts, and a bounded exact-repair mechanism that improves some difficult neighborhoods without destabilizing the run.

The next technical priority is official-format alignment. The reporting pipeline already produces chart-ready convergence and ablation outputs; the remaining reporting work is to turn those generated artifacts into final polished figures once the official problem interpretation is fixed.
