@echo off
REM HuntezPatch debug launch: runs the program from sources with a visible
REM console window, so all logs and tracebacks stay on screen for debugging.
chcp 65001 >nul
cd /d "%~dp0"
echo === HuntezPatch (debug, console) ===
python main.py
echo.
echo Program exited with code %errorlevel%.
pause
