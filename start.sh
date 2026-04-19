#!/bin/bash
# Startup script for the Inventory Dashboard application
# This script starts both the backend API and frontend development server

echo "================================================"
echo "Inventory Dashboard - Startup Script"
echo "================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "❌ Python is not installed or not in PATH"
    exit 1
fi

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed or not in PATH"
    exit 1
fi

echo -e "${BLUE}📦 Checking virtual environment...${NC}"
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

echo -e "${BLUE}📦 Installing Python dependencies...${NC}"
pip install -q -r requirements.txt

echo ""
echo -e "${BLUE}📦 Installing Frontend dependencies...${NC}"
cd inventory-dashboard
npm install --silent
cd ..

echo ""
echo "================================================"
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo "================================================"
echo ""
echo "Starting services..."
echo "  🔵 Backend API: http://localhost:8000"
echo "  🔵 Frontend Dev: http://localhost:5173"
echo "  🔵 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Start backend
echo -e "${BLUE}▶️  Starting Backend API...${NC}"
python app.py &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start frontend
echo -e "${BLUE}▶️  Starting Frontend Dev Server...${NC}"
cd inventory-dashboard
npm run dev &
FRONTEND_PID=$!
cd ..

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
