# Implementation Roadmap

## Phase 1: Foundation
- replace the temporary JSON schema with the official contest format
- extend feasibility checks with official hard constraints
- upgrade the baseline constructive solver beyond row packing
- keep CLI commands for inspect and constructive solve working on every change

## Phase 2: Scoring
- break objective into interpretable components
- measure congestion, blocking risk, and lateness proxies
- add logging for each objective term

Status:
- constructive and search CLI paths now print area utilization, lateness, retrieval-risk, and congestion terms

## Phase 3: Search
- implement destroy operators
- implement repair operators
- add adaptive operator weighting
- add acceptance policy and reheating strategy if needed

Status:
- first destroy operator: high-risk cluster removal
- second destroy operator: congestion-cluster removal
- larger neighborhoods: 3-block variants for both destroy families
- first repair operator: best-of-top reinsertion using resulting state quality over the top-ranked constructive candidates
- second repair operator: spread-biased reinsertion that prefers lower clustering among top-ranked candidates
- adaptive operator selection now biases destroy and repair choices by accepted or improved outcomes
- first local search loop: iterative destroy or repair search that keeps the best feasible incumbent
- acceptance now uses a breakdown-aware tie-break instead of accepting every equal-score candidate
- CLI now exposes `--iterations` and `--seed` for reproducible search experiments

## Phase 4: Exact Repair
- formulate local subproblem for CP-SAT or MIP
- constrain neighborhood size for predictable runtime
- compare exact repair against heuristic repair

## Phase 5: Competition Hardening
- timeout-safe execution
- reproducible runs from seeds
- benchmark harness
- submission checklist

Status:
- benchmark CLI mode now compares constructive and search across a seeded run range
- search and benchmark CLI paths now support an optional time limit for timeout-safe execution
