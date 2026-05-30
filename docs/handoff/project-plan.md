# Project Plan

## Goal

Build a competitive anytime hybrid optimizer for OGC 2026 that combines fast feasibility, retrieval-aware scoring, neighborhood search, and local exact repair.

## Strategic Plan

### Stage 1: Strong Baseline
- keep parser, feasibility, and constructive path stable
- improve objective transparency and diagnostics
- make the baseline clearly better than naive packing

### Stage 2: First Search Layer
- implement one destroy operator
- implement one repair operator
- add a loop that accepts improvements and stores the best incumbent
- add targeted tests around search behavior

### Stage 3: Adaptive Search
- add multiple destroy and repair operators
- track operator effectiveness
- bias search toward successful neighborhoods

### Stage 4: Exact Repair
- define a bounded neighborhood repair model
- use CP-SAT or MIP only for local repair
- compare exact repair versus heuristic repair in ablations

### Stage 5: Competition Hardening
- switch to official input format
- map objective terms to the contest metric as closely as possible
- add benchmark scripts, seed control, and timeout handling
- prepare report tables and presentation visuals from experiment logs

## Success Criteria

- all edited slices keep focused tests green
- CLI remains usable for inspect and constructive runs
- each new optimization layer improves or clarifies the baseline
- docs stay current enough that a fresh session can resume with minimal overhead