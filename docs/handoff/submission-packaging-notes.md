# Submission Packaging Notes

## Purpose

Use this note when preparing a competition submission package for OGC 2026. The goal is to reduce avoidable submission mistakes and keep the open-source release in a presentable state.

For ready-to-paste project copy, demo links, and judge-facing asset references, see `docs/handoff/hackathon-submission-kit.md`.

## Pre-Submission Checks

- run the current validated test suite from a clean shell
- verify the CLI commands in the handoff status still work
- confirm the intended seed and time-limit settings for the submission run
- confirm any benchmark artifacts referenced in the report are reproducible from committed code

## Required Runtime Inputs

- official competition instance files once the parser is updated
- chosen seed or seed policy for reproducible runs
- chosen iteration count or time limit for search mode

## Recommended Command Checklist

Use commands of this shape before packaging:

```powershell
Set-Location "F:\Projects\Hackathons\YardMind"
$env:PYTHONPATH = "src"
pytest tests/test_loader_and_feasibility.py tests/test_local_search.py tests/test_benchmark.py tests/test_smoke.py
python -m yardmind.cli examples/sample-instance.json --mode inspect
python -m yardmind.cli examples/sample-instance.json --mode constructive
python -m yardmind.cli examples/sample-instance.json --mode search --iterations 6 --seed 11
python -m yardmind.cli examples/curated-improvement-instance.json --mode benchmark --runs 4 --iterations 12 --seed 7 --time-limit-seconds 0.05 --output artifacts/curated-improvement-benchmark.json
pwsh -File scripts/validate-documented-workflow.ps1
python scripts/generate_chart_ready_artifacts.py
```

Replace the example instance paths with official instances once the parser is updated.

## Packaging Checklist

- include source under `src/yardmind/`
- include dependency and environment information from `pyproject.toml`
- include the technical report and any referenced artifact paths
- include benchmark artifacts used to support ablation or convergence claims when allowed
- avoid including generated clutter that is not needed for reproduction

## Open-Source Readiness

- remove dead code and commented-out experiments before final packaging
- keep file names and module boundaries understandable to reviewers
- make sure the report terminology matches the actual code paths and CLI modes
- keep deterministic settings and benchmark commands visible in the README or handoff docs

## Known Current Gaps

- official-format parser is not implemented yet
- official submission command and output contract are not wired yet
- exact repair is currently a bounded in-process neighborhood search, not an external CP-SAT or MIP integration

See `docs/analysis/official-parser-readiness.md` for the current parser boundary and the first tasks to take when the competition schema arrives.

Until those gaps are closed, treat this note as a packaging discipline guide rather than a final submission recipe.