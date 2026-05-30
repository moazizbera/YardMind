# Experiment Plan

## Objectives

Measure whether retrieval-aware optimization beats naive density-first packing.

## Current Baseline

The current baseline is a constructive heuristic that:
- sorts blocks by due time and priority
- enumerates feasible top-left placements on the yard grid
- scores each candidate using compactness, priority, edge distance, and local congestion
- keeps a full objective breakdown on the final solution state

This is still an early baseline, but it is strong enough to support ablations against future local-search variants.

## Current Search Variant

The first search variant now exists and:
- starts from the constructive solution
- removes a small high-risk cluster or an urgent time-window cluster
- repairs the partial solution by sampling from the top-ranked feasible constructive candidates under a fixed seed
- preserves the best feasible incumbent across iterations

This remains an early search pass, so the next experiments should focus on whether operator adaptation, larger neighborhoods, or local exact repair improve incumbent quality across seeded runs.

## Key Comparisons

1. constructive baseline vs constructive plus local search
2. density-only scoring vs retrieval-aware scoring
3. heuristic repair vs local exact repair
4. single-seed vs multi-seed runs

## Metrics

- incumbent objective value
- feasibility rate
- runtime to first feasible solution
- runtime to best-known solution
- relocation-risk proxy
- lateness proxy

## Ablation Plan

Run ablations that remove one feature at a time:
- no blocking-risk penalty
- no exact repair
- no adaptive operator selection
- no zone-based decomposition

## Output Artifacts

Store enough data to generate:
- convergence plots
- operator effectiveness tables
- runtime breakdown charts
- final leaderboard-oriented comparison tables

## Current Benchmark Support

The CLI now includes a lightweight benchmark mode that:
- runs constructive once per instance as the baseline reference
- runs search repeatedly across a deterministic seed range
- prints mean constructive score, mean search score, best search score, and improved-run count
- prints per-destroy and per-repair attempt, feasible, accepted, and improved totals
- can save the full benchmark summary as a JSON artifact for downstream analysis
- records per-iteration history including selected operators, candidate objective, incumbent objective, and acceptance or improvement flags
- can export chart-ready CSV files for run summaries, convergence traces, and operator totals

This is enough to guide early tuning and save repeatable artifacts, but the next step is richer convergence logging so benchmark runs can feed charts and ablations automatically.

Current note:
- on the sample instance, even state-aware best-of-top repair does not yet produce a strictly better incumbent under the tie-break-aware acceptance policy, so the next tuning step should focus on larger neighborhoods or stronger scoring differentiation
- a curated synthetic benchmark case is now stored in `examples/curated-improvement-instance.json` so improvements can be demonstrated reproducibly even while the sample instance remains flat
- a denser development benchmark case is now stored in `examples/realistic-improvement-instance.json` so improvements can be tracked beyond the smaller curated micro-case
- bounded exact repair is now available for small destroy neighborhoods, so the next experiment should isolate its contribution against `best_of_top`, `spread`, and `sampled_greedy`
- the benchmark suite now includes that direct ablation, and the bounded exact repair mix wins on the broader realistic development case
- `scripts/generate_chart_ready_artifacts.py` now regenerates the current report and presentation figure data from the benchmark pipeline
