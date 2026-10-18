@echo off
chcp 65001 >nul
cd /d "%~dp0"
rem Console-less launch: pythonw creates no cmd window at all, so the GUI
rem appears straight away (no flash + hide dance like with python.exe).
where pythonw >nul 2>nul
if errorlevel 1 (
    echo WARNING: pythonw not found, falling back to console mode.
    python main.py
    pause
) else (
    start "" pythonw main.py
)
