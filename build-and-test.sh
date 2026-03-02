#!/bin/bash

# ═══════════════════════════════════════════════════════════════
# Build and Test Script - Test Maker Platform
# ═══════════════════════════════════════════════════════════════
#
# Usage:
# ./build-and-test.sh # Full rebuild and start
# ./build-and-test.sh --no-build # Just restart (skip build)
# ./build-and-test.sh --down # Stop and remove containers
# ./build-and-test.sh --logs # Show logs
#
# ═══════════════════════════════════════════════════════════════

set -e # Exit on error

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

log_success() {
    echo -e "${GREEN} $1${NC}"
}

log_warning() {
    echo -e "${YELLOW} $1${NC}"
}

log_error() {
    echo -e "${RED} $1${NC}"
}

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║ Test Maker Platform - Build & Test ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

NO_BUILD=false
DOWN=false
LOGS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --no-build)
            NO_BUILD=true
            shift
            ;;
        --down)
            DOWN=true
            shift
            ;;
        --logs)
            LOGS=true
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            echo "Usage: $0 [--no-build] [--down] [--logs]"
            exit 1
            ;;
    esac
done

if [ "$DOWN" = true ]; then
    log_info "Stopping and removing containers..."
    docker-compose down -v
    log_success "Containers stopped and removed"
    exit 0
fi

if [ "$LOGS" = true ]; then
    log_info "Showing logs (Ctrl+C to exit)..."
    docker-compose logs -f
    exit 0
fi

log_info "Checking configuration files..."

if [ ! -f "back/.env" ]; then
    log_warning "back/.env not found, copying from .env.example..."
    cp back/.env.example back/.env
    log_info "Please edit back/.env with your Firebase credentials"
fi

if [ ! -f "front/.env" ]; then
    log_warning "front/.env not found, copying from .env.example..."
    cp front/.env.example front/.env
fi

log_success "Configuration files OK"

log_info "Creating directories..."
mkdir -p back/data back/recordings back/recordings/segments back/logs
log_success "Directories created"

log_info "Stopping existing containers..."
docker-compose down 2>/dev/null || true

if [ "$NO_BUILD" = false ]; then
    log_info "Building Docker images (this may take a few minutes)..."
    docker-compose build --no-cache
    log_success "Build completed"
else
    log_info "Skipping build (--no-build flag)"
fi

log_info "Starting containers..."
docker-compose up -d

log_info "Waiting for services to be healthy..."

wait_for_service() {
    local service=$1
    local max_attempts=30
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if docker-compose ps | grep $service | grep -q "healthy"; then
            return 0
        fi
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done

    return 1
}

echo -n "Recording Service"
if wait_for_service "recording-service"; then
    log_success "Recording Service is healthy"
else
    log_error "Recording Service failed to start"
    docker-compose logs recording-service
    exit 1
fi

echo -n "Main API"
if wait_for_service "main-api"; then
    log_success "Main API is healthy"
else
    log_error "Main API failed to start"
    docker-compose logs main-api
    exit 1
fi

log_success "All services are healthy!"

log_info "Running health checks..."

if curl -s http://localhost:8000/ | grep -q "message"; then
    log_success "Main API is responding"
else
    log_error "Main API is not responding"
    exit 1
fi

if curl -s http://localhost:8001/health | grep -q "status"; then
    log_success "Recording Service is responding"
else
    log_error "Recording Service is not responding"
    exit 1
fi

if curl -s http://localhost:3000 > /dev/null 2>&1; then
    log_success "Frontend is responding"
else
    log_warning "Frontend may still be starting..."
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║ Platform is running successfully! ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║ Frontend: http://localhost:3000 ║"
echo "║ Main API: http://localhost:8000 ║"
echo "║ API Docs: http://localhost:8000/docs ║"
echo "║ Recording Service: http://localhost:8001 ║"
echo "║ Recording Health: http://localhost:8001/health ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║ Commands: ║"
echo "║ - View logs: docker-compose logs -f ║"
echo "║ - Stop: docker-compose down ║"
echo "║ - Restart: ./build-and-test.sh --no-build ║"
echo "║ - Rebuild: ./build-and-test.sh ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

read -p "Show logs? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker-compose logs -f
fi
