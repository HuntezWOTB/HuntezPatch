@echo off
chcp 65001 >nul
echo Installing required Python packages...
pip install -r requirements.txt
echo Done.
pause
