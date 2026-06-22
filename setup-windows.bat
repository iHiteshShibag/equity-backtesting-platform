@echo off
REM Windows 11 Quick Setup Script for Backtesting Platform

echo.
echo ========================================
echo  Equity Backtesting Platform - Setup
echo ========================================
echo.

echo 1. Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.11+ from python.org
    pause
    exit /b 1
)
echo ✓ Python found

echo.
echo 2. Checking Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not found. Please install Node.js 18+ from nodejs.org
    pause
    exit /b 1
)
echo ✓ Node.js found

echo.
echo 3. Checking PostgreSQL connection...
psql -U postgres -c "SELECT 1" >nul 2>&1
if errorlevel 1 (
    echo WARNING: PostgreSQL not accessible. Make sure it's installed and running
    echo Run: net start postgresql-x64-15
    pause
) else (
    echo ✓ PostgreSQL found
)

echo.
echo 4. Creating database...
psql -U postgres -c "CREATE DATABASE backtesting_db" >nul 2>&1
if errorlevel 1 (
    echo (Database may already exist - continuing)
) else (
    echo ✓ Database created
)

echo.
echo 5. Setting up Backend...
cd backend
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)
call venv\Scripts\activate
echo Installing backend dependencies...
pip install -r requirements.txt >nul 2>&1
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo ✓ Backend dependencies installed

echo.
echo 6. Setting up Frontend...
cd ..\frontend
echo Installing frontend dependencies...
call npm install >nul 2>&1
if errorlevel 1 (
    echo ERROR: Failed to install npm dependencies
    pause
    exit /b 1
)
echo ✓ Frontend dependencies installed

echo.
echo ========================================
echo  Setup Complete!
echo ========================================
echo.
echo Next Steps:
echo.
echo 1. EDIT backend/.env file:
echo    Change YOUR_PASSWORD to your PostgreSQL password
echo.
echo 2. FETCH DATA (one-time, takes 5-10 minutes):
echo    cd backend
echo    venv\Scripts\activate
echo    python scripts\ingest_data.py
echo.
echo 3. START BACKEND (in Terminal 1):
echo    cd backend
echo    venv\Scripts\activate
echo    uvicorn app.main:app --reload
echo.
echo 4. START FRONTEND (in Terminal 2):
echo    cd frontend
echo    npm run dev
echo.
echo 5. OPEN BROWSER:
echo    http://localhost:5173
echo.
pause
