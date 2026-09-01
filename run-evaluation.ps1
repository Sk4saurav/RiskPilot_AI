Write-Host "=================================================="
Write-Host " RiskPilot Beta 0.7 - Full Evaluation Flow        "
Write-Host "=================================================="

if (-Not (Test-Path ".demo_env")) {
    Write-Error "Error: .demo_env not found. Please run .\start-demo.ps1 first to seed the database."
    exit 1
}

$envConfig = Get-Content .demo_env | ConvertFrom-StringData
$apiKey = $envConfig.DEMO_API_KEY
$orgId = $envConfig.DEMO_ORG_ID

Write-Host "`nTarget Organization: $orgId"
Write-Host "Target API Key: $apiKey"

Write-Host "`nInitializing Golden Demo Scenario (Synthetic Data)..."
Write-Host "Scenario: 2,84,000 INR transaction -> UPI Abuse Ring Detection"
Write-Host "`nRunning Customer Simulator..."

python tools/customer_simulator/main.py --scenario upi_ring --api-key $apiKey

Write-Host "`n=================================================="
Write-Host " Evaluation Pipeline Complete!"
Write-Host " Navigate to the Dashboard (http://localhost:5173) to see:"
Write-Host "   1. The new case in Operations."
Write-Host "   2. The Evidence Graph and +25 deterministic score in Investigation."
Write-Host "=================================================="
