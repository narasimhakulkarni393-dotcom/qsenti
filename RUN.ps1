# Q-Sentinel Quick Launch Script for PowerShell

Write-Host "`n╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║        Q-SENTINEL: Phishing URL Detection Web App              ║" -ForegroundColor Cyan
Write-Host "║              Classical ML Edition v0.1.0                       ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

# Change to script directory
Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Path)

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python not found. Please install Python 3.8+" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if model exists
if (-not (Test-Path "models\phishing_model.pkl")) {
    Write-Host "`n⚠ Model not found. Training with sample dataset..." -ForegroundColor Yellow
    Write-Host ""
    python train.py --data data/sample_urls.csv
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Model training failed" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

Write-Host "`n✓ Starting Q-Sentinel web app..." -ForegroundColor Green
Write-Host ""
Write-Host "  Dashboard: http://localhost:8501" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Launch Streamlit
python -m streamlit run app.py --logger.level=error

Read-Host "Press Enter to exit"
