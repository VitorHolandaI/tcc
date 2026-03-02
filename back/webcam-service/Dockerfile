# ════════════════════════════════════════════════════════
# Webcam Service - Container for Webcam Video Capture
# ════════════════════════════════════════════════════════

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install service requirements
COPY webcam-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code and shared app package
COPY webcam-service/ .
COPY app/ app/

# Create webcam directory
RUN mkdir -p /app/webcam_recordings

# Expose port
EXPOSE 8003

# Run service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003"]
