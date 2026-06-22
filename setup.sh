#!/bin/bash
# Mac/Linux Quick Setup Script for Backtesting Platform

echo ""
echo "========================================"
echo " Equity Backtesting Platform - Setup"
echo "========================================"
echo ""

# Check Python
echo "1. Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python not found. Install from python.org"
    exit 1
fi
echo "✓ Python found: $(python3 --version)"

# Check Node
echo ""
echo "2. Checking Node.js..."
if ! command -v node &> /dev/null; then
    echo "ERROR: Node.js not found. Install from nodejs.org"
    exit 1
fi
echo "✓ Node.js found: $(node --version)"

# Check PostgreSQL
echo ""
echo "3. Checking PostgreSQL..."
if ! command -v psql &> /dev/null; then
    echo "WARNING: PostgreSQL not found. Install from postgresql.org"
    echo "Then run: createdb backtesting_db"
else
    echo "✓ PostgreSQL found"
    createdb backtesting_db 2>/dev/null || echo "  (Database may already exist)"
fi

# Backend setup
echo ""
echo "4. Setting up Backend..."
cd backend || exit 1

if [ ! -d "venv" ]; then
    echo "  Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
echo "  Installing dependencies..."
pip install -q -r requirements.txt

# Copy .env
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "  Created .env - please edit with your PostgreSQL password"
fi

cd ..

# Frontend setup
echo ""
echo "5. Setting up Frontend..."
cd frontend || exit 1
echo "  Installing dependencies..."
npm install -q

# Copy .env
if [ ! -f ".env" ]; then
    cp .env.example .env
fi

cd ..

echo ""
echo "========================================"
echo " Setup Complete!"
echo "========================================"
echo ""
echo "Next Steps:"
echo ""
echo "1. EDIT backend/.env with PostgreSQL password"
echo ""
echo "2. FETCH DATA (one-time, takes 5-10 minutes):"
echo "   cd backend && source venv/bin/activate"
echo "   python scripts/ingest_data.py"
echo ""
echo "3. START BACKEND (Terminal 1):"
echo "   cd backend && source venv/bin/activate"
echo "   uvicorn app.main:app --reload"
echo ""
echo "4. START FRONTEND (Terminal 2):"
echo "   cd frontend && npm run dev"
echo ""
echo "5. OPEN: http://localhost:5173"
echo ""
