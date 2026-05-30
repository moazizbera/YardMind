# Continuation Checklist

## Canonical Build Order

Use this file as the single execution checklist for implementation planning. Do not start a later phase until the current phase has a stable validation path, unless the later work is required to unblock it.

Working rule:
- finish one phase with tests and CLI validation green
- update docs for behavior changes before moving on
- avoid speculative features that do not improve score, reproducibility, or final-round clarity

## Session Restart Checklist

- [ ] Open the project folder in VS Code: `F:\Projects\Hackathons\YardMind`
- [ ] Open a new chat from the same folder workspace
- [ ] Read `docs/handoff/current-status.md`
- [ ] Read `docs/handoff/next-session-prompt.md`
- [ ] Read this checklist before choosing the next task
- [ ] Run the current validation commands before making edits

## Phase 1: Baseline Search Layer

Goal:
Reach a stable baseline with constructive solve, first search operators, and interpretable objective output.

- [x] Add CLI output for objective breakdown terms
- [x] Add at least one contest-inspired hard constraint beyond overlap and bounds
- [x] Implement the first destroy operator
- [x] Implement the second destroy operator
- [x] Implement the first repair operator
- [x] Add a local search loop that preserves the best feasible incumbent
- [x] Add reproducible search controls for iterations and seed
- [x] Add tests for destroy or repair behavior
- [x] Document the new search loop in `docs/implementation/roadmap.md`

Phase exit criteria:
- [x] `inspect`, `constructive`, and `search` CLI modes work
- [x] loader, feasibility, local-search, and smoke tests are green

## Phase 2: Official Problem Alignment

Goal:
Replace placeholder assumptions with contest-faithful input handling, constraints, and objective terms.

- [ ] Replace temporary JSON schema with the official OGC 2026 format
- [x] Add parser validation for official required fields
- [ ] Expand feasibility rules to match official constraints
- [ ] Add access-lane or retrieval-path hard constraints if required by the official problem
- [ ] Map objective components more closely to the contest metric
- [ ] Add tests that cover official-format parsing and new hard constraints

Phase exit criteria:
- [x] sample or synthetic official-format instances load cleanly
- [ ] feasibility coverage matches the current competition interpretation
- [ ] objective terms reflect the official evaluation logic as closely as possible

## Phase 3: Search Competitiveness

Goal:
Make `search` beat `constructive` consistently on controlled runs.

- [x] Add at least one more repair operator
- [x] Add operator effectiveness tracking
- [x] Add adaptive operator weighting or selection
- [x] Add a stronger acceptance policy than improvement-only if benchmarking justifies it
- [x] Add larger or more targeted neighborhoods
- [x] Add tests for operator selection and incumbent preservation

Phase exit criteria:
- [x] `search` shows measurable gains over `constructive` on curated benchmark cases
- [x] seeded runs are reproducible
- [x] search diagnostics are visible enough to debug why gains happen or fail

## Phase 4: Benchmarking And Reproducibility

Goal:
Turn solver changes into measurable evidence instead of intuition.

- [x] Add a benchmark runner for repeated seeded experiments
- [x] Add experiment logging for convergence and ablation tables
- [x] Add multi-seed batch execution support
- [x] Add timeout-safe solve control
- [x] Add result summaries that compare constructive versus search

Phase exit criteria:
- [x] repeated runs can be executed with fixed seeds and saved outputs
- [x] convergence and ablation artifacts can be generated from logs
- [x] runtime budgets are enforced cleanly

## Phase 5: Exact Repair

Goal:
Use exact optimization only where it is likely to pay off.

- [x] Formulate a bounded exact local repair model over a truncated candidate neighborhood
- [x] Limit neighborhood size for predictable runtime
- [x] Integrate exact repair as an optional operator inside search
- [x] Compare exact repair against heuristic repair in ablations

Phase exit criteria:
- [x] exact repair improves at least some hard neighborhoods without destabilizing runtime
- [x] fallback behavior remains feasible when exact repair is skipped or times out

## Phase 6: Competition Hardening

Goal:
Prepare for server evaluation, open-source release, and final-round review.

- [x] Add submission packaging notes
- [x] Clean up CLI and repo-level usage documentation
- [x] Verify deterministic and reproducible run instructions
- [x] Review code quality for public release
- [x] Prepare a final validation checklist for submission time

Phase exit criteria:
- [x] a fresh user can run the solver from documented steps
- [x] final-round code disclosure would be acceptable without cleanup panic
- [x] submission process is scripted or documented enough to avoid mistakes

## Phase 7: Technical Report

Goal:
Build the evidence and narrative needed for finalist judging.

- [ ] Finalize the problem statement interpretation
- [x] Document the baseline constructive heuristic
- [x] Document the search operators and acceptance logic
- [x] Add ablation results
- [x] Add runtime analysis
- [x] Add a worked example showing retrieval-aware placement decisions

Phase exit criteria:
- [ ] methodology is defensible from problem framing through experiments
- [x] charts and tables are generated from reproducible logs
- [x] the report explains not only what worked, but why

## Phase 8: Final Presentation

Goal:
Turn the technical story into a convincing demo and judging narrative.

- [x] Prepare one dense-but-bad layout example
- [x] Prepare one retrieval-aware improved layout example
- [x] Prepare a convergence chart
- [x] Prepare a system architecture slide
- [x] Prepare one slide on engineering robustness and reproducibility

Phase exit criteria:
- [x] demo examples clearly show why retrieval-aware optimization matters
- [x] slides align with the technical report and actual solver behavior
- [x] the presentation emphasizes score, rigor, and engineering discipline

## Current Recommended Next Work

- [x] Achieve measurable `search` gains over `constructive` on broader realistic cases beyond the curated benchmark
- [x] Start official-format parser work as soon as the competition schema is available
- [ ] Finalize the problem statement interpretation once the official schema and scoring details are available
- [x] Turn benchmark artifacts into chart-ready figures for the report and presentation