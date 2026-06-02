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

## Hidden-Case Stress Plan

The public proof and quality instances are now strong enough for a demo, but they are too small to justify risky last-minute solver rewrites. The next competitive step is a hidden-case stress program that tests whether the current official search fails under larger timing and bay-coupling patterns before any new algorithm branch is merged.

### Stress Families

1. tight-window cascade
	- blocks share overlapping release and due windows
	- one early bad bay assignment should force tardiness onto multiple downstream blocks
	- goal: test whether order perturbation alone is enough

2. overloaded preferred bay
	- many blocks strongly prefer the same bay while alternatives remain feasible but expensive
	- goal: test whether the search can trade preferred-bay loss against bay-load balance correctly

3. asymmetric bay geometry
	- bays differ enough in width and height that feasible orientation sets diverge sharply
	- goal: punish heuristics that treat bays as nearly interchangeable

4. long occupancy blockers
	- a few long-duration blocks occupy prime bays while shorter urgent blocks arrive later
	- goal: expose timing-placement interactions that simple order changes may miss

5. conflict clusters
	- 3-5 blocks overlap in time and compete for the same neighborhood of bays
	- goal: test whether current local neighborhoods are large enough to escape local minima

### Required Metrics

- official objective mean and best
- feasible runs over repeated seeds or repeated benchmark invocations
- runtime mean and worst-case runtime
- delta versus delegated baseline
- delta versus current official search baseline

### Acceptance Gate For New Solver Work

Do not keep a new official-search branch unless it meets at least one of these conditions:
- improves the public proof objective without hurting the public quality case
- improves at least one hidden-case family consistently across repeated runs
- preserves feasibility while reducing worst-case hidden-case runtime

### Suggested Artifact Set

Create one internal instance per stress family and store benchmark outputs under `artifacts/report/hidden_case_*` so the results can be compared without mixing them into the public demo narrative.

### Current Recommendation

The current official search should remain the shipped demo solver until a hidden-case stress family shows a repeatable failure mode that the new branch clearly fixes. This keeps the demo credible and prevents late complexity from replacing measured evidence with speculation.

First runnable template:
- `examples/official-hidden-overloaded-bay-instance.json` encodes an overloaded preferred-bay stress case where several early blocks strongly prefer the same bay, while later blocks still retain feasible but costly alternatives.
- `examples/official-hidden-tight-window-instance.json` encodes a tight-window cascade where early long-duration assignments can force downstream tardiness if bay-time choices are made greedily.

First measured internal evidence:
- overloaded preferred-bay case: delegated mean objective `30.0`, official search mean objective `15.0`, mean delta `-15.0`, search feasible in `6/6` runs
- tight-window cascade case: delegated mean objective `38.0`, official search mean objective `18.0`, mean delta `-20.0`, search feasible in `6/6` runs

Interpretation:
- the current official search is already doing meaningful work beyond the public proof and quality cases
- hidden-case benchmarking now supports the claim that the shipped solver handles both bay-preference overload and timing-pressure cascades without introducing unvalidated last-minute algorithm branches
