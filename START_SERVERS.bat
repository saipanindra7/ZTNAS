@echo off
REM ZTNAS Enterprise System - Start All Servers
REM This script starts backend and frontend in separate terminal windows

echo.
echo ========================================
echo ZTNAS Enterprise System - Server Startup
echo ========================================
echo.

REM Check if backend exists
if not exist "backend\main.py" (
    echo ERROR: backend\main.py not found!
    echo Make sure you're in the ZTNAS project root directory.
    pause
    exit /b 1
)

REM Check if frontend exists
if not exist "frontend\serve_simple.py" (
    echo ERROR: frontend\serve_simple.py not found!
    echo Make sure you're in the ZTNAS project root directory.
    pause
    exit /b 1
)

echo.
echo Starting ZTNAS Enterprise Backend...
echo Starting Backend on port 8000...
start "ZTNAS Backend [FastAPI]" cmd /k "cd backend && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"

timeout /t 3 /nobreak

echo.
echo Starting ZTNAS Enterprise Frontend...
echo Starting Frontend on port 5500...
start "ZTNAS Frontend [Python HTTP Server]" cmd /k "cd frontend && python serve_simple.py"

echo.
echo ========================================
echo Servers Starting...
echo ========================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5500/static/html/login.html
echo Health:   http://localhost:8000/health
echo.
echo Check the terminal windows for any startup errors.
echo Both terminal windows will remain open for logs.
echo.
echo To stop servers: Close the terminal windows
echo.
echo ========================================
echo.

pause
