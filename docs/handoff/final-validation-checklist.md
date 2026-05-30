# Final Validation Checklist

Use this list immediately before submission packaging or milestone handoff.

## Code Validation

- run the full test suite
- run inspect, constructive, search, and benchmark CLI modes from a clean shell
- confirm benchmark artifact output paths are created successfully

## Reproducibility Validation

- record the exact seed range used for any reported benchmark results
- record any search iteration counts or time limits used in reported results
- rerun at least one benchmark command twice and confirm matching outputs

## Documentation Validation

- make sure the README examples still match the CLI
- make sure the report, pitch, and handoff docs use the same terminology for solver stages
- make sure known gaps are still stated honestly

## Submission Package Validation

- include only the files needed for source review and reproduction
- include benchmark artifacts only when they support a concrete report claim
- remove stale generated files that are not part of the intended package

## Verified Command Set

```powershell
Set-Location "F:\Projects\Hackathons\YardMind"
$env:PYTHONPATH = "src"
pytest
python -m yardmind.cli examples/sample-instance.json --mode inspect
python -m yardmind.cli examples/sample-instance.json --mode constructive
python -m yardmind.cli examples/sample-instance.json --mode search --iterations 6 --seed 11
python -m yardmind.cli examples/curated-improvement-instance.json --mode benchmark --runs 4 --iterations 12 --seed 7 --time-limit-seconds 0.05 --output artifacts/curated-improvement-benchmark.json
pwsh -File scripts/validate-documented-workflow.ps1
python scripts/generate_chart_ready_artifacts.py
```

Replace development instances with official instances once the parser is updated.