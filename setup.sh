#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#  ResumeAI Pro - Setup Script
#  Run this ONCE to install all dependencies
# ═══════════════════════════════════════════════════════════════

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════╗"
echo "║       ResumeAI Pro — Setup               ║"
echo "║   Smart Resume Optimizer (No API Keys)   ║"
echo "╚══════════════════════════════════════════╝"
echo -e "${NC}"

# ─── Check Python ────────────────────────────────────────────
echo -e "${YELLOW}[1/4] Checking Python...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 not found. Install Python 3.9+ first.${NC}"
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}✓ $PYTHON_VERSION${NC}"

# ─── Check Node ──────────────────────────────────────────────
echo -e "${YELLOW}[2/4] Checking Node.js...${NC}"
if ! command -v node &> /dev/null; then
    echo -e "${RED}Node.js not found. Install Node.js 18+ first.${NC}"
    exit 1
fi
NODE_VERSION=$(node --version)
echo -e "${GREEN}✓ Node.js $NODE_VERSION${NC}"

# ─── Install Python dependencies ─────────────────────────────
echo -e "${YELLOW}[3/4] Installing Python backend dependencies...${NC}"
cd backend

# Use venv if available
if python3 -m venv --help &> /dev/null; then
    python3 -m venv venv
    source venv/bin/activate
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

pip install -q --no-input -r requirements.txt
echo -e "${GREEN}✓ Python dependencies installed${NC}"

# ─── Install Node dependencies ────────────────────────────────
echo -e "${YELLOW}[4/4] Installing frontend dependencies...${NC}"
cd ../frontend
npm install --silent
echo -e "${GREEN}✓ Frontend dependencies installed${NC}"

cd ..

echo -e "${GREEN}"
echo "╔══════════════════════════════════════════════╗"
echo "║            ✅ Setup Complete!                ║"
echo "║                                              ║"
echo "║   Run: ./start.sh to launch the app         ║"
echo "║   Then open: http://localhost:3000           ║"
echo "╚══════════════════════════════════════════════╝"
echo -e "${NC}"
