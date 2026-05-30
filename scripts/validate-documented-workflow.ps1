$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot
$env:PYTHONPATH = "src"

Write-Host "Running test suite..."
pytest

Write-Host "Running documented CLI commands..."
python -m yardmind.cli examples/sample-instance.json --mode inspect
python -m yardmind.cli examples/sample-instance.json --mode constructive
python -m yardmind.cli examples/sample-instance.json --mode search --iterations 6 --seed 11
python -m yardmind.cli examples/curated-improvement-instance.json --mode benchmark --runs 4 --iterations 12 --seed 7 --time-limit-seconds 0.05 --output artifacts/curated-improvement-benchmark.json
python -m yardmind.demo --instance examples/sample-instance.json --output artifacts/demo/index.html
python scripts/generate_official_baseline_artifact.py
python scripts/compare_official_constructive_variants.py

Write-Host "Generating chart-ready artifacts..."
python scripts/generate_chart_ready_artifacts.py

Write-Host "Documented workflow validation completed successfully."