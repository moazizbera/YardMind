# Strategy Options

## Shortlisted Solver Families

### 1. Monolithic exact optimization
Pros:
- strong optimality guarantees on small instances
- easy to describe mathematically

Cons:
- likely too slow for full-size hidden instances
- high implementation risk under time limits

### 2. Pure constructive heuristics
Pros:
- fast and stable
- easy to debug

Cons:
- weak final solution quality
- limited adaptability on hard instances

### 3. Metaheuristic only
Pros:
- strong search capability
- flexible on hidden cases

Cons:
- can spend too long searching poor neighborhoods
- needs a reliable feasible baseline

### 4. Hybrid anytime optimization
Pros:
- fast initial feasibility
- scalable improvement loop
- strong engineering story
- good fit for runtime-constrained evaluation

Cons:
- more moving parts
- requires careful time-budgeting

## Chosen Direction

YardMind follows a hybrid anytime approach:
- greedy feasible construction first
- adaptive large neighborhood search second
- local exact repair on selected neighborhoods
- best-so-far incumbent preserved throughout runtime

## Why This Direction

This design gives the best balance between:
- robustness
- leaderboard performance potential
- technical originality
- final presentation quality
