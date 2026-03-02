# ════════════════════════════════════════════════════════
# Audio Service - Container for Audio Capture & Analysis
# ════════════════════════════════════════════════════════

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libsndfile1 \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install service requirements
COPY audio-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code and shared app package
COPY audio-service/ .
COPY app/ app/

# Create audio directory
RUN mkdir -p /app/audio_recordings

# Expose port
EXPOSE 8004

# Run service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8004"]
