# ════════════════════════════════════════════════════════
# Keystroke Service - Container for Keystroke Analysis
# ════════════════════════════════════════════════════════

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install service requirements
COPY keystroke-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code and shared app package
COPY keystroke-service/ .
COPY app/ app/

# Create temp directory for keystroke data
RUN mkdir -p /tmp/keystroke_analysis

# Expose port
EXPOSE 8005

# Run service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8005"]
