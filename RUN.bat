@echo off
REM Q-Sentinel Quick Launch Script for Windows

cls
echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║        Q-SENTINEL: Phishing URL Detection Web App              ║
echo ║              Classical ML Edition v0.1.0                       ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.

REM Change to project directory
cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Please install Python 3.8+
    pause
    exit /b 1
)

REM Check if model exists
if not exist "models\phishing_model.pkl" (
    echo.
    echo ⚠ Model not found. Training with sample dataset...
    echo.
    python train.py --data data/sample_urls.csv
    if %errorlevel% neq 0 (
        echo ERROR: Model training failed
        pause
        exit /b 1
    )
)

echo.
echo ✓ Starting Q-Sentinel web app...
echo.
echo   Dashboard: http://localhost:8501
echo.
echo   Press Ctrl+C to stop the server
echo.

REM Launch Streamlit
python -m streamlit run app.py --logger.level=error

pause
