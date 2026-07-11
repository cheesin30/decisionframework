# The Long Game · Live Room relay — PowerShell edition (Windows, zero installs)
#
# For company laptops with NO Node and NO Python: every Windows machine has
# PowerShell. This script compiles and runs the relay core (relay.cs, which
# must sit in the same folder) using the compiler built into Windows itself.
# Nothing is downloaded or installed.
#
#   Easiest: double-click start-live.bat (same folder)
#   Manual:  powershell -NoProfile -ExecutionPolicy Bypass -File server.ps1
#   Options: -Port 9000   -StaticDir C:\path\to\game\files
#
# Notes for locked-down machines:
#  · First run: click "Allow" on the Windows Firewall prompt or phones can't
#    connect.
#  · If it says LOCALHOST-ONLY mode: Windows needs one-time permission to
#    listen for other devices. Either run PowerShell "as administrator" once,
#    or have an admin run:  netsh http add urlacl url=http://+:8877/ user=Everyone
#  · If Add-Type itself is refused (rare "Constrained Language Mode" lockdown),
#    this machine can't host anything — use the phone-hotspot + personal-laptop
#    setup from the README instead.

param(
    [int]$Port = 8877,
    [string]$StaticDir = ""
)

$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path

if ($StaticDir -eq "") {
    # Kit layout (game html next to this script) or repo layout (html in parent)
    if (Test-Path (Join-Path $here 'long-term-game-live.html')) { $StaticDir = $here }
    elseif (Test-Path (Join-Path (Split-Path -Parent $here) 'long-term-game-live.html')) { $StaticDir = Split-Path -Parent $here }
    else { $StaticDir = $here }
}

$csPath = Join-Path $here 'relay.cs'
if (-not (Test-Path $csPath)) {
    Write-Host "ERROR: relay.cs not found next to server.ps1 ($csPath)." -ForegroundColor Red
    Write-Host "Copy the whole live-server folder together."
    exit 1
}

Write-Host ""
Write-Host "THE LONG GAME - live room relay (PowerShell edition)" -ForegroundColor Cyan
Write-Host "Compiling the relay core with Windows' built-in compiler..." -ForegroundColor DarkGray

try {
    Add-Type -TypeDefinition (Get-Content -Raw -LiteralPath $csPath) -Language CSharp
} catch {
    Write-Host ""
    Write-Host "Could not compile/load the relay on this machine:" -ForegroundColor Red
    Write-Host ("  " + $_.Exception.Message)
    Write-Host ""
    Write-Host "If the message mentions 'Constrained Language Mode' or 'not allowed'," -ForegroundColor Yellow
    Write-Host "this laptop is locked beyond what any script can do - use the" -ForegroundColor Yellow
    Write-Host "phone-hotspot + personal-laptop setup from live-server/README.md." -ForegroundColor Yellow
    exit 1
}

Write-Host ("Big screen:  http://localhost:{0}/?live=host" -f $Port) -ForegroundColor Green
Write-Host "Press Ctrl+C in this window to stop." -ForegroundColor DarkGray
Write-Host ""

# Blocks forever serving the game + live API. All further status lines
# (including phone-reachable address / localhost-only guidance) come from it.
[LongGameRelay.Server]::Run($Port, $StaticDir)
