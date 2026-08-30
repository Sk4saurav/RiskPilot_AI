$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "                RISKPILOT DEMO ENVIRONMENT                " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Verify dependencies
Write-Host "`n[1/4] Verifying dependencies..." -ForegroundColor Yellow
if (-not (Get-Command "python" -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Python is not installed or not in PATH." -ForegroundColor Red
    exit 1
}
if (-not (Get-Command "npm" -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Node.js/npm is not installed or not in PATH." -ForegroundColor Red
    exit 1
}
Write-Host "Dependencies verified." -ForegroundColor Green

# 2. Reset database
Write-Host "`n[2/4] Resetting and seeding the demo environment..." -ForegroundColor Yellow
$resetOutput = cmd /c "python -m tools.demo.reset_demo 2>&1"
$resetOutputString = $resetOutput | Out-String

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error resetting demo environment. Output:" -ForegroundColor Red
    Write-Host $resetOutputString
    exit 1
}

# Extract API Key from output
$apiKey = ""
$lines = $resetOutputString -split "`n"
$foundKey = $false
foreach ($line in $lines) {
    if ($foundKey -and $line -match "^[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+$") {
        $apiKey = $line.Trim()
        break
    }
    if ($line -match "API Key \(JWT\):") {
        $foundKey = $true
    }
}

Write-Host "Demo database seeded successfully." -ForegroundColor Green
if ($apiKey) {
    Write-Host "Generated API Key: $apiKey" -ForegroundColor Gray
}

# 3. Start API Server
Write-Host "`n[3/5] Starting FastAPI backend (port 8000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$PWD'; Write-Host 'Starting RiskPilot API...'; python -m uvicorn apps.api.app.main:app --host 127.0.0.1 --port 8000" -WindowStyle Normal
Start-Sleep -Seconds 2 # Give it a moment to bind the port
Write-Host "Backend API spawned in a new window." -ForegroundColor Green

# 4. Start Investigation Worker
Write-Host "`n[4/5] Starting Background Investigation Worker..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$PWD'; Write-Host 'Starting RiskPilot Background Worker...'; python -m workers.investigation.main" -WindowStyle Normal
Start-Sleep -Seconds 1 # Give it a moment to initialize
Write-Host "Background worker spawned in a new window." -ForegroundColor Green

# 5. Start Dashboard
Write-Host "`n[5/5] Starting Vite dashboard (port 5173)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$PWD\apps\dashboard'; Write-Host 'Starting RiskPilot Dashboard...'; npm run dev" -WindowStyle Normal
Write-Host "Frontend dashboard spawned in a new window." -ForegroundColor Green

# 6. Success and Instructions
Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "                     DEMO READY                             " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "`n1. Open the Analyst Dashboard:" -ForegroundColor White
Write-Host "   http://localhost:5173" -ForegroundColor Blue

Write-Host "`n2. The API is running at:" -ForegroundColor White
Write-Host "   http://localhost:8000" -ForegroundColor Blue

Write-Host "`n3. To trigger the interactive sales narrative, open a new terminal and run:" -ForegroundColor White
Write-Host "   python -m tools.customer_simulator.main" -ForegroundColor Yellow

Write-Host "`n(Press Ctrl+C in the spawned windows to shut down the servers when finished)" -ForegroundColor Gray
Write-Host "============================================================" -ForegroundColor Cyan
