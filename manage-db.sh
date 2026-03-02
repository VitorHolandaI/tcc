#!/bin/bash

# ═══════════════════════════════════════════════════════════════════════════════
# Database Management Script - Test Maker Platform
# ═══════════════════════════════════════════════════════════════════════════════
#
# Manages PostgreSQL database for local development:
# - Start/stop PostgreSQL container
# - Clean database (drop all tables)
# - Seed database with test data
# - Clean recordings (webcam, audio, screen recordings)
#
# Usage:
# ./manage-db.sh start # Start PostgreSQL container
# ./manage-db.sh stop # Stop PostgreSQL container
# ./manage-db.sh clean # Drop all tables and delete recordings
# ./manage-db.sh seed # Populate database with test data
# ./manage-db.sh reset # Clean + Seed (fresh start)
# ./manage-db.sh status # Check database connection
#
# ═══════════════════════════════════════════════════════════════════════════════

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

DB_URL="postgresql://testmaker:testmaker123@localhost:5432/testmaker"
export DATABASE_URL="$DB_URL"

# Python: prefer venv, fallback to system python3
if [ -f "$BASE_DIR/back/.venv/bin/python" ]; then
    PYTHON="$BASE_DIR/back/.venv/bin/python"
elif command -v python3 &> /dev/null; then
    PYTHON="python3"
else
    echo -e "${RED} Python 3 não encontrado!${NC}"
    exit 1
fi

start_database() {
    echo -e "${BLUE} Starting PostgreSQL container...${NC}"

    if docker ps | grep -q testmaker-db; then
        echo -e "${GREEN} PostgreSQL already running${NC}"
        return 0
    fi

    if docker ps -a | grep -q testmaker-db; then
        echo -e "${YELLOW} Starting existing container...${NC}"
        docker start testmaker-db
    else
        echo -e "${YELLOW}🆕 Creating new PostgreSQL container...${NC}"
        docker compose -f docker-compose.db.yml up -d
    fi

    echo -e "${BLUE} Waiting for database to be ready...${NC}"
    for i in {1..30}; do
        if docker exec testmaker-db pg_isready -U testmaker -d testmaker &> /dev/null; then
            echo -e "${GREEN} PostgreSQL ready!${NC}"
            echo -e "${GREEN} Connection: $DB_URL${NC}"
            return 0
        fi
        sleep 1
    done

    echo -e "${RED} Database failed to start${NC}"
    exit 1
}

stop_database() {
    echo -e "${YELLOW} Stopping PostgreSQL container...${NC}"
    docker compose -f docker-compose.db.yml down
    echo -e "${GREEN} PostgreSQL stopped${NC}"
}

check_database_running() {
    if ! docker ps | grep -q testmaker-db; then
        echo -e "${RED} PostgreSQL not running!${NC}"
        echo -e "${YELLOW} Start it with: ./manage-db.sh start${NC}"
        exit 1
    fi
}

clean_database() {
    echo -e "${YELLOW} Cleaning database and recordings...${NC}"

    check_database_running

    # Drop all tables using CASCADE for PostgreSQL foreign keys
    echo -e "${BLUE} → Dropping all database tables (CASCADE)...${NC}"
    cd "$BASE_DIR/back"
    PYTHONPATH="$BASE_DIR/back" $PYTHON -c "
from app.core.database import engine
from sqlalchemy import text
print('Dropping all tables with CASCADE...')
with engine.connect() as conn:
    conn.execute(text('DROP SCHEMA public CASCADE;'))
    conn.execute(text('CREATE SCHEMA public;'))
    conn.commit()
print(' All tables dropped')
"

    echo -e "${BLUE} → Cleaning recording files...${NC}"
    rm -rf "$BASE_DIR/back/recordings/"*.webm 2>/dev/null || true
    rm -rf "$BASE_DIR/back/recordings/segments/"* 2>/dev/null || true
    rm -rf "$BASE_DIR/back/webcam_recordings/"*.webm 2>/dev/null || true
    rm -rf "$BASE_DIR/back/audio_recordings/"*.wav 2>/dev/null || true

    mkdir -p "$BASE_DIR/back/recordings/segments"
    mkdir -p "$BASE_DIR/back/webcam_recordings"
    mkdir -p "$BASE_DIR/back/audio_recordings"

    echo -e "${GREEN} Database and recordings cleaned${NC}"
}

seed_database() {
    echo -e "${BLUE} Seeding database with test data...${NC}"

    check_database_running

    cd "$BASE_DIR/back"
    PYTHONPATH="$BASE_DIR/back" $PYTHON seed_db.py

    echo -e "${GREEN} Database seeded successfully${NC}"
}

reset_database() {
    echo -e "${YELLOW} Resetting database (clean + seed)...${NC}"
    clean_database
    seed_database
    echo -e "${GREEN} Database reset complete!${NC}"
}

check_status() {
    echo -e "${BLUE} Database Status${NC}"
    echo ""

    if docker ps | grep -q testmaker-db; then
        echo -e "${GREEN} PostgreSQL container: RUNNING${NC}"
    else
        echo -e "${RED} PostgreSQL container: STOPPED${NC}"
        return 1
    fi

    if docker exec testmaker-db pg_isready -U testmaker -d testmaker &> /dev/null; then
        echo -e "${GREEN} Database connection: OK${NC}"
    else
        echo -e "${RED} Database connection: FAILED${NC}"
        return 1
    fi

    TABLE_COUNT=$(docker exec testmaker-db psql -U testmaker -d testmaker -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null | xargs || echo "0")
    echo -e "${BLUE} Tables: $TABLE_COUNT${NC}"

    echo ""
    echo -e "${CYAN} Connection String:${NC}"
    echo -e " $DB_URL"
    echo ""
}

print_help() {
    echo "Database Management Script"
    echo ""
    echo "Usage: ./manage-db.sh [COMMAND]"
    echo ""
    echo "Commands:"
    echo " start Start PostgreSQL container"
    echo " stop Stop PostgreSQL container"
    echo " clean Drop all tables and delete recordings"
    echo " seed Populate database with test data"
    echo " reset Clean + Seed (fresh start)"
    echo " status Check database connection and info"
    echo " help Show this help message"
    echo ""
    echo "Examples:"
    echo " ./manage-db.sh start # Start database"
    echo " ./manage-db.sh reset # Fresh start (clean + seed)"
    echo " ./manage-db.sh status # Check if database is running"
    echo ""
}

case "${1:-help}" in
    start)
        start_database
        ;;
    stop)
        stop_database
        ;;
    clean)
        clean_database
        ;;
    seed)
        seed_database
        ;;
    reset)
        reset_database
        ;;
    status)
        check_status
        ;;
    help|--help|-h)
        print_help
        ;;
    *)
        echo -e "${RED} Unknown command: $1${NC}"
        echo ""
        print_help
        exit 1
        ;;
esac
