# ═══════════════════════════════════════════════════════════════
# Main API + Recording Service - Multi-stage Docker Build
# ═══════════════════════════════════════════════════════════════

FROM python:3.12-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# ═══════════════════════════════════════════════════════════════
# Main API Service
# ═══════════════════════════════════════════════════════════════

FROM base as main-api

COPY . .

# Create recordings directory
RUN mkdir -p /app/recordings /app/recordings/segments /app/logs

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]

# ═══════════════════════════════════════════════════════════════
# Recording Service
# ═══════════════════════════════════════════════════════════════

FROM base as recording-service

COPY . .

# Install recording-service specific dependencies (websockets etc.)
RUN pip install --no-cache-dir -r recording-service/requirements.txt

# Create recordings directory
RUN mkdir -p /app/recordings /app/recordings/segments /app/logs

EXPOSE 8001

CMD ["python", "recording-service/main.py"]
