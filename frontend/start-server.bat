@echo off
REM ZTNAS Frontend Server Startup Script (Windows)
REM Purpose: Start production-ready frontend server for college dashboard
REM Usage: Double-click or run from command line

setlocal enabledelayedexpansion

echo.
echo ======================================================================
echo  ZTNAS - Zero Trust Network Access System
echo  Frontend Server (Production-Ready)
echo ======================================================================
echo.

REM Check if serve.py exists
if not exist "serve.py" (
    echo ERROR: serve.py not found in current directory
    echo Please run this script from: d:\projects\ztnas\frontend
    pause
    exit /b 1
)

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found in PATH
    echo Please install Python 3.8+ first
    pause
    exit /b 1
)

echo Checking system configuration...
echo.

REM Step 3: Check if simple server exists
if not exist "serve_simple.py" (
    echo ERROR: serve_simple.py not found
    pause
    exit /b 1
)

echo Checking system configuration...
echo.

REM Get Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Python Version: %PYTHON_VERSION%

REM Check if static directory exists
if not exist "static" (
    echo ERROR: static directory not found
    pause
    exit /b 1
)

echo Static Directory: ✓ Found
echo.

REM Count files
setlocal enabledelayedexpansion
set count=0
for /r "static" %%f in (*) do set /a count+=1
echo Files in static: !count! files
echo.

REM Start server
echo ======================================================================
echo Starting Production Frontend Server...
echo ======================================================================
echo.
echo Access the dashboard at: http://localhost:5500
echo.
echo Features:
echo  ✓ Automatic index.html serving
echo  ✓ Security headers enabled
echo  ✓ CORS support for API calls
echo  ✓ Production logging
echo  ✓ Directory listing blocked
echo.
echo Press Ctrl+C to stop the server
echo.
echo ======================================================================
echo.

python serve_simple.py

endlocal
pause
