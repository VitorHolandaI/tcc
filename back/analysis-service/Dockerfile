# ════════════════════════════════════════════════════════
# Analysis Service - Modular Container for Video Analysis
# ════════════════════════════════════════════════════════

FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for OpenCV and MediaPipe
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY . .

# Create webcam recordings directory
RUN mkdir -p /app/webcam_recordings

# Expose port
EXPOSE 8002

# Run service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
