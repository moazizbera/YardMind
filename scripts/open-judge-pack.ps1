param(
    [string]$ListenHost = "127.0.0.1",
    [int]$Port = 5173,
    [switch]$Intro,
    [switch]$SkipInstall,
    [switch]$NoOpenDocs,
    [switch]$NoOpen,
    [switch]$Foreground
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$judgeSummary = Join-Path $repoRoot "docs\report\judge-summary.md"
$technicalReport = Join-Path $repoRoot "docs\report\technical-report.md"

if (-not $NoOpenDocs) {
    Start-Process $judgeSummary
    Start-Process $technicalReport
}

$launcherArgs = @{
    ListenHost = $ListenHost
    Port = $Port
    View = "judge"
    Intro = $Intro
    AutoPlay = $true
    Kiosk = $true
    SkipInstall = $SkipInstall
    NoOpen = $NoOpen
    Foreground = $Foreground
}

& (Join-Path $PSScriptRoot "open-react-demo.ps1") @launcherArgs