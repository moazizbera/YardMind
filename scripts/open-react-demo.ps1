param(
    [string]$ListenHost = "127.0.0.1",
    [int]$Port = 5173,
    [ValidateSet("default", "judge", "story", "walkthrough", "proof", "equations", "history", "organization", "yard-stage", "replay-stage")]
    [string]$View = "default",
    [switch]$Intro,
    [switch]$AutoPlay,
    [switch]$Kiosk,
    [switch]$SkipInstall,
    [switch]$NoOpen,
    [switch]$Foreground
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$webRoot = Join-Path $repoRoot "web"

function Get-DemoUrl {
    param(
        [string]$BaseUrl,
        [string]$SelectedView,
        [bool]$EnableIntro,
        [bool]$EnableAutoPlay,
        [bool]$EnableKiosk
    )

    $query = [System.Collections.Generic.List[string]]::new()

    switch ($SelectedView) {
        "judge" { $query.Add("view=judge") }
        "story" { $query.Add("view=story") }
        "walkthrough" { $query.Add("walkthrough=1") }
        "proof" { $query.Add("view=proof") }
        "equations" { $query.Add("view=equations") }
        "history" { $query.Add("view=history") }
        "organization" { $query.Add("view=organization") }
        "yard-stage" { $query.Add("view=yard-stage") }
        "replay-stage" { $query.Add("view=replay-stage") }
        default { }
    }

    if ($EnableIntro) {
        $query.Add("splash=1")
    }

    if ($EnableAutoPlay) {
        $query.Add("autoplay=1")
    }

    if ($EnableKiosk) {
        $query.Add("kiosk=1")
    }

    if ($query.Count -eq 0) {
        return $BaseUrl
    }

    return "$BaseUrl/?$($query -join '&')"
}

function Get-AvailablePort {
    param(
        [string]$RequestedHost,
        [int]$StartingPort
    )

    $candidatePort = $StartingPort

    while ($true) {
        $listener = $null
        try {
            $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Parse($RequestedHost), $candidatePort)
            $listener.Start()
            return $candidatePort
        }
        catch {
            $candidatePort += 1
        }
        finally {
            if ($null -ne $listener) {
                $listener.Stop()
            }
        }
    }
}

Set-Location $webRoot

if (-not $SkipInstall -and -not (Test-Path "node_modules")) {
    npm install
}

$resolvedPort = Get-AvailablePort -RequestedHost $ListenHost -StartingPort $Port
$baseUrl = "http://$ListenHost`:$resolvedPort"
$targetUrl = Get-DemoUrl -BaseUrl $baseUrl -SelectedView $View -EnableIntro:$Intro -EnableAutoPlay:$AutoPlay -EnableKiosk:$Kiosk
$viteBinary = Join-Path $webRoot "node_modules\.bin\vite.cmd"
$viteArgs = @("--host", $ListenHost, "--port", "$resolvedPort", "--strictPort")

if ($Foreground) {
    Write-Host "Starting React demo at $targetUrl"
    if (-not $NoOpen) {
        Start-Process $targetUrl
    }
    & $viteBinary @viteArgs
    exit $LASTEXITCODE
}

Write-Host "Starting React demo at $targetUrl"

Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$webRoot'; & '$viteBinary' --host '$ListenHost' --port '$resolvedPort' --strictPort"
) -WorkingDirectory $webRoot | Out-Null

if (-not $NoOpen) {
    Start-Process $targetUrl
}