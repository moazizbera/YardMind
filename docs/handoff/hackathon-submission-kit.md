# Hackathon Submission Kit

## Project Name

YardMind

## One-Line Tagline

Retrieval-aware shipyard block planning that packs smarter and cuts future moves.

## Elevator Pitch

YardMind is a retrieval-aware hybrid optimizer for shipyard block packing and scheduling. Instead of only asking whether a block fits now, it evaluates whether that placement will create expensive retrieval conflicts later, then improves the plan with seeded search under runtime limits.

## Short Description

YardMind helps plan shipyard block placement as a space-time optimization problem, not just a packing problem. The system builds a feasible layout quickly, scores future blocking risk explicitly, and presents development and official-sample behavior through a judge-friendly frontend.

## Long Description

Shipyard planning is difficult because every placement decision affects future operations. A dense layout can look good in the moment but still become operationally expensive if it blocks later retrievals, creates congestion, or forces unnecessary reshuffling.

YardMind is built around retrieval-aware optimization. It first produces a feasible plan, then improves that plan with neighborhood search and targeted repair. The core design principle is that a placement should be judged by both current feasibility and downstream operational impact.

The project now includes:
- a Python solver pipeline with constructive, search, benchmark, and official-sample evaluation modes
- official OGC 2026 sample inspection, validation, constructive comparison, and portfolio-search support
- a React control-room frontend that visualizes yard layouts, search history, and delegated-versus-native official constructive behavior
- screenshot-ready judge mode and exported demo assets for submission materials

## Problem Statement

The challenge is not only to fit blocks into a yard. It is to fit them in a way that preserves future mobility. YardMind treats the yard as a time-evolving system and tries to reduce downstream retrieval disruption rather than maximizing short-term packing density alone.

## What Makes It Different

- Retrieval-aware scoring: future blocking risk is part of the optimization signal, not an afterthought.
- Feasibility first, improvement second: a reliable baseline is built quickly, then improved under time limits.
- Interpretable behavior: objective breakdowns, official comparison summaries, and search traces are exposed for judging and reporting.
- Demo-ready product surface: the project includes a frontend that makes solver behavior visible instead of relying only on raw logs.

## Key Features

- constructive baseline for fast feasible layouts
- seeded local-search improvement loop
- benchmark and comparison tooling
- official-sample constructive benchmarking between delegated and native heuristics
- browser presentation layer for layouts, metrics, and traces
- reproducible screenshot artifacts for the submission portal

## Tech Stack

- Python 3.13
- TypeScript
- React
- Vite
- PowerShell scripts for reproducible workflow checks
- pytest for regression and smoke validation

## Demo Flow For Judges

1. Open the YardMind control room and show the high-level metrics.
2. Compare the constructive baseline layout with the improved local-search layout.
3. Point to the search trace to show that the optimizer is actively improving candidates.
4. Show the official delegated-versus-native constructive comparison.
5. Switch to judge mode for a cleaner screenshot-oriented summary view.

## Recommended Links And Assets

- Repository: https://github.com/moazizbera/YardMind
- README: `README.md`
- Demo script: `docs/presentation/demo-script.md`
- Judge screenshot: `artifacts/demo/hackathon-frontend-judge.png`
- Full demo screenshot: `artifacts/demo/hackathon-frontend.png`
- Static demo artifact: `artifacts/demo/index.html`

## Commands To Regenerate Demo Assets

```powershell
Set-Location "F:\Projects\Hackathons\YardMind"
$env:PYTHONPATH = "src"
python -m yardmind.demo --instance examples/sample-instance.json --output artifacts/demo/index.html
npm --prefix web run build
```

For live frontend preview:

```powershell
Set-Location "F:\Projects\Hackathons\YardMind"
npm --prefix web run dev
```

Then open:
- `http://localhost:5173`
- `http://localhost:5173/?view=judge`

## Suggested Form Answers

### Project Summary

YardMind is a retrieval-aware optimizer for shipyard block planning that balances fast feasibility with lower downstream retrieval disruption. It combines constructive planning, improvement search, official-sample benchmarking, and a frontend that makes the optimization behavior visible for judges.

### Innovation

Most layout tools focus on whether a placement fits. YardMind also scores whether that placement will remain operationally efficient later. That retrieval-aware perspective is combined with an explainable search loop and a presentation layer that exposes objective deltas, search behavior, and official comparison outputs.

### Why It Matters

In shipyard operations, a layout that looks dense today can become expensive tomorrow if it creates congestion or forces avoidable rehandling. YardMind is designed to reduce that future disruption while still producing feasible plans quickly.

### Built With

Python, React, TypeScript, Vite, PowerShell, pytest.

## Judge Notes

- The current official path includes inspection, validation, delegated constructive, native constructive, and a first official portfolio search.
- The frontend is intended to make progress legible: layouts, metrics, and official comparison are visible without reading raw JSON.
- The repository is currently aligned for demo and documentation: generated clutter is ignored, screenshots are exported, and the README reflects the presentation workflow.
