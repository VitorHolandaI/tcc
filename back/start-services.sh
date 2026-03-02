#!/bin/bash

# ═══════════════════════════════════════════════════════════════
# Start All Services - Test Maker Platform
# ═══════════════════════════════════════════════════════════════

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║ Starting Test Maker Platform - Scalable Architecture ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

if [ -f .env ]; then
    echo " Loading .env file..."
    export $(cat .env | grep -v '^#' | xargs)
else
    echo " No .env file found. Using default configuration."
    echo " Copy .env.example to .env and configure as needed."
fi

echo ""
echo "Starting services..."
echo ""

echo " Cleaning up existing processes..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:8001 | xargs kill -9 2>/dev/null || true

echo ""

echo " Starting Recording Service (port 8001)..."
python -m recording-service.main > logs/recording-service.log 2>&1 &
RECORDING_PID=$!
echo " PID: $RECORDING_PID"

sleep 2

echo " Starting Main API (port 8000)..."
python -m app.main > logs/main-api.log 2>&1 &
MAIN_API_PID=$!
echo " PID: $MAIN_API_PID"

sleep 2

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║ Services Started Successfully! ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║ Main API: http://localhost:8000 ║"
echo "║ API Docs: http://localhost:8000/docs ║"
echo "║ Recording Service: http://localhost:8001 ║"
echo "║ Recording Health: http://localhost:8001/health ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║ Logs: ║"
echo "║ - tail -f logs/main-api.log ║"
echo "║ - tail -f logs/recording-service.log ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║ To stop: ./stop-services.sh ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

echo $MAIN_API_PID > .main-api.pid
echo $RECORDING_PID > .recording-service.pid

echo " PIDs saved to .main-api.pid and .recording-service.pid"
echo ""
echo "Press Ctrl+C to view logs (services will continue in background)"
echo ""

trap "echo ''; echo 'Services running in background. Use ./stop-services.sh to stop.'; exit 0" INT

tail -f logs/main-api.log logs/recording-service.log
