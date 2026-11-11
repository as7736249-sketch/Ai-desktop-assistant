@echo off
REM ═══════════════════════════════════════════════════════════
REM   Build Jarvis as a single-folder Windows .exe
REM   Output: dist\Jarvis\Jarvis.exe
REM ═══════════════════════════════════════════════════════════

title Building Jarvis.exe
color 0E

echo.
echo    ╔══════════════════════════════════════════════════╗
echo    ║       🔨  BUILDING JARVIS.EXE  🔨              ║
echo    ║       Takes 3-5 minutes on first build          ║
echo    ╚══════════════════════════════════════════════════╝
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo ❌ Python not found in PATH. Install Python first.
    pause & exit /b 1
)

cd backend

if not exist ".venv\Scripts\python.exe" (
    echo Creating venv...
    python -m venv .venv
)
call .venv\Scripts\activate.bat

echo 📦 Installing dependencies + PyInstaller...
python -m pip install -q --upgrade pip
python -m pip install -q -r requirements.txt
python -m pip install -q pyinstaller==6.10.0

cd ..

echo.
echo 🔨 Building... (this takes a few minutes)
echo.

pyinstaller ^
  --name Jarvis ^
  --add-data "frontend;frontend" ^
  --add-data "backend\.env;." ^
  --paths backend ^
  --collect-all pywhatkit ^
  --noconfirm ^
  --clean ^
  backend\app\main.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo    ╔══════════════════════════════════════════════════╗
    echo    ║       ✅  BUILD SUCCESSFUL!                      ║
    echo    ║                                                  ║
    echo    ║   Your app: dist\Jarvis\Jarvis.exe               ║
    echo    ║   Double-click it to run!                        ║
    echo    ║                                                  ║
    echo    ║   To share: zip the whole dist\Jarvis folder     ║
    echo    ╚══════════════════════════════════════════════════╝
) else (
    echo.
    echo ❌ Build failed. Check errors above.
    echo.
    echo Common fixes:
    echo   1. Run from a short path like C:\jarvis\
    echo   2. Add antivirus exclusion for this folder
    echo   3. Delete dist\ and build\ folders, try again
)

echo.
pause
