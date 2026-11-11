@echo off
setlocal
REM ═══════════════════════════════════════════════════════════
REM   Jarvis AI Desktop Assistant — Windows launcher
REM   Double-click to run
REM ═══════════════════════════════════════════════════════════

REM Always run from the folder this file lives in (fixes "wrong folder" errors)
cd /d "%~dp0"

title Jarvis AI Assistant
color 0B

echo.
echo    ╔══════════════════════════════════════════════════╗
echo    ║        🤖  JARVIS AI ASSISTANT  🤖               ║
echo    ║        Starting up, please wait...               ║
echo    ╚══════════════════════════════════════════════════╝
echo.

REM ─── 1. Check Python is installed ───
where python >nul 2>nul
if errorlevel 1 (
    echo ❌ ERROR: Python is not installed or not in PATH
    echo.
    echo Please install Python 3.10 or newer from:
    echo    https://www.python.org/downloads/
    echo During install, TICK "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

cd backend

REM ─── 2. Create virtual environment if missing ───
if not exist ".venv\Scripts\python.exe" (
    echo 📦 Creating virtual environment ^(one-time^)...
    python -m venv .venv
    if errorlevel 1 (
        echo ❌ Failed to create venv. Is Python 3.10+ installed?
        pause
        exit /b 1
    )
)

REM ─── 3. Activate venv ───
call .venv\Scripts\activate.bat

REM ─── 4. Install / update dependencies ───
echo 📦 Checking dependencies (first run can take a few minutes)...
python -m pip install -q --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo ⚠️  Some packages failed to install. Retrying the important ones...
    python -m pip install fastapi "uvicorn[standard]" pydantic pydantic-settings python-multipart requests colorlog
    echo.
)

REM ─── 5. Verify the CORE components actually import ───
echo 🔎 Verifying core components...
python -c "import fastapi, uvicorn, requests, pydantic_settings, colorlog, multipart" >nul 2>nul
if errorlevel 1 (
    echo.
    echo ❌ Core components are still missing.
    echo    Most likely cause: no internet during install, or a broken Python install.
    echo    Fix: connect to internet, then delete the folder "backend\.venv"
    echo         and run START.bat again.
    echo.
    pause
    exit /b 1
)
echo ✅ Core components OK

REM ─── 6. Check whether port 8000 is already in use ───
netstat -ano | findstr /R /C:":8000 .*LISTENING" >nul 2>nul
if not errorlevel 1 (
    echo.
    echo ⚠️  Port 8000 is already in use ^(maybe Jarvis is already running^).
    echo    If the website doesn't load, close the other Jarvis window first,
    echo    or change API_PORT in backend\.env to 8001 and run again.
    echo.
)

REM ─── 7. Launch ───
echo 👉 If a browser does not open by itself, go to:  http://127.0.0.1:8000
echo.
echo   ⚠️  IMPORTANT: KEEP THIS BLACK WINDOW OPEN!
echo       This window IS the server. If you close it,
echo       the website shows "Cannot reach server".
echo       To stop Jarvis later: press Ctrl+C here.
echo.
echo ═══════════════════════════════════════════════════════════
echo.

python -m app.main

echo.
echo Jarvis has stopped.
pause
