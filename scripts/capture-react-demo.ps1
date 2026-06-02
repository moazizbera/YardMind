param(
    [string]$ListenHost = "127.0.0.1",
    [int]$Port = 5173,
    [switch]$SkipSnapshot,
    [switch]$SkipInstall,
    [switch]$SkipBrowserInstall
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$webRoot = Join-Path $repoRoot "web"
$openDemoScript = Join-Path $PSScriptRoot "open-demo.ps1"

Set-Location $repoRoot

if (-not $SkipSnapshot) {
    & $openDemoScript -NoOpen
}

Set-Location $webRoot

if (-not $SkipInstall -and -not (Test-Path "node_modules\playwright")) {
    npm install
}

if (-not $SkipBrowserInstall) {
    npx playwright install chromium
}

npm run capture -- --host=$ListenHost --port=$Port --output-dir=..\artifacts\demo