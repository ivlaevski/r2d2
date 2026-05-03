<#
.SYNOPSIS
    Use the project venv, refresh Python/npm deps, start core services in separate terminals, open API + dashboard in the browser.

.DESCRIPTION
    - Ensures .venv exists (creates it if missing), then pip / npm updates unless skipped.
    - Starts in new windows: orchestrator with in-process API, Vite dashboard.
    - Does not start apps.audio_service.main (optional; run manually if needed).
    - Does not start apps.perception_service.main (it would contend for the camera with the orchestrator).

    Requires: Python 3.11+ on PATH for first-time venv; Node.js 20+ for the dashboard.

.PARAMETER SkipUpdates
    Skip pip and npm install steps.

.PARAMETER SkipDashboard
    Do not open a terminal for the React dev server.

.PARAMETER SkipBrowsers
    Do not open API docs or dashboard URLs.

.PARAMETER ApiPort
    Port for OpenAPI URL (default 8000; must match API_PORT in .env if you changed it).

.PARAMETER DashboardPort
    Port shown in the dashboard URL (default 5173 for Vite dev).

.PARAMETER ShellStartupDelaySeconds
    Wait before opening browsers so uvicorn/Vite can bind (default 6).
#>
[CmdletBinding()]
param(
    [switch] $SkipUpdates,
    [switch] $SkipDashboard,
    [switch] $SkipBrowsers,
    [int] $ApiPort = 8000,
    [int] $DashboardPort = 5173,
    [int] $ShellStartupDelaySeconds = 6
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-PwshOrWindowsPowerShell {
    if (Get-Command pwsh -ErrorAction SilentlyContinue) {
        return (Get-Command pwsh).Source
    }
    return (Join-Path $env:WINDIR 'System32\WindowsPowerShell\v1.0\powershell.exe')
}

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$PyExe = Join-Path $RepoRoot '.venv\Scripts\python.exe'
$PipExe = Join-Path $RepoRoot '.venv\Scripts\pip.exe'
$DashboardDir = Join-Path $RepoRoot 'apps\dashboard'
$Pwsh = Get-PwshOrWindowsPowerShell

Set-Location $RepoRoot
Write-Host "Repository root: $RepoRoot" -ForegroundColor Cyan

if (-not (Test-Path $PyExe)) {
    Write-Host 'No .venv found; creating virtual environment...' -ForegroundColor Yellow
    python -m venv (Join-Path $RepoRoot '.venv')
    if (-not (Test-Path $PyExe)) {
        throw "Failed to create venv at $PyExe (is python on PATH?)."
    }
}

if (-not $SkipUpdates) {
    Write-Host 'Updating pip and editable install [dev]...' -ForegroundColor Cyan
    & $PyExe -m pip install -U pip
    if ($LASTEXITCODE -ne 0) { throw "pip install -U pip failed (exit $LASTEXITCODE)." }
    & $PipExe install -e ".[dev]"
    if ($LASTEXITCODE -ne 0) { throw "pip install -e .[dev] failed (exit $LASTEXITCODE)." }

    if (-not $SkipDashboard -and (Test-Path (Join-Path $DashboardDir 'package.json'))) {
        Write-Host 'Updating dashboard npm dependencies...' -ForegroundColor Cyan
        Push-Location $DashboardDir
        try {
            if (Get-Command npm -ErrorAction SilentlyContinue) {
                npm install
                if ($LASTEXITCODE -ne 0) { throw "npm install failed in apps/dashboard (exit $LASTEXITCODE)." }
            }
            else {
                Write-Warning 'npm not found; skip dashboard npm install. Install Node.js 20+ to run the SPA.'
            }
        }
        finally {
            Pop-Location
        }
    }
}
else {
    Write-Host 'Skipping dependency updates (-SkipUpdates).' -ForegroundColor DarkGray
}

function Start-ServiceWindow {
    param(
        [Parameter(Mandatory)] [string] $Title,
        [Parameter(Mandatory)] [string] $WorkingDirectory,
        [Parameter(Mandatory)] [string] $CommandLine
    )
    $wdLit = $WorkingDirectory.Replace("'", "''")
    $script = "Set-Location -LiteralPath '$wdLit'; $CommandLine"
    $args = @(
        '-NoExit'
        '-NoProfile'
        '-Command'
        $script
    )
    Start-Process -FilePath $Pwsh -WorkingDirectory $WorkingDirectory -ArgumentList $args -WindowStyle Normal | Out-Null
    Write-Host "Started window: $Title" -ForegroundColor Green
}

$pyLiteral = $PyExe.Replace("'", "''")

Write-Host 'Launching services in new terminals...' -ForegroundColor Cyan

$orchCmd = "& '$pyLiteral' -m apps.orchestrator_service.main --with-api"
Start-ServiceWindow -Title 'robot-follower: orchestrator + API' -WorkingDirectory $RepoRoot -CommandLine $orchCmd

if (-not $SkipDashboard) {
    if (Get-Command npm -ErrorAction SilentlyContinue) {
        $dashCmd = "npm run dev"
        Start-ServiceWindow -Title 'robot-follower: dashboard (Vite)' -WorkingDirectory $DashboardDir -CommandLine $dashCmd
    }
    else {
        Write-Warning 'npm not found; dashboard terminal not started.'
    }
}

if (-not $SkipBrowsers) {
    $apiUrl = "http://127.0.0.1:$ApiPort/docs"
    $dashUrl = "http://localhost:$DashboardPort/"
    Write-Host "Waiting $ShellStartupDelaySeconds s for servers before opening browsers..." -ForegroundColor DarkGray
    Start-Sleep -Seconds $ShellStartupDelaySeconds
    Write-Host "Opening $apiUrl and $dashUrl" -ForegroundColor Cyan
    Start-Process $apiUrl
    Start-Process $dashUrl
}

Write-Host 'Done. Close each terminal window to stop that service.' -ForegroundColor Cyan
