# Current Status

## Project Summary

YardMind is a Python-based optimization project for OGC 2026 focused on retrieval-aware shipyard block packing and scheduling. The current codebase is a scaffold plus a working baseline execution path.

## What Exists Today

### Repository Structure
- `src/yardmind/` package code
- `src/yardmind/solver/` solver modules
- `src/yardmind/solver/local_search.py` local search operators and loop
- `examples/sample-instance.json` local development instance
- `tests/` smoke and loader or feasibility tests
- `docs/` analysis, architecture, implementation, handoff, report, and presentation material

### Working Code Paths
- CLI entrypoint exists in `src/yardmind/cli.py`
- benchmark runner exists in `src/yardmind/benchmark.py`
- JSON instance loader exists in `src/yardmind/loader.py`
- feasibility checking exists in `src/yardmind/solver/feasibility.py`
- constructive baseline exists in `src/yardmind/solver/constructive.py`
- local search exists in `src/yardmind/solver/local_search.py`
- objective scoring exists in `src/yardmind/solver/scoring.py`

### Current Solver Behavior
- loads a temporary JSON instance schema
- exposes an explicit `--input-format` boundary so development and official parsing paths are separated
- loads official OGC 2026 JSON instances for inspection, validates required top-level fields, and preserves official bay and weight metadata in memory
- validates official solution JSON files against the released baseline `utils.check_feasibility(...)` path during official inspect mode
- runs the released official baseline greedy algorithm for `--input-format official --mode constructive`, validates its returned operations in-repo, and can persist the official solution JSON through `--output`
- official constructive CLI now also exposes an explicit `--official-constructive-variant delegated|native` switch so the first YardMind-native heuristic can be exercised without using only comparison scripts
- official search CLI now runs an official portfolio plus incumbent-refinement loop: it evaluates the delegated baseline constructive path plus multiple YardMind-native constructive orderings, then repeatedly rebuilds perturbation neighborhoods around the current best feasible incumbent using nearby order changes, bay-bias perturbations, neighbor-aware incumbent repair, objective-driven rebuilds, reinsertion candidates, and partial reconstruction before returning the best feasible objective and optionally persisting the chosen operations JSON through `--output`
- official search now also includes a dedicated direct incumbent repair family that removes and reinserts 1-2 high-impact blocks against fixed incumbent assignments, and can escalate to 3-block dense-cluster repairs when overlap-cluster and bay-neighborhood pressure is strong before escalating to broader reconstruction neighborhoods
- official partial reconstruction now also supports opt-in 4-block focus neighborhoods for denser incumbent clusters, while the default search path keeps the smaller neighborhood cap for stability on tight time budgets
- official benchmark CLI now compares delegated-versus-native constructive runs on official instances, printing feasibility, objective, and runtime side by side and optionally writing the JSON summary through `--output`
- the native official heuristic now scores urgency-weighted future bay scarcity plus future window overlap, preserving bays that later, tighter-slack blocks are more dependent on and avoiding those bays during the windows they are likely to need when the current block has other feasible options
- includes `scripts/generate_official_baseline_artifact.py` to regenerate and validate a reproducible official baseline artifact under `artifacts/official/`
- includes `scripts/compare_official_constructive_variants.py` to write delegated-versus-native official constructive artifacts and a summary with runtime plus objective data under `artifacts/official/comparison/`
- includes a lightweight presentation layer via `python -m yardmind.demo`, which generates a browser-viewable static demo page under `artifacts/demo/index.html` for the development solver path plus the current official delegated-versus-native constructive comparison summary and official bay placement snapshots
- includes `scripts/open-demo.ps1` as the one-command demo launcher; it rebuilds `artifacts/demo/index.html` with `PYTHONPATH=src` and opens the page unless `-NoOpen` is supplied
- includes `scripts/open-react-demo.ps1`, `scripts/open-judge-pack.ps1`, and `scripts/open-submission-rehearsal.ps1` with an optional `-Intro` switch so the animated splash can play before a direct product surface such as the judge sequence or replay stage
- validates block placement against yard bounds, time windows, space-time overlap, and optional yard-level minimum clearance
- official regression fixtures now cover released-checker failure modes for Stage 1, Stage 2, Stage 3, and Stage 5; inspection of the released checker shows ordinary overlap collisions are classified at Stage 2 before Stage 4, so a standalone Stage 4 fixture is not currently treated as a blocker
- constructs a feasible solution by enumerating candidate coordinates
- scores candidates using compactness, edge distance, urgency, priority, and local congestion
- prints a detailed objective breakdown for constructive and search solves
- runs a seeded local-search layer using high-risk and congestion-focused destroy operators, best-of-top and spread repair operators, and best-feasible-incumbent preservation
- uses larger 3-block destroy neighborhoods and adaptive operator weighting inside the seeded local-search loop
- runs seeded benchmark comparisons between constructive and search modes with per-destroy and per-repair attempt and improvement totals
- can write benchmark summaries to JSON artifacts for later ablation and convergence analysis
- benchmark artifacts now include per-iteration convergence history with accepted and improved move flags
- acceptance now uses a deterministic tie-break on objective breakdown terms instead of accepting every equal-score candidate
- best-of-top repair now evaluates top feasible reinsertion candidates by resulting state quality before placing them
- bounded exact repair now enumerates a capped top-candidate neighborhood for small destroy sets and falls back to heuristic repair on larger neighborhoods or local timeout
- `examples/curated-improvement-instance.json` exists as a small reproducible case where seeded search can beat the constructive baseline
- `examples/realistic-improvement-instance.json` exists as a denser development case where seeded search improves over constructive across repeated runs
- benchmark ablation coverage now includes a direct comparison showing the bounded exact repair mix outperforms the heuristic-only repair mix on the broader realistic development case
- search and benchmark modes now support an optional wall-clock time limit for timeout-safe execution
- the main technical report now lives at `docs/report/technical-report.md`, while the older draft remains at `docs/report/technical-report-outline.md`
- the final presentation outline now includes dense-baseline and improved-layout examples, a convergence trace, a system architecture slide, and an engineering-robustness slide
- chart-ready CSV and JSON artifacts for the report and presentation can now be regenerated with `python scripts/generate_chart_ready_artifacts.py`
- returns a feasible baseline solution and a feasible local-search solution on the sample instance

## Validation Status

The following commands were last verified successfully:

```powershell
Set-Location "F:\Projects\Hackathons\YardMind"
$env:PYTHONPATH = "src"
pytest tests/test_loader_and_feasibility.py tests/test_smoke.py
pytest tests/test_local_search.py tests/test_smoke.py
pytest tests/test_benchmark.py tests/test_smoke.py
pytest tests/test_loader_and_feasibility.py tests/test_local_search.py tests/test_smoke.py
python -m yardmind.cli examples/sample-instance.json --mode inspect
python -m yardmind.cli examples/official-sample-instance.json --input-format official --mode inspect
python -m yardmind.cli examples/official-sample-instance.json --input-format official --mode inspect --solution examples/official-sample-solution.json
python -m yardmind.cli examples/official-sample-instance.json --input-format official --mode constructive --time-limit-seconds 5
python -m yardmind.cli examples/official-sample-instance.json --input-format official --mode constructive --official-constructive-variant native --time-limit-seconds 5
python -m yardmind.cli examples/official-sample-instance.json --input-format official --mode constructive --time-limit-seconds 5 --output artifacts/official-sample-solution.json
python -m yardmind.cli examples/official-sample-instance.json --input-format official --mode search --time-limit-seconds 5 --output artifacts/official-search-solution.json
python -m yardmind.cli examples/official-sample-instance.json --input-format official --mode benchmark --time-limit-seconds 5 --output artifacts/official-benchmark-summary.json
python scripts/generate_official_baseline_artifact.py
python scripts/compare_official_constructive_variants.py
python -m yardmind.cli examples/sample-instance.json --mode constructive
python -m yardmind.cli examples/sample-instance.json --mode search
python -m yardmind.cli examples/sample-instance.json --mode search --iterations 5 --seed 11
python -m yardmind.cli examples/sample-instance.json --mode benchmark --runs 2 --iterations 4 --seed 3
python -m yardmind.cli examples/sample-instance.json --mode benchmark --runs 2 --iterations 4 --seed 3 --output artifacts/benchmark-sample.json
python -m yardmind.cli examples/curated-improvement-instance.json --mode benchmark --runs 4 --iterations 12 --seed 7 --time-limit-seconds 0.05 --output artifacts/curated-improvement-benchmark.json
python -m yardmind.cli examples/realistic-improvement-instance.json --mode benchmark --runs 6 --iterations 20 --seed 0
.\scripts\validate-documented-workflow.ps1
python scripts/generate_chart_ready_artifacts.py
```

## Current Limitations

- development solve modes still use the temporary rectangle-based schema and objective logic
- official OGC 2026 loading currently supports inspection, feasibility validation, delegated constructive, native constructive comparison benchmarking, and a bounded incumbent-refinement search over the current constructive and perturbation families, including neighbor-aware incumbent repair; a true direct assignment destroy/repair neighborhood-search layer is still missing
- the repo now also includes a first YardMind-native official constructive heuristic exposed through the CLI for comparison on the public official sample, but it should still be treated as an early baseline rather than the main official solver path
- pure Stage 4 official collision coverage remains unverified as a standalone checker outcome; the released checker's Stage 2 entry logic already catches ordinary same-bay overlap collisions before Stage 4, so any future Stage 4 fixture needs to demonstrate behavior not already dominated by entry or exit feasibility
- no yard zoning constraints beyond simple metadata
- no access-lane or retrieval-path hard constraints yet
- local search is still heuristic and lightweight; it does not yet use reheating or external exact-solver backends such as CP-SAT
- exact repair is currently bounded to small top-candidate neighborhoods rather than an official CP-SAT or MIP model
- benchmark support now writes structured JSON artifacts with per-iteration history; broader development-case improvements now exist, but the sample instance still stays flat and official-format realism is still missing

## Most Important Next Step

Extend the current official incumbent-refinement loop into a true official improvement loop that perturbs and repairs incumbent official assignments directly instead of repeatedly rebuilding them through constructive reruns.