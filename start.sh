#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#  ResumeAI Pro - Start Script
#  Starts both backend (FastAPI) and frontend (Vite) servers
# ═══════════════════════════════════════════════════════════════

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# ─── Colors ──────────────────────────────────────────────────
echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════╗"
echo "║         ResumeAI Pro — Launching...          ║"
echo "║       Smart Resume Optimizer v2.0            ║"
echo "╚══════════════════════════════════════════════╝"
echo -e "${NC}"

# ─── Kill any existing processes ─────────────────────────────
pkill -f "uvicorn main:app" 2>/dev/null || true
pkill -f "vite" 2>/dev/null || true
sleep 1

# ─── Start Backend ────────────────────────────────────────────
echo -e "${YELLOW}[1/2] Starting FastAPI backend (port 8000)...${NC}"
cd backend

# Activate venv if present
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

nohup python -m uvicorn main:app --host 0.0.0.0 --port 8000 --log-level warning > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > ../pids/backend.pid
echo -e "${GREEN}✓ Backend started (PID: $BACKEND_PID)${NC}"

# Wait for backend to be ready
sleep 2
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    sleep 2  # Extra wait on slower machines
fi

# ─── Start Frontend ───────────────────────────────────────────
echo -e "${YELLOW}[2/2] Starting React frontend (port 3000)...${NC}"
cd ../frontend

nohup npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > ../pids/frontend.pid
echo -e "${GREEN}✓ Frontend starting (PID: $FRONTEND_PID)${NC}"

sleep 3

# ─── Success ─────────────────────────────────────────────────
echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════╗"
echo "║           🚀 ResumeAI Pro is Running!            ║"
echo "║                                                  ║"
echo "║   📱 Open:  http://localhost:3000                ║"
echo "║   🔧 API:   http://localhost:8000/docs           ║"
echo "║                                                  ║"
echo "║   Press Ctrl+C to stop all services             ║"
echo "╚══════════════════════════════════════════════════╝"
echo -e "${NC}"

# ─── Keep alive & handle stop ────────────────────────────────
cleanup() {
    echo -e "\n${YELLOW}Stopping services...${NC}"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    pkill -f "uvicorn main:app" 2>/dev/null || true
    pkill -f "vite" 2>/dev/null || true
    echo -e "${GREEN}✓ All services stopped.${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Wait
tail -f ../logs/backend.log &
wait
