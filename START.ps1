# Meeting Notes Agent - Startup Script (PowerShell)
# Run with: powershell -ExecutionPolicy Bypass -File .\START.ps1

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Meeting Notes Agent - Docker Startup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is installed
try {
    $dockerVersion = docker --version
    Write-Host "[OK] Docker is installed: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Docker is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Docker Desktop from https://www.docker.com/products/docker-desktop"
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if Docker daemon is running
try {
    docker ps > $null
    Write-Host "[OK] Docker daemon is running" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Docker daemon is not running" -ForegroundColor Red
    Write-Host "Please start Docker Desktop"
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "Starting Docker Compose services..."
Write-Host ""

# Navigate to script directory
Push-Location $PSScriptRoot

# Check if containers exist
$containers = docker ps -a 2>&1 | Select-String "meeting-notes-"
if ($null -eq $containers) {
    Write-Host "[INFO] First time setup detected" -ForegroundColor Yellow
    Write-Host "[INFO] Building images and initializing services..." -ForegroundColor Yellow
} else {
    Write-Host "[INFO] Containers already exist, starting them..." -ForegroundColor Yellow
}

# Start services
docker-compose up -d

Write-Host ""
Write-Host "Waiting for services to initialize..." -ForegroundColor Yellow
Write-Host "This may take 30-60 seconds on first run..."
Write-Host ""

# Wait for backend
$counter = 0
$maxWait = 30
while ($counter -lt $maxWait) {
    $backendReady = docker exec meeting-notes-backend curl -f http://localhost:8000/health 2>&1 | Select-String "200"
    if ($null -ne $backendReady) {
        Write-Host "[OK] Backend is ready!" -ForegroundColor Green
        break
    }
    $counter++
    Write-Host "[WAIT] Backend starting... ($counter/$maxWait)" -ForegroundColor Yellow
    Start-Sleep -Seconds 2
}

if ($counter -eq $maxWait) {
    Write-Host "[WARN] Backend took longer than expected, continuing anyway..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Successfully Started!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Frontend:   http://localhost:3000" -ForegroundColor Cyan
Write-Host "Backend:    http://localhost:8000" -ForegroundColor Cyan
Write-Host "API Docs:   http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "View logs:" -ForegroundColor Cyan
Write-Host "  docker-compose logs -f"
Write-Host ""
Write-Host "Stop services:" -ForegroundColor Cyan
Write-Host "  docker-compose down"
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Try to open browser
Write-Host "Attempting to open http://localhost:3000 in your browser..." -ForegroundColor Cyan
Start-Process "http://localhost:3000"

Pop-Location
Read-Host "Press Enter to close this window"
