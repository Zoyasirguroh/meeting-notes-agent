@echo off
REM Meeting Notes Agent - Startup Script
REM This script helps you start the application

setlocal enabledelayedexpansion

echo.
echo ========================================
echo Meeting Notes Agent - Docker Startup
echo ========================================
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not installed or not in PATH
    echo Please install Docker Desktop from https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

REM Check if Docker daemon is running
docker ps >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker daemon is not running
    echo Please start Docker Desktop
    pause
    exit /b 1
)

echo [OK] Docker is installed and running
echo.

REM Get the directory where this script is located
cd /d "%~dp0"

echo Starting Docker Compose services...
echo.

REM Check if containers already exist
docker ps -a | find "meeting-notes-" >nul
if errorlevel 1 (
    echo [INFO] First time setup detected
    echo [INFO] Building images and initializing services...
    docker-compose up -d
) else (
    echo [INFO] Containers already exist, starting them...
    docker-compose up -d
)

echo.
echo Waiting for services to initialize...
echo This may take 30-60 seconds on first run...
echo.

REM Wait for backend to be ready
set /a counter=0
:wait_backend
timeout /t 2 /nobreak >nul
docker exec meeting-notes-backend curl -f http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    set /a counter+=1
    if !counter! lss 30 (
        echo [WAIT] Backend starting... (!counter!/30)
        goto wait_backend
    ) else (
        echo [WARN] Backend took longer than expected, continuing anyway...
    )
)

echo.
echo ========================================
echo Successfully Started!
echo ========================================
echo.
echo Frontend:   http://localhost:3000
echo Backend:    http://localhost:8000
echo API Docs:   http://localhost:8000/docs
echo.
echo View logs:
echo   docker-compose logs -f
echo.
echo Stop services:
echo   docker-compose down
echo.
echo ========================================
echo.

REM Try to open frontend in browser
echo Attempting to open http://localhost:3000 in your browser...
start http://localhost:3000

pause
