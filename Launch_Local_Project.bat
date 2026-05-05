@echo off
setlocal
cd /d "%~dp0"
echo Starting Skateboarding Preservation Project...
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Launch_Local_Project.ps1"
echo.
echo Launcher finished. Press any key to close this window.
pause >nul
