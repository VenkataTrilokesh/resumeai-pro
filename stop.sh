#!/bin/bash
# Stop all running services
pkill -f "uvicorn main:app" 2>/dev/null && echo "Backend stopped"
pkill -f "vite" 2>/dev/null && echo "Frontend stopped"
echo "All services stopped."
