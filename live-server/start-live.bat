@echo off
rem The Long Game - one-click launcher for the PowerShell relay edition.
rem Double-click me. Click "Allow" if Windows Firewall asks.
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0server.ps1" %*
echo.
echo (relay stopped)
pause
