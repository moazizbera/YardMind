param(
    [string]$Instance = "examples/sample-instance.json",
    [string]$Output = "artifacts/demo/index.html",
    [int]$Iterations = 8,
    [int]$Seed = 11,
    [switch]$NoOpen
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot
$env:PYTHONPATH = "src"

python -m yardmind.demo --instance $Instance --output $Output --iterations $Iterations --seed $Seed

if (-not $NoOpen) {
    Start-Process $Output
}