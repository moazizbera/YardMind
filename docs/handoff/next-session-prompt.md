# Next Session Prompt

Paste the following into the next chat session after opening the YardMind folder in VS Code.

```text
Continue the YardMind project in F:\Projects\Hackathons\YardMind.

Before editing, read these files first:
- docs/handoff/current-status.md
- docs/handoff/checklist.md
- docs/implementation/roadmap.md
- docs/implementation/experiment-plan.md

Current known state:
- Python package scaffold exists and tests are passing.
- CLI supports inspect, constructive, search, and benchmark modes.
- The loader still uses a development JSON schema, but now exposes `--input-format` and fails clearly for the reserved `official` path.
- Feasibility checker handles yard bounds, time windows, space-time overlap, and minimum clearance.
- Constructive baseline enumerates feasible placements and scores them with a retrieval-aware heuristic.
- Local search includes multiple destroy and repair operators, adaptive weighting, bounded exact repair, and best-feasible-incumbent preservation.
- Benchmarking, JSON artifacts, chart-ready CSV exports, and documented workflow scripts are all in place.

Validated commands:
- Set-Location "F:\Projects\Hackathons\YardMind"
- $env:PYTHONPATH = "src"
- pytest
- python -m yardmind.cli examples/sample-instance.json --mode inspect
- python -m yardmind.cli examples/sample-instance.json --mode constructive
- python -m yardmind.cli examples/sample-instance.json --mode search --iterations 6 --seed 11
- python -m yardmind.cli examples/curated-improvement-instance.json --mode benchmark --runs 4 --iterations 12 --seed 7 --time-limit-seconds 0.05 --output artifacts/curated-improvement-benchmark.json
- python scripts/generate_chart_ready_artifacts.py
- .\scripts\validate-documented-workflow.ps1

Next implementation goals:
1. Add official-format parsing instead of the temporary development schema.
2. Finalize the problem statement interpretation once the official schema and scoring details are available.
3. Add more contest-faithful hard constraints such as access-lane or retrieval-path rules once the rules are confirmed.
4. Keep the focused tests green after each edit.

Work iteratively. Make the smallest grounded change, validate immediately, and update docs if behavior changes.
```