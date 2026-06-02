param(
    [string]$Instance = "examples/challenge-instance.json",
    [int]$Iterations = 20,
    [int]$Seed = 7,
    [string]$ListenHost = "127.0.0.1",
    [int]$Port = 5173,
    [switch]$Intro,
    [switch]$SkipInstall,
    [switch]$NoLaunch,
    [switch]$NoOpenDocs,
    [switch]$NoOpenBrowser,
    [switch]$Foreground
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot

Write-Host "Preparing submission rehearsal pack..."
$reportPackArgs = @{
    Instance = $Instance
    Iterations = $Iterations
    Seed = $Seed
    CaptureScreenshots = $true
    SkipInstall = $SkipInstall
    NoOpen = $true
}

& (Join-Path $PSScriptRoot "generate-report-pack.ps1") @reportPackArgs

if ($NoLaunch) {
    Write-Host "Submission rehearsal assets refreshed. Launch step skipped."
    exit 0
}

Write-Host "Launching judge presentation pack..."
$judgePackArgs = @{
    ListenHost = $ListenHost
    Port = $Port
    Intro = $Intro
    SkipInstall = $SkipInstall
    NoOpenDocs = $NoOpenDocs
    NoOpen = $NoOpenBrowser
    Foreground = $Foreground
}

& (Join-Path $PSScriptRoot "open-judge-pack.ps1") @judgePackArgs