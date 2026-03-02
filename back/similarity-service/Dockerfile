# ════════════════════════════════════════════════════════
# Similarity Service - Container for Code Similarity Analysis
# ════════════════════════════════════════════════════════

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install service requirements
COPY similarity-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code and shared app package
COPY similarity-service/ .
COPY app/ app/

# Expose port
EXPOSE 8006

# Run service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8006"]
