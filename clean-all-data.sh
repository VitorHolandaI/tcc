#!/bin/bash

# Full cleanup: stops containers, removes volumes, images, and all data files.
# Usage:
#   ./clean-all-data.sh          # clean only
#   ./clean-all-data.sh --build  # clean then rebuild and start

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REBUILD=false

for arg in "$@"; do
    [[ "$arg" == "--build" ]] && REBUILD=true
done

echo "======================================"
echo " Full cleanup starting..."
echo "======================================"

# 1. Stop and remove all containers, networks, volumes, and locally built images
echo ""
echo "[1/4] Stopping containers and removing volumes + images..."
cd "$BASE_DIR" && docker compose down -v --rmi local --remove-orphans 2>/dev/null
echo "      Done."

# 2. Remove data directories
echo ""
echo "[2/4] Removing recorded data files..."
rm -rf "$BASE_DIR/back/recordings"/*
rm -rf "$BASE_DIR/back/webcam_recordings"/*
rm -rf "$BASE_DIR/back/audio_recordings"/*
rm -rf "$BASE_DIR/back/data"/*
rm -rf "$BASE_DIR/back/logs"/*
echo "      Done."

# 3. Recreate empty directories so volume mounts don't fail
echo ""
echo "[3/4] Recreating empty directories..."
mkdir -p "$BASE_DIR/back/recordings"
mkdir -p "$BASE_DIR/back/webcam_recordings"
mkdir -p "$BASE_DIR/back/audio_recordings"
mkdir -p "$BASE_DIR/back/data"
mkdir -p "$BASE_DIR/back/logs"
echo "      Done."

# 4. Optionally rebuild and start
echo ""
if [ "$REBUILD" = true ]; then
    echo "[4/4] Building and starting all services..."
    cd "$BASE_DIR" && docker compose up --build -d
    echo ""
    echo "======================================"
    echo " All clean and running."
    echo " Logs: docker compose logs -f"
    echo "======================================"
else
    echo "[4/4] Skipped rebuild (pass --build to also rebuild and start)."
    echo ""
    echo "======================================"
    echo " All clean. Run to start:"
    echo "   docker compose up --build"
    echo "======================================"
fi
