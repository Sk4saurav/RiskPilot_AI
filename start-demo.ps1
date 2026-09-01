Write-Host "=================================================="
Write-Host " RiskPilot Beta 0.7 - Startup Sequence Initiated  "
Write-Host "=================================================="

Write-Host "`n[1/5] Cleaning database for a pristine environment..."
Remove-Item "apps\api\riskpilot.db" -Force -ErrorAction SilentlyContinue

Write-Host "[2/5] Seeding Organization and default Policy..."
python tools\seed.py

Write-Host "[3/5] Starting API Server (Port 8000)..."
Start-Process powershell -ArgumentList "-NoExit -Command `"title RiskPilot API Server; python -m uvicorn apps.api.app.main:app --port 8000`""

Write-Host "[4/5] Starting Investigation Worker..."
Start-Process powershell -ArgumentList "-NoExit -Command `"title RiskPilot Worker; python -m workers.investigation.main`""

Write-Host "[5/5] Starting Dashboard (Port 5173)..."
Start-Process powershell -ArgumentList "-NoExit -Command `"title RiskPilot Dashboard; cd apps\dashboard; npm run dev`""

Write-Host "`nWaiting 5 seconds for services to boot..."
Start-Sleep -Seconds 5

Write-Host "`nOpening Dashboard..."
Start-Process "http://localhost:5173"

Write-Host "`n=================================================="
Write-Host " RiskPilot is now running!"
Write-Host " To run the evaluation, execute: .\run-evaluation.ps1"
Write-Host "=================================================="
