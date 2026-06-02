param(
    [string]$Instance = "examples/challenge-instance.json",
    [int]$Iterations = 20,
    [int]$Seed = 7,
    [switch]$CaptureScreenshots,
    [switch]$SkipInstall,
    [switch]$NoOpen
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$webRoot = Join-Path $repoRoot "web"
$technicalReport = Join-Path $repoRoot "docs\report\technical-report.md"
$judgeSummary = Join-Path $repoRoot "docs\report\judge-summary.md"

Set-Location $repoRoot
$env:PYTHONPATH = "src"

Write-Host "Regenerating demo snapshot..."
python -m yardmind.demo --instance $Instance --output artifacts/demo/index.html --iterations $Iterations --seed $Seed

Write-Host "Regenerating chart-ready artifacts..."
python scripts/generate_chart_ready_artifacts.py

Set-Location $webRoot
if (-not $SkipInstall -and -not (Test-Path "node_modules")) {
    npm install
}

Write-Host "Building React presentation..."
npm run build

Set-Location $repoRoot

if ($CaptureScreenshots) {
    Write-Host "Capturing presentation screenshots..."
    & (Join-Path $PSScriptRoot "capture-react-demo.ps1") -SkipSnapshot -SkipInstall
}

Write-Host "Report pack ready:"
Write-Host "- docs/report/technical-report.md"
Write-Host "- docs/report/judge-summary.md"
Write-Host "- artifacts/demo/index.html"
Write-Host "- artifacts/demo/hackathon-frontend-judge.png"
Write-Host "- artifacts/demo/hackathon-frontend-organization.png"
Write-Host "- artifacts/demo/hackathon-frontend-equations.png"
Write-Host "- artifacts/demo/hackathon-frontend-proof.png"
Write-Host "- artifacts/report/repair_ablation_comparison.csv"
Write-Host "- artifacts/report/presentation/realistic_seed1_convergence.csv"
Write-Host "- artifacts/report/presentation/realistic_seed1_worked_example.csv"
Write-Host "- web/dist/index.html"

if (-not $NoOpen) {
    Start-Process $technicalReport
    Start-Process $judgeSummary
    Start-Process "artifacts/demo/index.html"
}
