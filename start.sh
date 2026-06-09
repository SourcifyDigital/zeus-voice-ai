#!/bin/bash
# Zeus Voice AI — Quick Start (Windows git-bash)

echo "╔═══════════════════════════════════════╗"
echo "║     Zeus Voice AI — Quick Start       ║"
echo "╚═══════════════════════════════════════╝"
echo ""

# Kill any existing servers on 8000 or 5500
kill $(lsof -t -i:8000) 2>/dev/null
kill $(lsof -t -i:5500) 2>/dev/null

# Start backend
echo "[1/2] Starting backend on port 8000..."
/c/Users/abelf/AppData/Local/Programs/Python/Python311/python.exe "$(dirname $0)/backend/main.py" &
BACKEND_PID=$!
sleep 2

# Check backend is up
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "  ✓ Backend running (PID: $BACKEND_PID)"
else
    echo "  ✗ Backend failed to start"
    exit 1
fi

# Start frontend
echo "[2/2] Starting frontend on port 5500..."
cd "$(dirname $0)/frontend"
/c/Users/abelf/AppData/Local/Programs/Python/Python311/python.exe -m http.server 5500 &
FRONTEND_PID=$!
sleep 1

echo ""
echo "  ✓ Frontend running (PID: $FRONTEND_PID)"
echo ""
echo "═══════════════════════════════════════════"
echo "  Open: http://localhost:5500"
echo "  API:  http://localhost:8000"
echo "  Docs: http://localhost:8000/docs"
echo "═══════════════════════════════════════════"
echo ""
echo "Press Ctrl+C to stop both servers."

# Wait for either process
wait $BACKEND_PID $FRONTEND_PID
