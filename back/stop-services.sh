#!/bin/bash

# ═══════════════════════════════════════════════════════════════
# Stop All Services - Test Maker Platform
# ═══════════════════════════════════════════════════════════════

echo "Stopping Test Maker Platform services..."
echo ""

if [ -f .recording-service.pid ]; then
    RECORDING_PID=$(cat .recording-service.pid)
    echo " Stopping Recording Service (PID: $RECORDING_PID)..."
    kill $RECORDING_PID 2>/dev/null || echo " Already stopped"
    rm .recording-service.pid
fi

if [ -f .main-api.pid ]; then
    MAIN_API_PID=$(cat .main-api.pid)
    echo " Stopping Main API (PID: $MAIN_API_PID)..."
    kill $MAIN_API_PID 2>/dev/null || echo " Already stopped"
    rm .main-api.pid
fi

echo ""
echo " Cleaning up ports 8000 and 8001..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:8001 | xargs kill -9 2>/dev/null || true

echo ""
echo " All services stopped."
