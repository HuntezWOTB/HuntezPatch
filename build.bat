@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo === HuntezPatch build v1.03 ===
echo [1/3] Installing dependencies...
python -m pip install -r requirements.txt pyinstaller
if errorlevel 1 (
    echo ERROR: pip install failed.
    pause
    exit /b 1
)

echo [2/3] Making exe icon from huntezpatch_icon.png...
set NOICON=
if not exist huntezpatch_icon.png (
    echo WARNING: huntezpatch_icon.png not found, building without exe icon.
    set NOICON=1
)
if not defined NOICON (
    python -c "from PIL import Image; im=Image.open('huntezpatch_icon.png'); im.save('huntezpatch_icon.ico', sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)]); print('icon ok')"
    if errorlevel 1 (
        echo WARNING: icon convert failed, building without exe icon.
        set NOICON=1
    )
)

echo [3/3] Building onefile exe...
if defined NOICON (
    python -m PyInstaller --noconfirm --clean --onefile --windowed --name HuntezPatch-1.03 --add-data "locales;locales" --add-data "huntezpatch_icon.png;." main.py
) else (
    python -m PyInstaller --noconfirm --clean --onefile --windowed --name HuntezPatch-1.03 --icon huntezpatch_icon.ico --add-data "locales;locales" --add-data "huntezpatch_icon.png;." main.py
)
if errorlevel 1 (
    echo ERROR: PyInstaller build failed.
    pause
    exit /b 1
)
if exist huntezpatch_icon.ico del huntezpatch_icon.ico

echo.
echo OK: dist\HuntezPatch-1.03.exe
pause
